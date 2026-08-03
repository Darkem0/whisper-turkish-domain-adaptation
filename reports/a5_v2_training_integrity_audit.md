# A5_v2 training integrity audit

{
  "status": "PASSED",
  "problems": [],
  "checkpoints": [
    {
      "checkpoint": "step-050",
      "adapter_sha256": "c1e92cf49fb5c2797717c36ff79cd73ab8908ee0d9b165e930eee5ec4ece0511",
      "optimizer_step": 50,
      "consumed_microbatches": 800,
      "config_sha256": "65ddce80f9dba065e0b0c29ca5c13d3ccc92d928aefe561134223a3bd4a5caad",
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
      "adapter_sha256": "2e575e7e7491524fa5ab906c0497595ffd8ee6608a1652a0225aff58bd7ba4e6",
      "optimizer_step": 100,
      "consumed_microbatches": 1600,
      "config_sha256": "65ddce80f9dba065e0b0c29ca5c13d3ccc92d928aefe561134223a3bd4a5caad",
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
      "adapter_sha256": "c5c608bb40155e8f40088ac586fd9a3e5b47cbe3cd765df679736377c59cc18b",
      "optimizer_step": 150,
      "consumed_microbatches": 2400,
      "config_sha256": "65ddce80f9dba065e0b0c29ca5c13d3ccc92d928aefe561134223a3bd4a5caad",
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
      "adapter_sha256": "b09e5029a1bf7b327d0e4a77a8b92b8a9c1115d39a1204f9c2afd9c3c1b5d8c6",
      "optimizer_step": 200,
      "consumed_microbatches": 3200,
      "config_sha256": "65ddce80f9dba065e0b0c29ca5c13d3ccc92d928aefe561134223a3bd4a5caad",
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
    "trainable_parameters": 2621440,
    "base_weights_frozen": true,
    "contracts": {
      "contracts/A5_v2_data_manifest.lock.json": "35e14b8e2f79e3fe1c4375e8ad814c99f71515693b8f7f4d7e44d7dc10f341fe",
      "contracts/A5_v2_eval_contract.yaml": "a62c6f6403ae790033c6e1dd8bc2436a564970a65f18d8d7dc8e2126f84639bf",
      "contracts/A5_v2_training_contract.yaml": "1a2c0976fab9d1db6ddccb59d6736cc786b3a941dc256a9b68b10727431131df"
    }
  },
  "validations": [
    {
      "evaluation_wall_seconds": 2864.860714899987,
      "normalized_cer": 0.1500157808619673,
      "normalized_wer": 0.2706121639051493,
      "optimizer_step": 50,
      "predictions": "runs/A5_v2_fresh_base_200/validations/step-050/predictions.jsonl",
      "predictions_sha256": "23cb3ccbb5df8d26446d8553828b4529b9f451f3afeb2e7f67923a9c467e3b83",
      "raw_cer": 0.2139120003818671,
      "raw_wer": 0.5099649027073283,
      "reference_chars": 481843,
      "reference_words": 80633,
      "sample_count": 9081,
      "samples": 9081,
      "validation_loss": 2.54700496099342
    },
    {
      "evaluation_wall_seconds": 2738.9208079999953,
      "normalized_cer": 0.14569473168381797,
      "normalized_wer": 0.2661350332374243,
      "optimizer_step": 100,
      "predictions": "runs/A5_v2_fresh_base_200/validations/step-100/predictions.jsonl",
      "predictions_sha256": "3cace4b2554aee11f76abd30fb2ca95dc8ba5e14a52a2e177200018875342fff",
      "raw_cer": 0.20900168727158017,
      "raw_wer": 0.5044336685972245,
      "reference_chars": 481843,
      "reference_words": 80633,
      "sample_count": 9081,
      "samples": 9081,
      "validation_loss": 2.491956075872701
    },
    {
      "evaluation_wall_seconds": 2628.951637499995,
      "normalized_cer": 0.14378649324329937,
      "normalized_wer": 0.26485762476436153,
      "optimizer_step": 150,
      "predictions": "runs/A5_v2_fresh_base_200/validations/step-150/predictions.jsonl",
      "predictions_sha256": "e0c1633f6e0bf7108d74ae644f01cb3836f84f37b22e5aecb99a9738234c13f4",
      "raw_cer": 0.20731441569141815,
      "raw_wer": 0.5013456029169199,
      "reference_chars": 481843,
      "reference_words": 80633,
      "sample_count": 9081,
      "samples": 9081,
      "validation_loss": 2.44398810230495
    },
    {
      "evaluation_wall_seconds": 5473.601836499991,
      "normalized_cer": 0.14336290168522994,
      "normalized_wer": 0.26462198630816547,
      "optimizer_step": 200,
      "predictions": "runs/A5_v2_fresh_base_200/validations/step-200/predictions.jsonl",
      "predictions_sha256": "ca6b029c30fbfcce179accd50891a9416a597ad0d93dcdf34dd15c2e2f7416c7",
      "raw_cer": 0.20690141809676596,
      "raw_wer": 0.5002294345987375,
      "reference_chars": 481843,
      "reference_words": 80633,
      "sample_count": 9081,
      "samples": 9081,
      "validation_loss": 2.425177686842721
    }
  ]
}
