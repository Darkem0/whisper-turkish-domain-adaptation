from __future__ import annotations

import json
from pathlib import Path

import pytest

from whisper_arge.evaluation import evaluate
from whisper_arge.ledger import assert_not_run, experiment_signature
from whisper_arge.lock import verify_lock
from whisper_arge.manifests import validate_manifest
from whisper_arge.matrix import validate_matrix
from whisper_arge.metrics import corpus_metrics
from whisper_arge.normalization import normalize_turkish
from whisper_arge.provenance import assert_recipe_allowed, validate_registry_sources
from whisper_arge.selection import select_rows

ROOT = Path(__file__).resolve().parents[1]


def test_turkish_normalization_preserves_dotless_i_and_digits() -> None:
    assert normalize_turkish("IŞIK, İZMİR'de 42₺!") == "ışık izmirde 42"


def test_metrics_are_corpus_level_not_mean_of_sample_rates() -> None:
    result = corpus_metrics([("bir", "yanlış"), ("bir iki üç dört", "bir iki üç dört")])
    assert result["raw_wer"] == pytest.approx(0.2)
    assert result["raw_cer"] > 0


def test_manifest_and_evaluation_are_domain_separated() -> None:
    manifest = ROOT / "tests/fixtures/eval_manifest.jsonl"
    predictions = ROOT / "tests/fixtures/predictions.jsonl"
    assert validate_manifest(manifest)["rows"] == 3
    report = evaluate(manifest, predictions)
    assert set(report["domain_metrics"]) == {"common_voice_clean", "common_voice_phone"}
    assert report["domain_metrics"]["common_voice_clean"]["normalized_wer"] == 0
    assert report["domain_metrics"]["common_voice_phone"]["normalized_wer"] > 0


def test_prediction_coverage_is_strict(tmp_path: Path) -> None:
    path = tmp_path / "predictions.jsonl"
    path.write_text('{"sample_id":"cv-1","prediction":"x"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="coverage mismatch"):
        evaluate(ROOT / "tests/fixtures/eval_manifest.jsonl", path)


def test_selection_is_stable_and_seeded() -> None:
    rows = [
        {
            "dataset_id": "d",
            "dataset_revision": "r",
            "split": "test",
            "stable_source_id": str(index),
        }
        for index in range(10)
    ]
    assert select_rows(rows, 3, 7) == select_rows(reversed(rows), 3, 7)
    assert select_rows(rows, 3, 7) != select_rows(rows, 3, 8)


def test_matrix_has_single_declared_change_per_candidate() -> None:
    result = validate_matrix(ROOT / "experiments/matrix_v1.jsonl")
    assert result["experiments"] >= 20
    assert result["smoke"] > result["medium"]


def test_duplicate_signature_is_rejected(tmp_path: Path) -> None:
    config = {
        "model": "openai/whisper-large-v3-turbo",
        "model_revision": "revision",
        "dataset_manifest_sha256": "a" * 64,
        "evaluation_lock_sha256": "b" * 64,
        "seed": 1,
        "training": {"budget_steps": 200},
    }
    signature = experiment_signature(config)
    ledger = tmp_path / "ledger.jsonl"
    ledger.write_text(
        json.dumps({"event": "completed", "experiment_id": "old", "signature": signature})
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="duplicate experiment signature"):
        assert_not_run(config, ledger)


def test_eval_lock_is_current() -> None:
    assert verify_lock(ROOT / "evaluation/EVAL_LOCK.json") == []


def test_legacy_recipe_is_blocked() -> None:
    with pytest.raises(ValueError, match="legacy denylist"):
        assert_recipe_allowed(
            "legacy_mediaspeech_only_1epoch_lora",
            ROOT / "configs/legacy_denylist.json",
        )


def test_unresolved_registry_source_blocks_run(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(
        json.dumps(
            {
                "dataset_id": "openslr/SLR108/MediaSpeech/TR",
                "dataset_revision": "SLR108",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="checksum is unresolved"):
        validate_registry_sources(manifest, ROOT / "data/registry.json")
