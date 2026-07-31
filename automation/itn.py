# ruff: noqa
from __future__ import annotations
import re

ONES={"sıfır":0,"bir":1,"iki":2,"üç":3,"dört":4,"beş":5,"altı":6,"yedi":7,"sekiz":8,"dokuz":9,"on":10,"yirmi":20,"otuz":30,"kırk":40,"elli":50,"altmış":60,"yetmiş":70,"seksen":80,"doksan":90}
def _number(words: list[str]) -> int | None:
    total=cur=0
    for w in words:
        if w in ONES: cur += ONES[w]
        elif w=="yüz": cur=max(1,cur)*100
        elif w=="bin": total += max(1,cur)*1000; cur=0
        else: return None
    return total+cur if words else None
def normalize(text: str) -> dict:
    raw=text; changes=[]; canonical=text
    def money(m):
        n=_number(m.group(1).split())
        if n is None:return m.group(0)
        new=f"{n:,}".replace(",", ".")+" TL"; changes.append({"from":m.group(0),"to":new,"kind":"money"});return new
    canonical=re.sub(r"\b((?:sıfır|bir|iki|üç|dört|beş|altı|yedi|sekiz|dokuz|on|yirmi|otuz|kırk|elli|altmış|yetmiş|seksen|doksan|yüz|bin)(?:\s+(?:sıfır|bir|iki|üç|dört|beş|altı|yedi|sekiz|dokuz|on|yirmi|otuz|kırk|elli|altmış|yetmiş|seksen|doksan|yüz|bin)){0,5})\s+lira\b",money,canonical,flags=re.I)
    canonical=re.sub(r"\byüzde\s+(bir|iki|üç|dört|beş|altı|yedi|sekiz|dokuz|on)\b",lambda m: "%"+str(ONES[m.group(1)]),canonical,flags=re.I)
    if canonical != raw and not changes: changes.append({"kind":"percent"})
    return {"raw_text":raw,"canonical_text":canonical,"presentation_text":canonical,"normalization_changes":changes}
