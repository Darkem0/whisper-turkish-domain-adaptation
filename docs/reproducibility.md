# Yeniden Üretilebilirlik

## Sabitlenen temel bileşenler

Kontrollü A0–A7 serisi için aşağıdakiler deney kimliğinin parçasıdır:

- base model revision,
- tokenizer/processor revision,
- LoRA scope ve rank,
- train/validation manifest hashleri,
- sample schedule,
- augmentation assignment,
- random seed,
- optimizer ve scheduler ayarları,
- checkpoint mapping,
- decode profili,
- normalization ve metric implementasyonu,
- prediction JSONL SHA-256 değerleri.

## Ortak eğitim ayarları

- Base model: `openai/whisper-large-v3-turbo`
- Framework: plain Hugging Face Transformers
- PEFT: LoRA
- Rank: 16
- Alpha: 32
- Dropout: 0.05
- Batch size: 1
- Gradient accumulation: 16
- Precision: FP16
- Optimizer: AdamW
- Seed: 20260730

Deneyler arasında değişen temel unsur model scope, replay/anchor yaklaşımı, parent adapter ve schedule/augmentasyon politikasıdır.

## Frozen evaluation

Her checkpoint aynı frozen evaluation protokolünde ölçülür:

- MediaSpeech Clean
- MediaSpeech Phone
- MediaSpeech G.711
- CV Scripted
- FLEURS
- CV Spontaneous
- TSC

Her evaluation targetı için:

- sample ID sırası,
- prediction JSONL,
- prediction hash,
- raw/normalize WER,
- raw/normalize CER,
- checkpoint hash,
- dataset/manifest hash

korunmalıdır.

## A7 authoritative checkpoint mapping

- step-050: original A7 run
- step-100: original A7 run
- step-150: original A7 run
- step-200: isolated final continuation run

Final adapter SHA:

`fa5aa88e3d7fd1c16b7b7cdb0c516bc7d49210f3c5cb63c8405f280bad9e4894`

## A7 resume sınırlaması

A7 step-200, step-150 adapterından `ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET` biçiminde tamamlandı. Optimizer, scaler ve tam RNG state exact olarak geri yüklenmedi. Schedule konumu ve global step doğru biçimde 150/2400’den devam ettirildi.

Bu nedenle:

- toplam model güncelleme sayısı 200’dür,
- schedule 3.200 occurrence ile tamamlanmıştır,
- fakat koşu exact bit-for-bit resume değildir.

## Augmentasyon tekrar üretimi

A7 V3 augmented bucketları:

- phone_band,
- speed_075,
- noise_gain,
- phone_band_noise_gain.

Universal peak guard yalnız bu bucketlara uygulanır. Unchanged source anchor bucketlarına uygulanmaz.

Audit koşulları:

- deterministic output,
- finite waveform,
- non-silent output,
- final peak <= 0.980001,
- noise SNR korunumu,
- transcript değişmezliği.

## Bağımsız doğrulama ilkesi

Kaydedilmiş metric tabloları tek başına authoritative değildir. Nihai karşılaştırmalar prediction artefaktlarından bağımsız olarak yeniden hesaplanmalıdır. A5–A6 analiz hatası, bu ilkenin neden zorunlu olduğunu gösterir.

## Yayımlanmayan artefaktlar

Bu public depoda şu dosyalar bulunmaz:

- model checkpointleri,
- ham ses dosyaları,
- özel transkriptler,
- kişisel veri,
- erişim tokenları,
- makineye özgü mutlak yollar,
- lisansı belirsiz veri kopyaları.

Yerel yeniden üretimde kullanıcı, kendi lisanslı veri manifestlerini ve model erişimini sağlamalıdır.
