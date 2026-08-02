# Tam Araştırma Raporu

## 1. Araştırma sorusu

Bu çalışma, `openai/whisper-large-v3-turbo` modelinin Türkçe telefon ve karşılıklı konuşma koşullarında nasıl iyileştirilebileceğini inceler. Temel soru, tek bir genel Türkçe fine-tuning yaklaşımının yeterli olup olmadığı değil; veri dağılımı, LoRA kapsamı, staged adaptation, telefon augmentasyonu ve decode stratejisinin birlikte nasıl davrandığıdır.

## 2. Deney çerçevesi

Kontrollü seri aşağıdaki sabit ilkelere dayanır:

- plain Hugging Face Transformers Whisper,
- LoRA/PEFT,
- base model ağırlıkları frozen,
- rank 16, alpha 32, dropout 0.05,
- batch size 1,
- gradient accumulation 16,
- FP16,
- ortak frozen evaluation setleri,
- raw ve normalize WER/CER,
- checkpoint bazlı değerlendirme,
- prediction artefaktlarının hashlenmesi,
- paired karşılaştırma.

## 3. Legacy deneylerden öğrenilenler

Legacy seri, yalnız MediaSpeech ile LoRA eğitiminin kötüleşme üretebildiğini; Common Voice ağırlıklı genel Türkçe eğitiminin bir domaini geliştirirken diğerini bozabildiğini; balanced-phone continuation ve repeat-safe decode’un uzun telefon örneğinde daha iyi davranabildiğini gösterdi.

Bu dönemden çıkan temel dersler:

- daha fazla Türkçe veri tek başına çözüm değildir,
- veri oranı kritik önemdedir,
- telefon bandı ve gürültü benzetimi hedef-domain için faydalı olabilir,
- decode stratejisi model eğitimi kadar belirleyici olabilir,
- temiz dış domainlerde negatif transfer mümkündür.

## 4. Kontrollü A0–A7 serisi

### A0 — Base model

Eğitimsiz `whisper-large-v3-turbo` referansıdır. Bütün iyileşme ve regresyonlar A0’a göre ölçülür.

### A2 — Encoder+decoder Q/V LoRA

A2, temiz/telefon/G.711/robustness tarafında iyileşme üretti. FLEURS tarafında belirgin regresyon gösterdi. Bu deney, birleşik encoder+decoder adaptasyonunun hedef-domain için çalışabileceğini; ancak genelleme maliyeti doğurabileceğini gösterdi.

### A3 — Encoder-only + %10 replay

A3 step-50, robustness tarafında istatistiksel olarak desteklenen iyileşme sağladı. Buna karşılık CV Scripted performansı bütün checkpointlerde güçlü biçimde kötüleşti. Replay, genel-domain korumasını yeterince sağlayamadı.

### A4 — Decoder-only, zero replay

A4, Phone ve robustness tarafında en güçlü adaylardan biri oldu. Phone için erken checkpoint, robustness için geç checkpoint daha iyi sonuç verdi. Bu, tek bir checkpointin bütün hedeflerde en iyi olmadığını gösterdi.

### A5 — Encoder-only, temiz schedule

A5 temiz schedule ve zero replay koşulunda Phone’u iyileştirdi; ancak A4’ün robustness sonucunu geçemedi. Encoder-only yaklaşımın katkısı sınırlı kaldı.

### A6 — Encoder+decoder, temiz schedule

A6, A5’ten farklı predictionlar üretti. İlk rapordaki “tam eşit ve CI=0” sonucu analiz scriptindeki path replacement hatasından kaynaklandı; A6 yanlışlıkla kendisiyle karşılaştırılmıştı. Düzeltme sonrasında 4.059 prediction farkı ve 27/28 hedefte farklı aggregate metric bulundu.

### A7 — Staged source-anchored balanced-phone integration

