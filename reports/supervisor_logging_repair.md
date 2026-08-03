# Supervisor logging repair

`Start-WhisperResearch.ps1` now redirects supervisor and watchdog stdout/stderr to separate files under `logs/`. The supervisor catches executor exceptions, writes `runs/<id>/execution.log`, emits `technical_failed`, and records `FAILED_TECHNICAL` rather than silently exiting.
