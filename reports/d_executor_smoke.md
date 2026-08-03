# D executor smoke

The live D0 executor began after the bounded fake executor test passed. The initial real invocation exposed the known Whisper decoder limit (`448` requested plus four prompt tokens); the executor now caps `max_new_tokens` at `444`, matching the existing bounded inference implementation. D0 resumed from zero and produced `runs/D0/progress.json` with real file progress.
