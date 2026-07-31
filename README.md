# Whisper Large-v3-turbo Türkçe Autoresearch

Bu depo, yalnızca `openai/whisper-large-v3-turbo` ve açık, etiketli Türkçe
konuşma verileriyle çok-domain ASR araştırması içindir. Şirket/çağrı verisi,
pseudo-label, kapalı veri ve alternatif final ASR modelleri bu fazın dışındadır.

Mevcut durum:

- Eski deneyler, artifactleri kayıp **legacy kayıtlar** olarak
  `ledger/experiments.jsonl` içinde korunur; yeniden üretilmiş sayılmaz.
- Değerlendirme tanımı, normalizer ve metric kodu
  `evaluation/EVAL_LOCK.json` ile kilitlenir.
- Common Voice, MediaSpeech, FLEURS ve iki Khan Academy domaini ayrı raporlanır.
- Sabit telefon/codec bozulmaları ayrı domainlerdir; temiz-domain negatif
  transferi kabul kararına dahildir.
- İlk yeni deney matrisi kısa 200-step eleme ile başlar. Uzun eğitim bu
  başlangıç aşamasının parçası değildir.

## Hızlı doğrulama

```powershell
python -m pip install -e ".[dev]"
python -m pytest
python -m whisper_arge.cli verify-eval-lock
python -m whisper_arge.cli validate-matrix experiments/matrix_v1.jsonl
python -m whisper_arge.cli ledger-summary ledger/experiments.jsonl
```

Gerçek araştırma ortamı için RTX 4070/CUDA 12.1 kilidi:

```powershell
python -m pip install -r requirements/research-cu121.lock.txt
python -m pip install -e ".[dev]" --no-deps
python -m whisper_arge.cli capture-environment > runs/environment-preflight.json
```

`requirements/research-cu121.lock.txt` geçmişte bu makinede doğrulanmış
PyTorch/CUDA ailesini temel alır; gerçek koşudan önce `capture-environment`
çıktısında CUDA availability ve GPU adı ayrıca doğrulanmalıdır.

Makinede `python` PATH'te yoksa Codex bundled Python kullanılabilir:

```powershell
$env:PYTHONNOUSERSITE="1"
C:\Users\emre\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pip install -e ".[dev]"
C:\Users\emre\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest
```

## Araştırma akışı

1. `data/registry.json` revisionlarını ve lisansları doğrula.
2. Kaynak manifestleri üret; her manifest için SHA-256 kaydet.
3. `evaluation/suite_v1.json` seçimini bir kez materialize et ve lock dosyasına
   gerçek manifest/audio hashlerini ekle.
4. Base model predictionlarını aynı decode sözleşmesiyle bir kez üret.
5. Matristeki smoke deneylerini yalnızca tek ana hipotez değiştirerek çalıştır.
6. Kabul edilen adayı ledger'a yaz, artifact bundle'ını sakla ve ayrı commit et.
   Reddedilen adayın kod/config değişikliğini izole commit üzerinden revert et.
7. Yalnızca smoke eşiğini geçen adayları 500–1000 step'e yükselt.

Detaylı plan için `docs/RESEARCH_PLAN.md`, komut ve artifact sözleşmesi için
`docs/AUTORESEARCH_PROTOCOL.md` dosyalarına bakın.
