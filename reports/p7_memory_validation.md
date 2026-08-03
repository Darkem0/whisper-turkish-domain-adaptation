# P7 memory validation

The executor collected three real repeats for every named mode, but the result is **FAILED_TECHNICAL** for promotion: GPU utilization polling was not implemented, MEM3/MEM4 remained batch size one rather than the required bucketed/frame-budget batching, and profile runs were split across foreground invocations after the execution timeout. The raw timing/cache records are retained; they are not a valid fair MEM0-MEM4 promotion benchmark.
