# ruff: noqa
from __future__ import annotations
import argparse, os, time, traceback
from .core import *
from .experiment_runner import run

def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--once", action="store_true"); args=p.parse_args()
    STATE.mkdir(exist_ok=True); queue_path=STATE/"experiment_queue.json"
    queue=read(queue_path, default_queue()); write(queue_path, queue); (STATE/"supervisor.pid").write_text(str(os.getpid()), encoding="utf-8")
    while True:
        item=next((x for x in queue if x.get("status") == "PENDING"), None)
        if not item: status(); break
        item.update({"status":"PREFLIGHT", "start_time":now(), "pid":os.getpid(), "git_commit":git_commit(), "config_hash":sha(ROOT/"evaluation"/"EVAL_LOCK_v2d.json")}); status(item); event("started", experiment=item["id"])
        registry=ROOT/"protocols"/"immutable_test_registry.json"
        try:
            if item["id"] != "P1_immutable_lock" and registry.exists():
                expected=read(registry,{})["entries"]
                if any(e["sha256"] != "MISSING" and sha(ROOT/e["path"]) != e["sha256"] for e in expected): verdict, err="BLOCKED", "immutable evaluation registry changed"
                else: item["status"]="RUNNING"; status(item); verdict,err=run(item)
            else: item["status"]="RUNNING"; status(item); verdict,err=run(item)
        except Exception:
            err=traceback.format_exc(); verdict="FAILED_TECHNICAL"; (RUNS/item["id"]).mkdir(parents=True, exist_ok=True); (RUNS/item["id"] / "execution.log").write_text(err, encoding="utf-8"); event("technical_failed",experiment=item["id"],traceback=err)
        item.update({"status":verdict,"end_time":now(),"verdict":verdict,"error":err,"result_path":str(RUNS/item["id"]),"log_path":str(STATE/"events.jsonl")})
        with (STATE/("completed_experiments.jsonl" if verdict=="PASSED" else "failed_experiments.jsonl")).open("a",encoding="utf-8") as f: f.write(json.dumps(item,ensure_ascii=False)+"\n")
        write(queue_path,queue); write(STATE/"current_experiment.json",item); status(item,err); event("finished",experiment=item["id"],verdict=verdict,error=err)
        if args.once: break
        time.sleep(1)
if __name__ == "__main__": main()
