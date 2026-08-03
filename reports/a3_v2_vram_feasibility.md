# A3_v2 VRAM feasibility

Status: **resource-smoke gate passed; not a 200-step feasibility measurement**.

On the RTX 4070 SUPER (12,281.5 MiB reported by Torch), the two-step A3_v2 smoke measured 1825.98 MiB peak CUDA allocated, 2030.00 MiB peak CUDA reserved, and 3578 MiB peak driver VRAM. Reserved memory is below the 10,000 MiB acceptance threshold; no CUDA OOM occurred.

This permits a separately authorized 200-step training request. It does not establish the peak memory or runtime of that full training run.
