# Local continuation summary

- Manifest: 32 real WAV rows; 32 gold references; SHA-256 `035050a04d2d471d39ec6c6de8eb1e08dd7cd8fd4fe74aa9d3f5699473b78412`.
- Smoke: PASSED on RTX 4070 SUPER, FP16, peak VRAM `1674808832` bytes.
- D0-D7: PENDING; P3-P7 execution: PENDING.
- A2/A3/A4/A5/A6 contracts: INVALID; A3-A6 are BLOCKED_TRAINING_CONTRACT.
- Supervisor/watchdog not started. `state/supervisor.pid=11452` and `state/watchdog.pid=14324` are stale; neither PID is live. The current supervisor implementation would convert pending D/P items into BLOCKED placeholders rather than execute their real inference/post-processing, so starting it would misrepresent execution state.
- Intended watcher command after a real D0-D7 executor is wired: `powershell -ExecutionPolicy Bypass -File scripts/night_watchdog_v2d.ps1`.
