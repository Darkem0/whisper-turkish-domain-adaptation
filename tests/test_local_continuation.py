import json
from pathlib import Path

from whisper_arge.local_continuation import reconcile_queue, sha256_file


def test_reconcile_does_not_turn_prototype_into_execution_pass(tmp_path: Path):
    (tmp_path / "state").mkdir()
    (tmp_path / "state/events.jsonl").write_text("", encoding="utf-8")
    (tmp_path / "state/experiment_queue.json").write_text(json.dumps([{"id": "P3_quality", "status": "PASSED"}]), encoding="utf-8")
    result = reconcile_queue(tmp_path)
    row = json.loads((tmp_path / "state/experiment_queue.json").read_text(encoding="utf-8"))[0]
    assert row["implementation_status"] == "PASSED" and row["execution_status"] == "BLOCKED"
    assert result["progress"] == 0


def test_hash_is_stable(tmp_path: Path):
    item = tmp_path / "x.wav"
    item.write_bytes(b"audio")
    assert sha256_file(item) == sha256_file(item)
