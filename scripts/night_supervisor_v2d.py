from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import shutil
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

from whisper_arge.pipeline_policy import is_global_fatal


ROOT = Path(__file__).resolve().parents[1]
RUN_ROOT = ROOT / "runs" / "night_supervisor_v2d"
PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"
LOCKED_FILES = (
    ROOT / "data/materialized/training_v2d/TRAINING_LOCK_v2d.json",
    ROOT / "evaluation/EVAL_LOCK_v2d.json",
    ROOT / "evaluation/ACCEPTANCE_LOCK_v2d.json",
    ROOT / "evaluation/acceptance_v2d.json",
)
MANIFESTS = {
    "mediaspeech_paired": ROOT
    / "data/materialized/mediaspeech_v2d/paired/mediaspeech_holdout_paired_v2d.jsonl",
    "cv_scripted": ROOT / "data/materialized/hf_v2d/cv_scripted_test_v2d.jsonl",
    "fleurs": ROOT / "data/materialized/fleurs_tr_v2d/fleurs_tr_test_v2d.jsonl",
    "cv_spontaneous": ROOT
    / "data/materialized/cv_spontaneous_v2c/cv_spontaneous_holdout_v2c.jsonl",
    "tsc_exploratory": ROOT / "data/materialized/tsc_v2a/tsc_full_v2a.jsonl",
}
STATES = [
    "A1_EVAL_WAIT",
    "A1_EVAL_FINALIZE",
    "A1_ARTIFACT_LOCK",
    "A2_TRAIN_200",
    "A2_EVAL",
    "A2_FINALIZE",
    "A3_TRAIN_200",
    "A3_EVAL",
    "A3_FINALIZE",
    "A6_TRAIN_200",
    "A6_EVAL",
    "A6_FINALIZE",
    "COMPARISON_REPORT",
    "DONE",
]
LEGACY_STATES = {
    "A1_EVAL_FINALIZE": "A1_FINALIZE",
    "A1_ARTIFACT_LOCK": "A1_LOCK",
    "A2_TRAIN_200": "A2_TRAIN",
    "A3_TRAIN_200": "A3_TRAIN",
    "A6_TRAIN_200": "A6_TRAIN",
}


def now() -> str:
    return datetime.now(UTC).isoformat()


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def json_load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            f"Get-Process -Id {pid} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return str(pid) in result.stdout.split()


def process_rows() -> list[dict]:
    command = "Get-CimInstance Win32_Process | Select-Object ProcessId,Name,CommandLine | ConvertTo-Json -Compress"
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode or not result.stdout.strip():
        return []
    value = json.loads(result.stdout)
    return value if isinstance(value, list) else [value]


def active_gpu_workers() -> list[dict]:
    markers = ("run-lora-v2d", "cache-adapter-predictions-batch", "run_adapter_v2d_batches")
    return [
        row
        for row in process_rows()
        if any(marker in (row.get("CommandLine") or "") for marker in markers)
    ]


def expected_ids(manifest: Path) -> set[str]:
    return {str(row["sample_id"]) for row in read_jsonl(manifest)}


def validate_eval(root: Path) -> dict:
    domains: dict[str, dict] = {}
    all_pass = True
    for name, manifest in MANIFESTS.items():
        expected = expected_ids(manifest)
        domain = root / name
        progress_path = domain / "progress.json"
        prediction_path = domain / "predictions.jsonl"
        errors: list[str] = []
        if not progress_path.exists() or not prediction_path.exists():
            errors.append("missing_progress_or_final_predictions")
            actual_ids: list[str] = []
            progress = {}
        else:
            progress = json_load(progress_path)
            actual_ids = [str(row["sample_id"]) for row in read_jsonl(prediction_path)]
            if not progress.get("completed"):
                errors.append("progress_not_completed")
            if int(progress.get("next", -1)) != len(expected) or int(
                progress.get("total", -2)
            ) != len(expected):
                errors.append("progress_count_mismatch")
            for part_name in progress.get("parts", []):
                if (
                    not Path(part_name).exists()
                    or not Path(part_name).read_text(encoding="utf-8").strip()
                ):
                    errors.append("incomplete_or_missing_part")
                    break
        actual_set = set(actual_ids)
        missing = sorted(expected - actual_set)
        unexpected = sorted(actual_set - expected)
        duplicates = len(actual_ids) - len(actual_set)
        if missing:
            errors.append("missing_stable_id")
        if unexpected:
            errors.append("unexpected_stable_id")
        if duplicates:
            errors.append("duplicate_stable_id")
        domains[name] = {
            "expected": len(expected),
            "actual": len(actual_ids),
            "missing_stable_id": len(missing),
            "duplicate_stable_id": duplicates,
            "unexpected_stable_id": len(unexpected),
            "incomplete_batch": 1
            if any("part" in error or "progress" in error for error in errors)
            else 0,
            "status": "pass" if not errors else "fail",
            "errors": errors,
        }
        all_pass &= not errors
    return {"status": "pass" if all_pass else "incomplete_or_fail", "domains": domains}


