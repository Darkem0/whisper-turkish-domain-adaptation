# A4_v2 single-experiment overnight supervisor plan

Design only; not started. `scripts/run_a4_v2_overnight_supervisor.py` must use one GPU worker, `Start-Process`, PID `state/a4_v2_supervisor.pid`, atomic `state/a4_v2_supervisor_state.json`, heartbeat, and distinct `logs/a4-v2-supervisor.stdout.log` / stderr.

Stages are: preflight, 2-step smoke, smoke audit, 200-step training, checkpoint validation, integrity audit, frozen evaluation, quality artifacts, paired CI, gate audit, terminal report. Resume is stage/target-hash based; completed targets are never rerun. Any hash mismatch, OOM, NaN/Inf stops the chain; at most one technical retry is permitted. Scientific gate failure closes the experiment and never starts A5/A6. Windows restart may resume only a verified A4 checkpoint. Current contract state blocks the first stage.
