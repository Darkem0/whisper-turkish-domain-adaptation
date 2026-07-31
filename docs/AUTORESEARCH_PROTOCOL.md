# Autoresearch protokolü

## Deney öncesi

1. Git çalışma ağacı temiz olmalı; araştırma kodu ve config değişikliği tek,
   izole commit olmalıdır.
2. `verify-eval-lock` ve testler geçmelidir.
3. Dataset manifest SHA-256 ve eval-lock SHA-256 resolved config'e yazılmalıdır.
4. `reserve-run` aynı config + dataset hash + seed imzasını ledger'da arar.
   Bulursa koşuyu reddeder.
5. MediaSpeech arşiv checksum/lisansı ve Khan Math lisansı
   `data/registry.json` içinde çözülmeden bu kaynaklarla run rezerve edilemez.

## Komut iskeleti

```powershell
python -m pip install -r requirements/research-cu121.lock.txt
python -m pip install -e ".[dev]" --no-deps
python -m whisper_arge.cli verify-eval-lock
python -m whisper_arge.cli validate-manifest data/materialized/train_multidomain_v1.jsonl
python -m whisper_arge.cli reserve-run --config configs/resolved/S000.json
```

`reserve-run` eğitim başlatmaz. Run klasöründe resolved config ve ortam
snapshot'ı üretir, ledger'a reservation yazar. Eğitim uygulaması bu sözleşmeye
uyarak checkpoint, prediction, süre ve peak VRAM dosyalarını tamamlamalıdır.

## Kabul/ret ve Git

- Başarılı koşu: `decision.json` ve ledger `accepted` eventi eklenir; yalnızca
  araştırma kodu/config/özet sonuç commit edilir. Büyük checkpoint/prediction
  artifact deposunda tutulur; bundle hash commit edilir.
- Başarısız koşu: sebep ledger'a `rejected` olarak eklenir. Adaya özel kod/config
  commit'i `git revert <candidate_commit>` ile geri alınır. `reset --hard`
  kullanılmaz.
- Legacy deneyler yeni run gibi işaretlenemez. Denylist recipe kimlikleri yeni
  compute için yasaktır.

## Artifact bütünlüğü

Her koşuda aşağıdaki zincir kurulmalıdır:

`dataset revision -> source manifest -> materialized audio SHA -> train manifest
SHA -> resolved config SHA -> run signature -> predictions SHA -> metrics SHA ->
decision -> artifact bundle SHA`

Eksik bir halka koşuyu “reproducible” olmaktan çıkarır.

## Sabit compute

Smoke için 200 step, batch 1, accumulation 16 ve aynı evaluation periyodu;
medium için 750 step üst bütçe kullanılır. Early stopping üst bütçeyi
azaltabilir fakat artıramaz. OOM yaşayan aday için batch/accumulation değiştirmek
aynı deney değildir; yeni hipotez kimliği gerekir.