A7, A2 parent adapterından devam eden staged adaptation deneyidir. TSC yalnız “değiştirilmemiş source anchor” olarak kullanıldı; clean/read/general etiketi verilmedi. MediaSpeech ve CV Spontaneous telefon-benzeri kaynaklar olarak dengelendi. Telefon bandı, speed 0.75, noise/gain ve birleşik augmentasyon kullanıldı.

A7’nin ana sonucu:

- En iyi Phone: step-200, normalized WER `0.154285`
- En iyi robustness: step-150, normalized WER `0.147578`

Karşılaştırmalar:

- A2: `0.170825 → 0.154285`
- A4: `0.158385 → 0.154285`
- A6: `0.157203 → 0.154285`

Bu sonuç staged domain adaptation hipotezini destekler. Bununla birlikte CV Scripted tarafındaki maliyet, tek modelin bütün Türkçe domainlerinde en iyi olmadığını gösterir.

## 5. A7 eğitim zinciri ve resume notu

A7 eğitimi 200 optimizer step ve 3.200 schedule occurrence hedefledi. Eğitim sırasında kullanıcı terminal penceresini kapattığı için süreç kesildi. Son sağlam checkpoint step-150 idi. Exact optimizer state bulunmadığından final 50 step, `ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET` olarak tamamlandı.

Authoritative final step-200 adapter SHA:

`fa5aa88e3d7fd1c16b7b7cdb0c516bc7d49210f3c5cb63c8405f280bad9e4894`

Bu resume biçimi exact resume değildir ve bilimsel sınırlama olarak korunur.

## 6. A7 augmentasyon güvenliği

İlk noise/gain policy clipping üretti. Pozitif gain kaldırıldı ve 0/−3/−6 dB policy’ye geçildi. Daha sonra phone-band ve speed işlemlerinde filtre/resampling overshoot görüldü. Nihai V3 universal peak guard yalnız augmented bucketlara uygulandı.

V3 exhaustive audit:

- 1.493/1.493 augmented occurrence geçti,
- deterministic,
- finite,
- non-silent,
- maksimum final peak `0.9800000191`,
- noise SNR farkı `0.0 dB`.

Peak guard tetiklenmeleri:

- phone_band: 30,
- speed_075: 7,
- noise_gain: 6,
- combined: 6.

## 7. Telefon başarısı ile genel Türkçe başarısı aynı değildir

Telefon ve karşılıklı konuşma senaryolarında şu hatalar daha önemlidir:

- kısa utterance silinmesi,
- deletion artışı,
- tekrar ve hallucination,
- hızlı dönüşler,
- kesilen kelimeler,
- sayı, tarih, tutar ve özel isim hataları,
- kanal daralması ve G.711 etkisi.

Bu nedenle MediaSpeech Phone, G.711, robustness proxy ve CV Spontaneous sonuçları hedef-domain panelinde; MediaSpeech Clean, CV Scripted, FLEURS ve TSC ise genel-domain izleme panelinde tutulur.

## 8. Nihai bilimsel sınıflandırma

- `staged_domain_adaptation_supported`
- `staged_domain_adaptation_with_general_domain_cost`
- `augmentation_contribution_inconclusive`
- `open_data_experiment_line_completed`

Augmentasyon katkısı “inconclusive” kabul edilir; çünkü A7 aynı anda parent continuation, source rebalancing ve çoklu augmentasyonu değiştirdi. Bu tasarım nihai sistem entegrasyonunu ölçer, tek tek bileşenlerin nedensel etkisini ayırmaz.

## 9. Sonuç

A7, kontrollü seride en iyi Phone WER sonucunu verdi. A4 robustness tarafında güçlü bir Pareto adayı olarak kaldı. En doğru sonuç “A7 her yerde daha iyi” değildir. Doğru sonuç şudur:

> Staged domain adaptation, telefon-benzeri açık veri proxy’sinde iyileşme sağlamıştır; ancak genel-domain performans maliyeti oluşmuştur. Türkçe ASR için tek adapter yerine domain-aware seçim veya çoklu aday değerlendirmesi daha gerçekçi bir yaklaşımdır.
