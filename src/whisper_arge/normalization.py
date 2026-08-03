from __future__ import annotations

import re
import unicodedata

NORMALIZER_ID = "tr_basic_v1"


def normalize_turkish(text: str) -> str:
    """Deterministic surface normalization for normalized WER/CER.

    This intentionally does not expand numbers, abbreviations, currencies or
    morphology. Such transformations can hide semantically important ASR errors.
    """

    text = unicodedata.normalize("NFKC", text)
    text = text.replace("İ", "i").replace("I", "ı").lower()
    # Turkish proper-noun suffixes use apostrophes; punctuation removal must not
    # turn a single lexical token such as "Ankara'da" into two WER tokens.
    text = text.replace("'", "").replace("’", "")
    text = re.sub(r"[^\w\sçğıöşü]", " ", text, flags=re.UNICODE)
    text = re.sub(r"_+", " ", text)
    return " ".join(text.split())
