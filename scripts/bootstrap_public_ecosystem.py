from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "ecosystem" / "components.lock.json"


def run_git(args: list[str], cwd: Path | None = None) -> str:
    command = ["git", *args]
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            f"Git command failed ({completed.returncode}): {' '.join(command)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed.stdout.strip()


def load_lock() -> dict[str, Any]:
    try:
        payload = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Missing component lock: {LOCK_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {LOCK_PATH}: {exc}") from exc

    components = payload.get("components")
    if not isinstance(components, list) or not components:
        raise RuntimeError("components.lock.json must contain a non-empty components list")
    return payload


def component_path(destination: Path, component_id: str) -> Path:
    return destination / component_id


def current_head(path: Path) -> str:
    return run_git(["rev-parse", "HEAD"], cwd=path)


def verify_component(component: dict[str, Any], destination: Path) -> tuple[bool, str]:
    component_id = str(component["id"])
    expected = str(component["commit"])
    path = component_path(destination, component_id)
    if not path.exists():
        return False, f"{component_id}: missing at {path}"
    if not (path / ".git").exists():
        return False, f"{component_id}: {path} is not a Git checkout"
    actual = current_head(path)
    if actual != expected:
        return False, f"{component_id}: HEAD {actual} != locked {expected}"
    return True, f"{component_id}: OK {actual}"


def materialize_component(component: dict[str, Any], destination: Path) -> None:
    component_id = str(component["id"])
    clone_url = str(component["clone_url"])
    commit = str(component["commit"])
    path = component_path(destination, component_id)

    if path.exists():
        if not (path / ".git").exists():
            raise RuntimeError(f"Refusing to overwrite non-Git path: {path}")
        run_git(["remote", "set-url", "origin", clone_url], cwd=path)
    else:
        destination.mkdir(parents=True, exist_ok=True)
        run_git(["clone", "--no-checkout", clone_url, str(path)])

    run_git(["fetch", "--depth", "1", "origin", commit], cwd=path)
    run_git(["checkout", "--detach", commit], cwd=path)

    actual = current_head(path)
    if actual != commit:
        raise RuntimeError(f"Checkout verification failed for {component_id}: {actual} != {commit}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Materialize commit-pinned public companion repositories."
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=ROOT / "components",
        help="Directory where component repositories are stored.",
    )
    parser.add_argument(
        "--include",
        nargs="*",
        default=None,
        help="Optional component IDs to materialize or verify.",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Do not clone or fetch; verify existing component HEADs only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lock = load_lock()
    components: list[dict[str, Any]] = lock["components"]

    available_ids = {str(component["id"]) for component in components}
    requested = set(args.include or available_ids)
    unknown = requested - available_ids
    if unknown:
        raise RuntimeError(f"Unknown component IDs: {', '.join(sorted(unknown))}")

    selected = [component for component in components if str(component["id"]) in requested]
    destination = args.destination.expanduser().resolve()

    failures: list[str] = []
    for component in selected:
        component_id = str(component["id"])
        try:
            if not args.verify_only:
                materialize_component(component, destination)
            ok, message = verify_component(component, destination)
            print(message)
            if not ok:
                failures.append(message)
        except Exception as exc:  # noqa: BLE001 - CLI must report per-component failures.
            message = f"{component_id}: ERROR: {exc}"
            print(message, file=sys.stderr)
            failures.append(message)

    if failures:
        print(f"Failed components: {len(failures)}", file=sys.stderr)
        return 1

    print(f"Verified components: {len(selected)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
