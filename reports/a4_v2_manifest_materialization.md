# A4_v2 manifest materialization

Not materialized: the valid A2 train source and schedule are hash-locked in `contracts/A4_v2_data_manifest.lock.json`, but no non-leaking validation split has been authorized. Writing a train/replay/schedule bundle before that split would falsely imply an executable contract.

The verified A2 replay policy is 0%; A3's 10% replay is explicitly not copied.
