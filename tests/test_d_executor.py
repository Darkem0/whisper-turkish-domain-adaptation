import json
from pathlib import Path

from whisper_arge.d_executor import execute


def test_fake_executor_resumes_and_writes_complete_outputs(tmp_path: Path):
    manifest = tmp_path / "m.jsonl"
    manifest.write_text("".join(json.dumps({"sample_id": str(i), "audio_path": "x.wav", "reference_text": "merhaba"}) + "\n" for i in range(3)), encoding="utf-8")
    seen = []
    def fake(row):
        seen.append(row["sample_id"])
        return {"prediction": "merhaba", "peak_vram_bytes": 1}
    result = execute("D0", {"num_beams": 1}, manifest, tmp_path / "out", decoder=fake)
    assert result["processed"] == 3
    execute("D0", {"num_beams": 1}, manifest, tmp_path / "out", decoder=fake)
    assert seen == ["0", "1", "2"]
