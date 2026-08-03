# A3_v2 sampler audit

Status: **PASSED**.

The locked `a3_sample_schedule_200.jsonl` SHA-256 is `a9cde664e55dc8ac852b5a73343bb51d0db8380bfb5abff8ece9cf306d8857af`. All 3,200 consumed training-progress entries match its ordered `(microstep, sample_id, role)` triples.

| Checkpoint | Consumed | Acoustic | Replay |
| ---: | ---: | ---: | ---: |
| 50 | 800 | 719 | 81 |
| 100 | 1600 | 1425 | 175 |
| 150 | 2400 | 2154 | 246 |
| 200 | 3200 | 2880 | 320 |

Final ratios are exactly 0.90 acoustic and 0.10 clean replay.
