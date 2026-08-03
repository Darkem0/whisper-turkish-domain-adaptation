# A6_v2 corrected statistical analysis

Delta is A6 minus A5; negative favours A6. Derived only from explicit, distinct locked prediction roots.

| checkpoint | dataset | metric | delta | 95% CI | classification |
| --- | --- | --- | ---: | --- | --- |
| step-050 | mediaspeech_clean | normalized_WER | -0.0011 | [-0.0030, 0.0003] | inconclusive |
| step-050 | mediaspeech_clean | normalized_CER | -0.0014 | [-0.0039, -0.0000] | statistically_supported_a6_gain |
| step-050 | mediaspeech_phone | normalized_WER | -0.0026 | [-0.0071, 0.0006] | inconclusive |
| step-050 | mediaspeech_phone | normalized_CER | -0.0021 | [-0.0064, 0.0014] | inconclusive |
| step-050 | mediaspeech_g711 | normalized_WER | -0.0039 | [-0.0082, -0.0004] | statistically_supported_a6_gain |
| step-050 | mediaspeech_g711 | normalized_CER | -0.0038 | [-0.0083, -0.0003] | statistically_supported_a6_gain |
| step-050 | cv_scripted | normalized_WER | -0.0004 | [-0.0190, 0.0149] | inconclusive |
| step-050 | cv_scripted | normalized_CER | -0.0009 | [-0.0143, 0.0073] | inconclusive |
| step-050 | fleurs | normalized_WER | 0.0002 | [-0.0002, 0.0006] | inconclusive |
| step-050 | fleurs | normalized_CER | -0.0001 | [-0.0003, 0.0000] | inconclusive |
| step-100 | mediaspeech_clean | normalized_WER | -0.0031 | [-0.0070, 0.0008] | inconclusive |
| step-100 | mediaspeech_clean | normalized_CER | -0.0032 | [-0.0084, 0.0012] | inconclusive |
| step-100 | mediaspeech_phone | normalized_WER | 0.0028 | [-0.0035, 0.0104] | inconclusive |
| step-100 | mediaspeech_phone | normalized_CER | 0.0042 | [-0.0032, 0.0159] | inconclusive |
| step-100 | mediaspeech_g711 | normalized_WER | -0.0041 | [-0.0100, 0.0006] | inconclusive |
| step-100 | mediaspeech_g711 | normalized_CER | -0.0044 | [-0.0095, 0.0010] | inconclusive |
| step-100 | cv_scripted | normalized_WER | 0.0038 | [-0.0150, 0.0296] | inconclusive |
| step-100 | cv_scripted | normalized_CER | -0.0000 | [-0.0148, 0.0170] | inconclusive |
| step-100 | fleurs | normalized_WER | -0.0003 | [-0.0010, 0.0003] | inconclusive |
| step-100 | fleurs | normalized_CER | -0.0001 | [-0.0003, 0.0001] | inconclusive |
| step-150 | mediaspeech_clean | normalized_WER | -0.0104 | [-0.0204, -0.0024] | statistically_supported_a6_gain |
| step-150 | mediaspeech_clean | normalized_CER | -0.0127 | [-0.0242, -0.0031] | statistically_supported_a6_gain |
| step-150 | mediaspeech_phone | normalized_WER | -0.0025 | [-0.0064, 0.0005] | inconclusive |
| step-150 | mediaspeech_phone | normalized_CER | -0.0028 | [-0.0060, -0.0000] | statistically_supported_a6_gain |
| step-150 | mediaspeech_g711 | normalized_WER | -0.0074 | [-0.0187, -0.0005] | statistically_supported_a6_gain |
| step-150 | mediaspeech_g711 | normalized_CER | -0.0084 | [-0.0225, 0.0003] | inconclusive |
| step-150 | cv_scripted | normalized_WER | -0.0026 | [-0.0234, 0.0223] | inconclusive |
| step-150 | cv_scripted | normalized_CER | 0.0008 | [-0.0123, 0.0226] | inconclusive |
| step-150 | fleurs | normalized_WER | -0.0010 | [-0.0023, -0.0002] | statistically_supported_a6_gain |
| step-150 | fleurs | normalized_CER | -0.0002 | [-0.0006, 0.0001] | inconclusive |
| step-200 | mediaspeech_clean | normalized_WER | -0.0115 | [-0.0228, -0.0020] | statistically_supported_a6_gain |
| step-200 | mediaspeech_clean | normalized_CER | -0.0132 | [-0.0272, -0.0032] | statistically_supported_a6_gain |
| step-200 | mediaspeech_phone | normalized_WER | -0.0043 | [-0.0084, -0.0010] | statistically_supported_a6_gain |
| step-200 | mediaspeech_phone | normalized_CER | -0.0046 | [-0.0091, -0.0014] | statistically_supported_a6_gain |
| step-200 | mediaspeech_g711 | normalized_WER | -0.0042 | [-0.0080, -0.0002] | statistically_supported_a6_gain |
| step-200 | mediaspeech_g711 | normalized_CER | -0.0038 | [-0.0097, 0.0006] | inconclusive |
| step-200 | cv_scripted | normalized_WER | -0.0021 | [-0.0228, 0.0212] | inconclusive |
| step-200 | cv_scripted | normalized_CER | -0.0041 | [-0.0217, 0.0163] | inconclusive |
| step-200 | fleurs | normalized_WER | -0.0064 | [-0.0209, -0.0004] | statistically_supported_a6_gain |
| step-200 | fleurs | normalized_CER | -0.0048 | [-0.0138, -0.0001] | statistically_supported_a6_gain |
| step-050 | robustness_proxy | normalized_WER | -0.0022 | [-0.0040, -0.0005] | statistically_supported_a6_gain |
| step-100 | robustness_proxy | normalized_WER | -0.0019 | [-0.0059, 0.0013] | inconclusive |
| step-150 | robustness_proxy | normalized_WER | -0.0076 | [-0.0148, -0.0018] | statistically_supported_a6_gain |
| step-200 | robustness_proxy | normalized_WER | -0.0079 | [-0.0133, -0.0028] | statistically_supported_a6_gain |
