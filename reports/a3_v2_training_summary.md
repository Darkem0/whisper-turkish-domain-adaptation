# A3_v2 fresh-base 200-step training summary

Status: **PASSED**. The authorized run completed 200 optimizer steps with exit code 0. It used fresh pinned-base initialization; A2 weights were not loaded and `legacy_resume_attempted=false`.

The locked sampler consumed 3,200 microbatches exactly: 2,880 acoustic (90%) and 320 clean replay (10%). The final adapter is `runs/A3_v2_fresh_base_200/checkpoints/step-200/adapter/adapter_model.safetensors`, SHA-256 `7f00968483b0ddc9fd32cefe463c1b6545e5101f0412304f8c1017de68688d1a`.

Total wall time was 11,370.05 seconds (189.50 minutes). This includes four complete 9,081-row local validation passes. No frozen external benchmark or promotion decision was executed.

| Step | Validation loss | Normalized WER | Normalized CER | Evaluation wall time |
| ---: | ---: | ---: | ---: | ---: |
| 50 | 2.54410 | 0.26953 | 0.14890 | 2659.64 s |
| 100 | 2.48788 | 0.27133 | 0.14737 | 2635.47 s |
| 150 | 2.44057 | 0.27222 | 0.14671 | 2679.18 s |
| 200 | 2.42250 | 0.26493 | 0.14481 | 2661.93 s |

Step-200 is recorded as the final artifact only; it is not promoted or selected as a production checkpoint by this task.
