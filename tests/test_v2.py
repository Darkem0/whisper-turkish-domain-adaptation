import json
from pathlib import Path

import pytest

from whisper_arge.calibration import smoke_calibration
from whisper_arge.evaluation_v2 import evaluate_v2
from whisper_arge.materialize import materialize_rows
from whisper_arge.matrix import validate_matrix
from whisper_arge.tsc import assert_tsc_use_mode, index_tsc

ROOT = Path(__file__).resolve().parents[1]


def test_v2_matrix_and_calibration_gate(tmp_path: Path) -> None:
    assert validate_matrix(ROOT / "experiments/matrix_v2.jsonl")["experiments"] == 8
    path = tmp_path / "calibration.json"
    path.write_text(json.dumps({"results": [{"id": item, "normalized_wer_200": value, "normalized_wer_750": value} for item, value in zip(("A1", "A2", "A3", "A6"), (0.4, 0.3, 0.2, 0.1))]}), encoding="utf-8")
    assert smoke_calibration(path)["autoresearch_promotion_enabled"] is True


def test_v2_materializer_is_group_disjoint_and_dry_run(tmp_path: Path) -> None:
    source = tmp_path / "source.jsonl"
    rows = [{"sample_id": str(index), "dataset_id": "d", "dataset_revision": "r", "stable_source_id": f"s{index // 2}", "source_id": f"s{index // 2}", "audio": "missing.wav"} for index in range(8)]
    source.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    report = materialize_rows(source, tmp_path / "out.jsonl", holdout_fraction=0.5, seed=1, group_field="source_id", dry_run=True)
    assert report["rows"] == 8
    assert report["holdout_rows"] in {0, 2, 4, 6, 8}


def test_v2_evaluation_reports_disfluency_and_paired_delta(tmp_path: Path) -> None:
    manifest = tmp_path / "m.jsonl"
    rows = [
        {"sample_id": "clean", "domain": "tsc_holdout", "domain_group": "primary", "audio": "x", "audio_sha256": "a" * 64, "reference": "[disfluency] merhaba", "dataset_id": "d", "dataset_revision": "r", "split": "test", "source_id": "s"},
        {"sample_id": "phone", "domain": "tsc_phone", "domain_group": "derived", "audio": "x", "audio_sha256": "b" * 64, "reference": "[disfluency] merhaba", "dataset_id": "d", "dataset_revision": "r", "split": "test", "paired_clean_sample_id": "clean", "degradation": "phone"},
    ]
    manifest.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    predictions = tmp_path / "p.jsonl"
    predictions.write_text('{"sample_id":"clean","prediction":"[disfluency] merhaba"}\n{"sample_id":"phone","prediction":"merhaba"}\n', encoding="utf-8")
    report = evaluate_v2(manifest, predictions)
    assert "disfluency_f1" in report["domain_metrics"]["tsc_holdout"]
    assert report["paired_degradation"]["phone"]["point"] > 0


def test_tsc_modes_and_archive_index(tmp_path: Path) -> None:
    import tarfile

    assert_tsc_use_mode("research_provisional")
    with pytest.raises(ValueError, match="clearance-evidence"):
        assert_tsc_use_mode("commercial_cleared")
    payload = tmp_path / "clip.wav"
    payload.write_bytes(b"wav")
    archive = tmp_path / "tsc.tar.gz"
    with tarfile.open(archive, "w:gz") as handle:
        handle.add(payload, arcname="news/source-a/clip.wav")
    result = index_tsc(archive, tmp_path / "index.jsonl", tmp_path / "leakage.json", revision="rev")
    assert result["audio_rows"] == 1
    assert result["grouping_quality"] == "utterance_only"
    assert "utterance-clip" in (tmp_path / "index.jsonl").read_text(encoding="utf-8")
