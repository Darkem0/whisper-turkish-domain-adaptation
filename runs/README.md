# Run artifact sözleşmesi

Her gerçek koşu `runs/<run_id>/` altında en az şunları içermelidir:

- `config.json`: immutable resolved config
- `provenance.json`: dataset/model/evaluation/commit hashleri ve seed
- `environment.json`: OS, Python, CUDA, GPU ve paket sürümleri
- `timing.json`: başlangıç/bitiş, wall time, peak VRAM
- `checkpoints/`: adapter checkpoint ve trainer state
- `predictions/<tier>.jsonl`: her sabit eval örneğinin tahmini
- `metrics/<tier>.json`: domain metrikleri ve baseline delta
- `decision.json`: accept/reject gerekçesi ve promotion kararı

`runs/*` büyük ve makineye özgü olduğu için Git dışında tutulur; uzun ömürlü
artifact deposuna kopyalanmalı ve bundle SHA-256 değeri ledger'a yazılmalıdır.

