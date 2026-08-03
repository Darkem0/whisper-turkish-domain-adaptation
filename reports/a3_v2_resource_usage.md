# A3_v2 resource usage

Status: **PASSED**.

Peak observed training resource use was 1,831.79 MiB CUDA allocated, 2,118.00 MiB CUDA reserved, 3,751 MiB driver VRAM, and 2,090.19 MiB process RSS. The CUDA-reserved acceptance gate was `<10,000 MiB`; it passed throughout.

Across 200 optimizer steps, median/mean step wall times were 3.6198/3.6384 seconds. Total wall time, including local validation, was 11,370.05 seconds. The initial/final training losses were 2.28027/2.79712; all recorded training losses were finite.
