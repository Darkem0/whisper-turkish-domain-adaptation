# Supervisor launch

Stale PID files were checked and cleaned only when their referenced process was absent. Supervisor and watchdog were launched through `scripts/Start-WhisperResearch.ps1`; the live D0 executor writes `runs/D0/progress.json` while it processes the immutable manifest.
