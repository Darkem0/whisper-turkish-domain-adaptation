# Araştırma planı

## Araştırma sorusu

RTX 4070 sınıfı 12 GB GPU ve yalnızca açık, etiketli Türkçe konuşma verileri
ile `openai/whisper-large-v3-turbo` için hangi LoRA/veri/augmentasyon tarifi
temiz ve bozulmuş domainlerin tümünde en iyi dengeli sonucu verir?

Bu fazda şirket verisi, ham çağrı verisi, pseudo-label, Qwen/Omni veya başka
bir final ASR modeli yoktur. Base Whisper yalnızca sabit referanstır.

## Değişmezler

- Model ve model revision sabittir.
- Eval örnekleri, normalizer, metric kodu ve decode sözleşmesi kilitlidir.
- Seed, maksimum step, effective batch ve checkpoint aralığı aynı kademede
  sabittir.
- Her aday yalnızca `experiments/matrix_v1.jsonl` içindeki tek `change.path`
  alanını değiştirir.
- Raw ve normalized WER/CER corpus-level hesaplanır; örnek WER ortalaması
  kullanılmaz.
- Karar metriği domain-macro normalized WER'dir. Temiz-domain negatif transfer
  kapıları ayrıca zorunludur.

## Kademeli arama

### Kademe 0 — materialization ve base referansı

Dataset revision/lisans kayıtlarını tamamla; immutable train/eval manifestlerini
ve ses hashlerini üret. Eval suite'in smoke, selection ve full katmanlarını bir
kez dondur. Base model predictionlarını aynı decode koşuluyla cache'le.

Bu kademe bitmeden hiçbir LoRA koşusu geçerli değildir.

### Kademe 1 — 200-step smoke

Önce S000 çalışır. Ardından tek değişkenli adaylar:

- sampling/karışım oranı ve clean replay,
- encoder-only, decoder-only, encoder+decoder,
- target module, rank ve learning rate,
- telefon, codec, gürültü ve speed augmentasyonlarının ayrı ablation'ları,
- curriculum.

Numerik hata, OOM, eksik prediction veya eval-lock uyuşmazlığı doğrudan rettir.
Başarı, yalnızca bir domain kazanımı değil tüm kabul kapılarının geçmesidir.

### Kademe 2 — 750-step doğrulama

Her hipotez ailesinden en fazla bir smoke kazananı terfi eder. Kazanan tarifte
early stopping ve yalnızca kazanan augmentasyon için oran sweep'i yapılır.
Standart LoRA baseline'ı belirlendikten sonra DoRA/AdaLoRA denenebilir.

### Kademe 3 — uzun eğitim

Bu ilk görevde başlatılmaz. En fazla 2–3 aday, selection ve full eval sonuçları
ile gerekçelendirilerek daha güçlü bilgisayara aktarılır.

## Çok-domain checkpoint seçimi

Checkpoint skoru tek validation loss değildir:

1. domain başına normalized WER,
2. eşit ağırlıklı domain-macro normalized WER,
3. temiz domain ortalama ve en kötü negatif transfer,
4. bozulmuş domain macro,
5. peak VRAM ve wall time

birlikte saklanır. Kabul için `evaluation/suite_v1.json` eşikleri zorunludur.
Eşitlikte daha düşük rank/VRAM ve daha erken checkpoint seçilir.

## İlk araştırma sırası

1. S000 standard LoRA.
2. S010–S021 sampling/mix/replay.
3. Kazanan veri tarifi üzerinde S030–S061 LoRA scope/target/rank/LR.
4. Kazanan LoRA üzerinde S070–S080 ayrı augmentasyon/curriculum ablation.
5. Kazanan smoke tarifiyle M100.
6. M110 ve koşullu M120/M121.
7. Yalnız bundan sonra M130/M131.

Bu sıra, sonraki ailelerin önceki ailenin seçilmiş sonucunu parent olarak
materialize etmesini gerektirir; matristeki parent adları planlama soyudur,
gerçek resolved config hashleri ledger'da tutulur.

