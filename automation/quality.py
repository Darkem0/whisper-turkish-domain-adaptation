# ruff: noqa
from __future__ import annotations
import re
from collections import Counter

def quality_record(text: str, duration_seconds: float | None = None, *, average_logprob: float | None = None, no_speech_probability: float | None = None, detected_language: str = "tr") -> dict:
    words = re.findall(r"\w+", text, flags=re.UNICODE)
    repeated = sum(n - 1 for n in Counter(words).values() if n > 1)
    wpm = len(words) / (duration_seconds / 60) if duration_seconds and duration_seconds > 0 else 0.0
    reasons=[]
    if not text.strip(): reasons.append("empty_output")
    if detected_language != "tr": reasons.append("language_mismatch")
    if re.search(r"[\uE000-\uF8FF]", text): reasons.append("suspicious_unicode")
    if duration_seconds and (wpm > 260 or (duration_seconds > 10 and wpm < 2)): reasons.append("duration_text_outlier")
    if repeated >= max(3, len(words)//3): reasons.append("repetition")
    status = "PASS" if not reasons else ("RETRY_ALTERNATIVE_DECODE" if set(reasons) <= {"empty_output", "repetition", "duration_text_outlier"} else "REVIEW")
    return {"empty_output": not bool(text.strip()), "word_count":len(words), "words_per_minute":round(wpm,3), "repetition_score":round(repeated/max(1,len(words)),3), "compression_ratio":None, "average_logprob":average_logprob, "no_speech_probability":no_speech_probability, "detected_language":detected_language, "language_mismatch":detected_language != "tr", "suspicious_unicode":bool(re.search(r"[\uE000-\uF8FF]", text)), "duration_text_outlier":"duration_text_outlier" in reasons, "quality_status":status, "quality_reasons":reasons}

def second_pass_profile(record: dict) -> str | None:
    r=set(record["quality_reasons"])
    if "repetition" in r: return "D4"
    if "empty_output" in r: return "D2"
    if record.get("average_logprob") is not None and record["average_logprob"] < -1: return "D6"
    return None
