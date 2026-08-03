# Türkçe Telefon Konuşmaları için Whisper Large-v3-Turbo Uyarlaması

Bu depo, `openai/whisper-large-v3-turbo` ile açık Türkçe veri ve telefon-benzeri
bozulmalar üzerinde yapılan kontrollü ASR araştırmasını belgeler. Sonuçlar
MediaSpeech, Common Voice, FLEURS ve TSC gibi açık-veri proxylerinden gelir;
gerçek çağrı merkezi performansı veya şirket verisi sonucu değildir.

## Araştırma özeti

- D3, desteklenen decoding profilidir; MEM0 varsayılan bellek profilidir.
- A2 encoder+decoder Q/V LoRA, hedef proxyde kazanç sağladı ancak FLEURS
  regresyonu nedeniyle production adayı değildir.
- A2 robustness proxy `0.14655`, A0 farkı `-0.01508` ve %95 CI
  `[-0.03303, -0.00396]` ile iyileşti; FLEURS normalized WER `0.17693`
  olduğu için promotion gate geçmedi.
- `A3_legacy_aborted_step34_invalid` 34/200 adımda durduruldu; geçerli adapter
  veya sonuç üretmedi ve hiçbir koşulda resume/promotion edilmez.
- A3 encoder-only + replay, CV Scripted guardrail nedeniyle promotable değildir.
- A4 decoder-only, A5 encoder-only ve A6 encoder+decoder temiz-schedule
  ablationları diagnostic-only olarak korunur.
- A7, A2 parent adapter, TSC source anchor ve staged telefon augmentasyonu
  kullanır. En iyi Phone normalized WER `0.154285` (step-200), en iyi
  robustness proxy `0.147578` (step-150) değeridir. Step-200, step-150’den
  optimizer-state olmadan devam eden izole bir continuation’dır.

Telefon hedefi ile genel Türkçe izleme ayrı değerlendirilir: Phone/G.711 ve
robustness proxy iyileşmesi CV Scripted veya FLEURS maliyetini gizlemez; aynı
şekilde genel-domain maliyeti de telefon proxy sonucunu otomatik geçersiz kılmaz.

## Veri ve yöntem

Araştırmada Common Voice TR, MediaSpeech TR, FLEURS TR, TSC ve tarihsel Khan
Academy Türkçe kaynakları kullanılmış veya değerlendirilmiştir. Manifestler,
normalizasyon, WER/CER ve frozen evaluation hedefleri kilitli artefaktlarla
izlenir. LoRA/PEFT Q/V kapsamları, replay/source-anchor seçenekleri ve
phone-band, G.711, 0.75x speed, noise/gain augmentasyonları kontrollü olarak
incelenmiştir. Legacy VAD/segmentasyon ve repeat-safe decode bulguları tarihsel
bağlamdır; mevcut kontrollü seriyle havuzlanmaz.

## Deneyler

| Deney | Amaç | Değişiklik | Durum | Temel sonuç |
|---|---|---|---|---|
| A0 | Referans | Base model | successful | Kontrollü başlangıç |
| A2 | Hedef proxy | Encoder+decoder Q/V LoRA | failed promotion | Robustluk kazancı, FLEURS maliyeti |
| A3 | Replay hipotezi | Encoder-only + replay | failed | Promotable checkpoint yok |
| A4 | Scope ablation | Decoder-only, zero replay | diagnostic_only | Güçlü Phone ablationı |
| A5 | Scope ablation | Encoder-only, clean schedule | limited | A4’ü domine etmedi |
| A6 | Scope ablation | Encoder+decoder, clean schedule | diagnostic_only | Düzeltilmiş karşılaştırma |
| A7 | Entegrasyon | A2 parent + anchor + augmentation | successful | En iyi gözlenen Phone proxy |

## Çalıştırma ve doğrulama

```powershell
python -m pip install -e ".[dev]"
python -m pytest
python -m whisper_arge.cli verify-eval-lock
python -m whisper_arge.cli validate-matrix experiments/matrix_v1.jsonl
```

Araştırma bağımlılıkları için `requirements/research-cu121.lock.txt` kullanılır.
Yeni eğitim veya inference, ilgili manifest/evaluation lock ve GPU preflight
doğrulanmadan başlatılmamalıdır.

## Gizlilik ve yayın sınırı

WAV dosyaları, ham transkriptler, checkpoint/adapter ağırlıkları, cache, yerel
loglar ve şirket verisi GitHub’a eklenmez. Şirket-domain değerlendirmesi ancak
yetkilendirilmiş secure root, insan doğrulamalı referanslar ve leakage-safe
development/final-holdout ayrımı ile yapılabilir.

## Belgeler

- [Tam araştırma raporu](docs/full_research_report.md)
- [Deney kataloğu](docs/experiment_catalog.md)
- [Telefon odaklı değerlendirme](docs/call_oriented_evaluation.md)
- [Negatif sonuçlar](docs/negative_results.md)
- [Yeniden üretilebilirlik](docs/reproducibility.md)
- [Artefakt haritası](docs/artifact_map.md)
