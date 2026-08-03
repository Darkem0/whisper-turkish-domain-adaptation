# A3_v2 checkpoint validation

Status: **PASSED**. Every checkpoint was written with a verifiable adapter, config, optimizer state, scheduler state, and resume state. Each validation used the same 9,081-row A3 validation manifest and normalized metric code.

| Step | Adapter SHA-256 | Validation loss | Norm. WER | Norm. CER | Samples |
| ---: | --- | ---: | ---: | ---: | ---: |
| 50 | `d71c8a460bba4e13adefc4f9a68641f10e319546cebd94c7a2a0bb1e3d13bb21` | 2.54410 | 0.26953 | 0.14890 | 9081 |
| 100 | `7fd34ffb6dbd4f7679bfc92d198f5cf41c35c9a53f5b18d4253e7e321afb9a91` | 2.48788 | 0.27133 | 0.14737 | 9081 |
| 150 | `d929474c6104fea929fe6bc3dd1de82247d9e9f029ce89c6f766b7ebdbc7116c` | 2.44057 | 0.27222 | 0.14671 | 9081 |
| 200 | `7f00968483b0ddc9fd32cefe463c1b6545e5101f0412304f8c1017de68688d1a` | 2.42250 | 0.26493 | 0.14481 | 9081 |

No automatic best-checkpoint selection, promotion, or frozen external benchmark evaluation was performed.
