# ruff: noqa
from pathlib import Path
from automation.core import default_queue, profile, write, read
from whisper_arge.normalization import normalize_turkish
from automation.itn import normalize as itn
from automation.quality import quality_record, second_pass_profile

def test_decode_profiles_change_one_family_setting():
    assert profile("D2")["num_beams"] == 3
    assert profile("D4")["condition_on_prev_tokens"] is False
    assert profile("D6")["temperature"] == [0.0, 0.2, 0.4, 0.6]

def test_queue_quarantines_legacy_name():
    assert "A3_legacy_aborted_step34_invalid" not in {x["id"] for x in default_queue()}

def test_atomic_json_roundtrip(tmp_path: Path):
    path=tmp_path/"state.json"; write(path,{"ok":True}); assert read(path,{}) == {"ok":True}

def test_existing_normalizer_not_changed():
    assert normalize_turkish("Ankara'da") == "ankarada"

def test_deterministic_itn_preserves_raw_and_converts_unambiguous_money():
    value=itn("iki bin beş yüz lira")
    assert value["raw_text"] == "iki bin beş yüz lira"
    assert value["canonical_text"] == "2.500 TL"

def test_quality_routes_only_one_second_pass():
    assert second_pass_profile(quality_record("tekrar tekrar tekrar tekrar", 5)) == "D4"
