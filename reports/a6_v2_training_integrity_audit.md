# A6_v2 training integrity audit

{
  "status": "PASSED",
  "problems": [],
  "checkpoints": [
    {
      "checkpoint": "step-050",
      "adapter_sha256": "cad29e58816822cbc172f423f44d04d9e7ae1f2f6abd81ec82eacd71fcb5f303",
      "optimizer_step": 50,
      "consumed_microbatches": 800,
      "config_sha256": "93e147c0cac6e4abee7e6f8147e8c2b12b68b11ca460775706cfdcaa7e58937b",
      "input_manifest_hashes": {
        "data/materialized/training_a4_v2/a4_validation_manifest.jsonl": "864e801656175b9dc515f52d2852f1a740d2d88224ee4801fcd45806f4c09976",
        "data/materialized/training_a5_v2/a5_replay_manifest.jsonl": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "data/materialized/training_a5_v2/a5_sample_schedule.jsonl": "dd277700c6d1052d12937ee523b874d6a7054c010602df913e8ffb6363acc570",
        "data/materialized/training_a5_v2/a5_train_manifest.jsonl": "452e602bcf025c416e52e023ecd1fc1d6e5dcdd9f6512fd863c9063c390fa16e"
      },
      "optimizer_state": "PRESENT",
      "scheduler_state": "PRESENT",
      "resume_state": "PRESENT"
    },
    {
      "checkpoint": "step-100",
      "adapter_sha256": "7151134e9645e42d4b9c7be715c63096a5e7820580d838446d88e7ae7020b22f",
      "optimizer_step": 100,
      "consumed_microbatches": 1600,
      "config_sha256": "93e147c0cac6e4abee7e6f8147e8c2b12b68b11ca460775706cfdcaa7e58937b",
      "input_manifest_hashes": {
        "data/materialized/training_a4_v2/a4_validation_manifest.jsonl": "864e801656175b9dc515f52d2852f1a740d2d88224ee4801fcd45806f4c09976",
        "data/materialized/training_a5_v2/a5_replay_manifest.jsonl": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "data/materialized/training_a5_v2/a5_sample_schedule.jsonl": "dd277700c6d1052d12937ee523b874d6a7054c010602df913e8ffb6363acc570",
        "data/materialized/training_a5_v2/a5_train_manifest.jsonl": "452e602bcf025c416e52e023ecd1fc1d6e5dcdd9f6512fd863c9063c390fa16e"
      },
      "optimizer_state": "PRESENT",
      "scheduler_state": "PRESENT",
      "resume_state": "PRESENT"
    },
    {
      "checkpoint": "step-150",
      "adapter_sha256": "db1c74645eb7ff29d3c0e150e598a0f6308bc52574c273778fed5ff7b2b9f404",
      "optimizer_step": 150,
      "consumed_microbatches": 2400,
      "config_sha256": "93e147c0cac6e4abee7e6f8147e8c2b12b68b11ca460775706cfdcaa7e58937b",
      "input_manifest_hashes": {
        "data/materialized/training_a4_v2/a4_validation_manifest.jsonl": "864e801656175b9dc515f52d2852f1a740d2d88224ee4801fcd45806f4c09976",
        "data/materialized/training_a5_v2/a5_replay_manifest.jsonl": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "data/materialized/training_a5_v2/a5_sample_schedule.jsonl": "dd277700c6d1052d12937ee523b874d6a7054c010602df913e8ffb6363acc570",
        "data/materialized/training_a5_v2/a5_train_manifest.jsonl": "452e602bcf025c416e52e023ecd1fc1d6e5dcdd9f6512fd863c9063c390fa16e"
      },
      "optimizer_state": "PRESENT",
      "scheduler_state": "PRESENT",
      "resume_state": "PRESENT"
    },
    {
      "checkpoint": "step-200",
      "adapter_sha256": "e59a822518e5f9a9a4116dec2f748fba17cc8839ee5173e7d2dfa9ecfd640716",
      "optimizer_step": 200,
      "consumed_microbatches": 3200,
      "config_sha256": "93e147c0cac6e4abee7e6f8147e8c2b12b68b11ca460775706cfdcaa7e58937b",
      "input_manifest_hashes": {
        "data/materialized/training_a4_v2/a4_validation_manifest.jsonl": "864e801656175b9dc515f52d2852f1a740d2d88224ee4801fcd45806f4c09976",
        "data/materialized/training_a5_v2/a5_replay_manifest.jsonl": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "data/materialized/training_a5_v2/a5_sample_schedule.jsonl": "dd277700c6d1052d12937ee523b874d6a7054c010602df913e8ffb6363acc570",
        "data/materialized/training_a5_v2/a5_train_manifest.jsonl": "452e602bcf025c416e52e023ecd1fc1d6e5dcdd9f6512fd863c9063c390fa16e"
      },
      "optimizer_state": "PRESENT",
      "scheduler_state": "PRESENT",
      "resume_state": "PRESENT"
    }
  ],
  "global": {
    "optimizer_steps": 200,
    "consumed_microbatches": 3200,
    "acoustic": 3200,
    "replay": 0,
    "trainable_parameters": 3276800,
    "base_weights_frozen": true,
    "contracts": {
      "contracts/A6_v2_data_manifest.lock.json": "b8c100ebee9e669e727a1e84adccba2c63df03d710a6a3b0ac542bbdc94cb995",
      "contracts/A6_v2_eval_contract.yaml": "e10446312e33743db7d09d14caa60a12e6e93529a6096d98230fd753997dbeb1",
      "contracts/A6_v2_training_contract.yaml": "6bc2854946b34c1ee2e7f3b50751ec6a896ca62e922b8f4cf50511c20619611f"
    }
  },
  "validations": [
    {
      "evaluation_wall_seconds": 3031.1278709,
      "normalized_cer": 0.14739740363292053,
      "normalized_wer": 0.2697564242484373,
      "optimizer_step": 50,
      "predictions": "runs/A6_v2_fresh_base_200/validations/step-050/predictions.jsonl",
      "predictions_sha256": "739eafffcb037acbc33ed44b9087a88115511a682acf1fd16ae316989658ccd4",
      "raw_cer": 0.21053123112715139,
      "raw_wer": 0.5046693041310629,
      "reference_chars": 481843,
      "reference_words": 80633,
      "sample_count": 9081,
      "samples": 9081,
      "validation_loss": 2.3037861610952812
    },
    {
      "evaluation_wall_seconds": 3215.6199949999996,
      "normalized_cer": 0.1374160084386083,
      "normalized_wer": 0.2566226808215101,
      "optimizer_step": 100,
      "predictions": "runs/A6_v2_fresh_base_200/validations/step-100/predictions.jsonl",
      "predictions_sha256": "135d342cb011bf247d9c6d8fd2a2a53a249d717965abae480e73e637b5c2cfc4",
      "raw_cer": 0.19943633092106766,
      "raw_wer": 0.48943980752297445,
      "reference_chars": 481843,
      "reference_words": 80633,
      "sample_count": 9081,
      "samples": 9081,
      "validation_loss": 1.8347078980150864
    },
    {
      "evaluation_wall_seconds": 2975.493195100001,
      "normalized_cer": 0.1291829666359355,
      "normalized_wer": 0.24687468994939973,
      "optimizer_step": 150,
      "predictions": "runs/A6_v2_fresh_base_200/validations/step-150/predictions.jsonl",
      "predictions_sha256": "f21f52e517b369502fb187a4df2c16ae5e83b65aedb980cd8d8b72f12495a545",
      "raw_cer": 0.1908318684716806,
      "raw_wer": 0.47471878759316904,
      "reference_chars": 481843,
      "reference_words": 80633,
      "sample_count": 9081,
      "samples": 9081,
      "validation_loss": 1.688679703845942
    },
    {
      "evaluation_wall_seconds": 3136.367975700001,
      "normalized_cer": 0.12248440601666127,
      "normalized_wer": 0.236643020140887,
      "optimizer_step": 200,
      "predictions": "runs/A6_v2_fresh_base_200/validations/step-200/predictions.jsonl",
      "predictions_sha256": "c951be6e6ece90b0c0ae991d81bdaa73b7f7c7adbc9a856d7fda6c44aa4e7818",
      "raw_cer": 0.1829185024997769,
      "raw_wer": 0.4630610296032642,
      "reference_chars": 481843,
      "reference_words": 80633,
      "sample_count": 9081,
      "samples": 9081,
      "validation_loss": 1.639011752302197
    }
  ]
}
