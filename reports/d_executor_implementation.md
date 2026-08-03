# D executor implementation

`src/whisper_arge/d_executor.py` runs each D profile against the immutable 32-row WAV manifest with offline `openai/whisper-large-v3-turbo` Transformers inference. It writes resumable predictions, per-file progress/resource records, metrics, environment, and execution log before a terminal verdict is allowed.
