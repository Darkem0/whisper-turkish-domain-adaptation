# D7 foreground traceback

`python -X faulthandler -m automation.supervisor` reached D7 and failed before writing a prediction. The captured traceback is recorded in `logs/supervisor-foreground.stderr.log` and ends with `UnboundLocalError: cannot access local variable 'logprobs' where it is not associated with a value` in Transformers `generation_whisper.py:_need_fallback`.
