# Negatif Sonuçlar ve Araştırma Hataları

Negatif sonuçlar bu çalışmanın ikincil notları değil, ana bilimsel çıktılarındandır.

## Model ve veri tarafındaki negatif sonuçlar

### MediaSpeech-only LoRA

İlk legacy deneyde yalnız MediaSpeech ile LoRA eğitimi, aynı domain ölçümünde dahi kötüleşme üretti. Bu sonuç, “Türkçe veri eklemek otomatik olarak Türkçe ASR’yi geliştirir” varsayımını reddeder.

### Genel Türkçe LoRA ve domain kayması

Common Voice ağırlıklı eğitim Common Voice tarafını iyileştirirken MediaSpeech ve bazı dış-domain sonuçlarını bozdu. Veri oranı ve konuşma türü, toplam veri miktarından daha belirleyici olabilir.

### Replay’in sınırlı etkisi

A3’te %10 replay, CV Scripted forgetting’i önlemeye yetmedi. Replay’in varlığı tek başına genel-domain koruması sağlamaz.

### Joint scope sinerjisinin belirsizliği

A6 encoder+decoder yaklaşımı, en iyi tek-scope adayları açık biçimde aşan bir sinerji göstermedi. Daha geniş LoRA kapsamı otomatik olarak daha iyi değildir.

### Genel-domain maliyet

A7 Phone sonucunu iyileştirirken CV Scripted tarafında A0/A2’ye göre maliyet üretti. Sonuç “tek model her yerde daha iyi” değildir.

## Analiz ve yazılım hataları

### A5–A6 self-comparison bugı

`analyze_a6_v2_results.py` içindeki string replacement, A5 referans yolunu da A6 yoluna çevirdi. Böylece A6 yanlışlıkla kendisiyle karşılaştırıldı ve sahte `CI=0` sonucu üretildi.

Düzeltme sonrasında:

- 4.059 prediction farklı bulundu,
- 27/28 hedefte aggregate metric farklıydı,
- eski sonuç `SUPERSEDED_DUE_TO_REFERENCE_PATH_BUG` olarak işaretlendi.

### Stale state ve PID telemetrisi

Bazı worker süreçleri kapanmasına rağmen state dosyaları `RUNNING` kaldı. Süreç durumu; PID, CPU/GPU kullanımı, progress dosyası ve checkpoint artefaktları birlikte kontrol edilmeden yorumlanmamalıdır.

### Terminal penceresinin kapatılması

A7 worker’ın bağlı olduğu boş terminal penceresi kullanıcı tarafından kapatıldı ve eğitim kesildi. Görünmeyen arka plan süreci ve dosyaya yönlendirilmiş log kullanımı sonraki denemelerde tercih edildi.

### Resume schedule–weight mismatch

Bir resume denemesinde step-150 adapterı kullanılırken schedule step-170’ten devam ettirildi. Böylece ağırlıklarda olmayan 20 optimizer step atlanmış olacaktı. Deneme durduruldu ve doğru konum step-150/index-2400 olarak düzeltildi.

### Stale step-200 çakışması

Önceden kalmış step-200 klasörü, doğru resume koşusunun final checkpoint yazmasını engelledi. Final continuation izole bir run dizininde tamamlandı.

### Adapter dizininin dosya gibi hashlenmesi

Resume adapter klasörü `Path.read_bytes()` ile hashlenmeye çalışıldı ve `PermissionError` oluştu. Hash, gerçek `adapter_model.safetensors` dosyasına bağlandı.

## Augmentasyon policy gelişimi

### V1

Noise/gain policy clipping üretti.

### V2

0/−3/−6 dB noise policy noise kovalarında geçti; ancak phone-band resampling overshoot bulundu.

### V3

Universal peak guard yalnız augmented bucketlara uygulandı. Exhaustive audit 1.493/1.493 occurrence üzerinde geçti.

## Bilimsel ders

Bir deney yalnız son WER tablosundan ibaret değildir. Yanlış path, stale state, yarım checkpoint veya hatalı resume, ikna edici fakat geçersiz sonuç üretebilir. Bu nedenle prediction artefaktı, checkpoint provenance ve bağımsız metric recomputation birlikte korunmalıdır.