class Supervisor:
    def __init__(self, dry_run: bool) -> None:
        self.dry_run = dry_run
        RUN_ROOT.mkdir(parents=True, exist_ok=True)
        self.log_path = RUN_ROOT / "supervisor.log"
        self.error_path = RUN_ROOT / "supervisor_error.log"
        self.state_path = RUN_ROOT / "state.json"
        self.heartbeat_path = RUN_ROOT / "heartbeat.json"
        self.pid_path = RUN_ROOT / "supervisor.pid"
        self.lock_path = RUN_ROOT / "supervisor.lock"
        self.state = (
            json_load(self.state_path)
            if self.state_path.exists()
            else {"state": "A1_EVAL_WAIT", "eval_restarts": {}, "training_retries": {}}
        )
        self.continue_on_error = False
        self.lock_hashes = {str(path.relative_to(ROOT)): sha(path) for path in LOCKED_FILES}

    def log(self, message: str, *, error: bool = False) -> None:
        target = self.error_path if error else self.log_path
        with target.open("a", encoding="utf-8") as handle:
            handle.write(f"{now()} {message}\n")

    def set_state(self, value: str, **extra: object) -> None:
        if value not in STATES and value not in {"FAILED", "FAILED_SKIPPED", "GLOBAL_FATAL"}:
            raise ValueError(value)
        self.state.update({"state": value, "updated_at": now(), **extra})
        write_json(self.state_path, self.state)
        self.log(f"state={value}")

    def heartbeat(self) -> None:
        write_json(
            self.heartbeat_path,
            {
                "timestamp": now(),
                "state": self.state["state"],
                "gpu_workers": active_gpu_workers(),
                "a1_eval": validate_eval(ROOT / "runs/A1_v2d_eval"),
            },
        )

    def assert_locks_unchanged(self) -> None:
        current = {str(path.relative_to(ROOT)): sha(path) for path in LOCKED_FILES}
        if current != self.lock_hashes:
            raise RuntimeError("locked v2d artifact changed while supervisor was active")

    def acquire(self) -> None:
        if self.lock_path.exists():
            lock = json_load(self.lock_path)
            if pid_alive(int(lock.get("pid", 0))):
                raise RuntimeError(f"supervisor already active with PID {lock['pid']}")
            self.log("removing stale supervisor lock")
            self.lock_path.unlink()
            self.pid_path.unlink(missing_ok=True)
        descriptor = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(descriptor)
        write_json(self.lock_path, {"pid": os.getpid(), "started_at": now()})
        self.pid_path.write_text(f"{os.getpid()}\n", encoding="utf-8")

    def recover_a1_metric_failure(self) -> None:
        if self.state.get("state") != "FAILED":
            raise RuntimeError("recovery requires FAILED supervisor state")
        if self.lock_path.exists():
            lock = json_load(self.lock_path)
            if pid_alive(int(lock.get("pid", 0))):
                raise RuntimeError("live supervisor lock prevents recovery")
            self.lock_path.unlink()
        if self.pid_path.exists():
            old_pid = int(self.pid_path.read_text(encoding="utf-8").strip())
            if pid_alive(old_pid):
                raise RuntimeError("live supervisor PID prevents recovery")
            self.pid_path.unlink()
        archive = RUN_ROOT / "failure_archive" / datetime.now().strftime("%Y%m%dT%H%M%SZ")
        archive.mkdir(parents=True, exist_ok=False)
        for path in (self.state_path, self.log_path, self.error_path):
            if path.exists():
                shutil.copy2(path, archive / path.name)
        self.state = {
            "state": "A1_EVAL_FINALIZE",
            "updated_at": now(),
            "recovered_from": str(archive),
            "recovery_reason": "immutable A0 CV Spontaneous prediction path resolution",
            "eval_restarts": self.state.get("eval_restarts", {}),
            "training_retries": self.state.get("training_retries", {}),
        }
        write_json(self.state_path, self.state)
        self.log(f"recovered FAILED state to A1_EVAL_FINALIZE; archived metadata at {archive}")

    def release(self) -> None:
        self.lock_path.unlink(missing_ok=True)
        self.pid_path.unlink(missing_ok=True)

    def sleep_block(self, enabled: bool) -> None:
        try:
            flags = 0x80000000 | (0x00000001 if enabled else 0)
            ctypes.windll.kernel32.SetThreadExecutionState(flags)
        except AttributeError:
            self.log("SetThreadExecutionState unavailable", error=True)

    def start_eval(self, condition: str) -> subprocess.Popen:
        output_root = ROOT / "runs" / f"{condition}_v2d_eval"
        adapter = ROOT / "runs" / f"{condition}_v2d_200" / "adapter"
        command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts/run_adapter_v2d_batches.ps1"),
            "-Adapter",
            str(adapter),
            "-OutputRoot",
            str(output_root),
        ]
        self.log("starting eval: " + " ".join(command))
        return subprocess.Popen(
            command, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    def start_train(self, condition: str) -> subprocess.Popen:
        output = ROOT / "runs" / f"{condition}_v2d_200"
        command = [
            str(PYTHON),
            "-m",
            "whisper_arge.cli",
            "run-lora-v2d",
            "--condition",
            condition,
            "--output-root",
            str(output),
            "--steps",
            "200",
            "--seed",
            "20260730",
            "--gpu-telemetry",
        ]
        self.log("starting train: " + " ".join(command))
        (output / "worker").mkdir(parents=True, exist_ok=True)
        stdout = (output / "worker" / "worker.stdout.log").open("a", encoding="utf-8")
        stderr = (output / "worker" / "worker.stderr.log").open("a", encoding="utf-8")
        return subprocess.Popen(command, cwd=ROOT, stdout=stdout, stderr=stderr)

    def wait_child(self, child: subprocess.Popen) -> int:
        while child.poll() is None:
            self.assert_locks_unchanged()
            self.heartbeat()
            time.sleep(60)
        return int(child.returncode)

    def ensure_eval(self, condition: str, external_wait: bool = False) -> bool:
        root = ROOT / "runs" / f"{condition}_v2d_eval"
        report = validate_eval(root)
        workers = active_gpu_workers()
        if report["status"] == "pass" and not (external_wait and workers):
            return True
        if workers:
            if external_wait:
                self.log("existing A1 evaluation worker detected; monitoring only")
                return False
            raise RuntimeError("another GPU job is active; refusing duplicate evaluation")
        key = f"{condition}_eval"
        attempts = int(self.state["eval_restarts"].get(key, 0))
        while attempts < 3:
            child = self.start_eval(condition)
            code = self.wait_child(child)
            report = validate_eval(root)
            if code == 0 and report["status"] == "pass":
                return True
            attempts += 1
            self.state["eval_restarts"][key] = attempts
            write_json(self.state_path, self.state)
            self.log(
                f"evaluation retry {attempts} for {condition}; exit={code}; status={report['status']}",
                error=True,
            )
        raise RuntimeError(f"{condition} evaluation failed after three resumable attempts")

    def finalize_metrics(self, condition: str) -> None:
        root = ROOT / "runs" / f"{condition}_v2d_eval"
        report = root / f"{condition.lower()}_evaluation_v2d.json"
        if report.exists():
            return
        command = [
            str(PYTHON),
            "-m",
            "whisper_arge.cli",
            "evaluate-candidate-v2d",
            "--candidate-root",
            str(root),
        ]
        self.log("finalizing candidate metrics: " + " ".join(command))
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        if result.returncode:
            self.log(result.stderr, error=True)
            raise RuntimeError(f"{condition} candidate metric finalization failed")
        if not report.exists():
            raise RuntimeError(f"{condition} candidate metric report missing after finalization")

    def ensure_training(self, condition: str) -> bool:
        root = ROOT / "runs" / f"{condition}_v2d_200"
        result = root / "training_result.json"
        if result.exists():
            value = json_load(result)
            if value.get("steps") == 200:
                return True
            raise RuntimeError(f"existing {condition} result does not contain 200 steps")
        if active_gpu_workers():
            raise RuntimeError("GPU job already active; refusing training launch")
        attempts = int(self.state["training_retries"].get(condition, 0))
        while attempts < 2:
            child = self.start_train(condition)
            code = self.wait_child(child)
            if code == 0 and result.exists():
                audit = subprocess.run(
                    [
                        str(PYTHON),
                        "-m",
                        "whisper_arge.cli",
                        "audit-lora-run-v2d",
                        "--run-root",
                        str(root),
                    ],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                )
                if audit.returncode == 0:
                    return True
            attempts += 1
            self.state["training_retries"][condition] = attempts
            write_json(self.state_path, self.state)
            if attempts >= 2:
                break
            if root.exists():
                quarantine = (
                    ROOT
                    / "runs"
                    / f"{condition}_v2d_200_quarantine_{datetime.now().strftime('%Y%m%dT%H%M%S')}"
                )
                shutil.move(str(root), str(quarantine))
                self.log(f"quarantined failed training run to {quarantine}", error=True)
        raise RuntimeError(f"{condition} training failed twice")

    def artifact_lock(self, condition: str) -> None:
        run = ROOT / "runs" / f"{condition}_v2d_200"
        eval_root = ROOT / "runs" / f"{condition}_v2d_eval"
        metric_path = eval_root / f"{condition.lower()}_evaluation_v2d.json"
        metric = json_load(metric_path)
        acceptance = json_load(ROOT / "evaluation/acceptance_v2d.json")["promotion_200_step"]
        proxy = metric["robustness_proxy"]
        deltas = metric["mediaspeech_variant_paired_normalized_wer_delta_vs_a0"]
        guards = metric["paired_normalized_wer_delta_vs_a0"]
        gates = {
            "proxy_score": proxy["candidate_proxy_score"] <= acceptance["proxy_score_max"],
            "proxy_delta_point": proxy["point"] <= acceptance["proxy_paired_delta_point_max"],
            "proxy_delta_ci_upper": proxy["upper"]
            <= acceptance["proxy_paired_delta_ci95_upper_max"],
            "media_clean_delta": deltas["clean"]["point"]
            <= acceptance["mediaspeech_variant_delta_max"],
            "media_phone_delta": deltas["phone_8khz"]["point"]
            <= acceptance["mediaspeech_variant_delta_max"],
            "media_g711_delta": deltas["g711_mulaw"]["point"]
            <= acceptance["mediaspeech_variant_delta_max"],
            "cv_scripted_delta": guards["cv_scripted"]["point"]
            <= acceptance["cv_scripted_delta_max"],
            "fleurs_delta": guards["fleurs"]["point"] <= acceptance["fleurs_delta_max"],
            "paired_ci_hard_gate": max(
                deltas["clean"]["upper"],
                deltas["phone_8khz"]["upper"],
                deltas["g711_mulaw"]["upper"],
                guards["cv_scripted"]["upper"],
                guards["fleurs"]["upper"],
            )
            <= acceptance["hard_gate_paired_ci95_upper_max"],
        }
        content = {
            "schema_version": 1,
            "status": "immutable",
            "condition": condition,
            "promotion_200_step": {"pass": all(gates.values()), "checks": gates},
            "sha256": {
                "adapter": sha(run / "adapter/adapter_model.safetensors"),
                "training_metrics": sha(run / "training_result.json"),
                "metric_report": sha(metric_path),
                "training_lock": sha(
                    ROOT / "data/materialized/training_v2d/TRAINING_LOCK_v2d.json"
                ),
                "eval_lock": sha(ROOT / "evaluation/EVAL_LOCK_v2d.json"),
                "acceptance_lock": sha(ROOT / "evaluation/ACCEPTANCE_LOCK_v2d.json"),
                "predictions": {
                    name: sha(eval_root / name / "predictions.jsonl") for name in MANIFESTS
                },
            },
        }
        output = eval_root / f"{condition.lower()}_artifact_lock_v2d.json"
        if output.exists() and json_load(output) != content:
            raise RuntimeError(f"immutable artifact lock mismatch: {output}")
        if not output.exists():
            write_json(output, content)

    def run(self) -> None:
        self.acquire()
        self.sleep_block(True)
        try:
            self.heartbeat()
            if self.dry_run:
                self.set_state("A1_EVAL_WAIT", dry_run=True, duplicate_gpu_launch_prevented=True)
                self.log("dry run passed: state=A1_EVAL_WAIT; no GPU worker will be launched")
                return
            while self.state["state"] != "DONE":
                self.assert_locks_unchanged()
                state = self.state["state"]
                if state == "A1_EVAL_WAIT":
                    if self.ensure_eval("A1", external_wait=True):
                        self.set_state("A1_EVAL_FINALIZE")
                    else:
                        self.heartbeat()
                        time.sleep(60)
                elif state == "A1_EVAL_FINALIZE":
                    if self.ensure_eval("A1"):
                        self.finalize_metrics("A1")
                        self.set_state("A1_ARTIFACT_LOCK")
                elif state == "A1_ARTIFACT_LOCK":
                    self.artifact_lock("A1")
                    self.set_state("A2_TRAIN_200")
                elif state.endswith("TRAIN_200"):
                    condition = state.split("_")[0]
                    self.ensure_training(condition)
                    self.set_state(f"{condition}_EVAL")
                elif state.endswith("_EVAL"):
                    condition = state.split("_")[0]
                    if self.ensure_eval(condition):
                        self.set_state(f"{condition}_FINALIZE")
                elif state.endswith("_FINALIZE"):
                    condition = state.split("_")[0]
                    self.finalize_metrics(condition)
                    self.artifact_lock(condition)
                    next_state = {
                        "A2": "A3_TRAIN_200",
                        "A3": "A6_TRAIN_200",
                        "A6": "COMPARISON_REPORT",
                    }[condition]
                    self.set_state(next_state)
                elif state == "COMPARISON_REPORT":
                    summaries = {
                        name: json_load(
                            ROOT
                            / "runs"
                            / f"{name}_v2d_eval"
                            / f"{name.lower()}_evaluation_v2d.json"
                        )
                        for name in ("A1", "A2", "A3", "A6")
                    }
                    write_json(
                        RUN_ROOT / "final_summary.json",
                        {"status": "complete", "completed_at": now(), "conditions": summaries},
                    )
                    self.set_state("DONE")
                self.heartbeat()
        except Exception as exc:
            message = str(exc)
            if is_global_fatal(message):
                self.set_state("GLOBAL_FATAL", error=message)
                self.log(f"GLOBAL_FATAL: {message}", error=True)
            elif self.continue_on_error:
                next_state = {
                    "A1_EVAL_FINALIZE": "A1_ARTIFACT_LOCK",
                    "A1_ARTIFACT_LOCK": "A2_TRAIN_200",
                    "A2_TRAIN_200": "A2_EVAL",
                    "A2_EVAL": "A2_FINALIZE",
                    "A2_FINALIZE": "A3_TRAIN_200",
                    "A3_TRAIN_200": "A3_EVAL",
                    "A3_EVAL": "A3_FINALIZE",
                    "A3_FINALIZE": "A6_TRAIN_200",
                    "A6_TRAIN_200": "A6_EVAL",
                    "A6_EVAL": "A6_FINALIZE",
                    "A6_FINALIZE": "COMPARISON_REPORT",
                }.get(self.state.get("state"), "COMPARISON_REPORT")
                self.set_state(next_state, last_task_status="FAILED_SKIPPED", error=message)
                self.log(f"FAILED_SKIPPED: {message}; next={next_state}", error=True)
            else:
                self.set_state("FAILED", error=message)
                self.log(f"FAILED: {message}", error=True)
        finally:
            self.sleep_block(False)
            self.release()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--recover-a1-metric-failure", action="store_true")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args()
    supervisor = Supervisor(dry_run=args.dry_run)
    supervisor.continue_on_error = args.continue_on_error
    if args.resume and supervisor.state.get("state") == "FAILED":
        supervisor.set_state("A2_TRAIN_200", resumed_from_failed=True)
    if args.recover_a1_metric_failure:
        supervisor.recover_a1_metric_failure()
    supervisor.run()


if __name__ == "__main__":
    main()
