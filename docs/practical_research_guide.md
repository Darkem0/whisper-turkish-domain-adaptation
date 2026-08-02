# Pratik Araştırma Rehberi: Ne İşe Yaradı, Ne İşe Yaramadı, Neden?

Bu belge, Türkçe `whisper-large-v3-turbo` uyarlama çalışmasının **Legacy deneylerini**, kontrollü **A0–A7 serisini**, inference/memory denemelerini, veri kalite auditlerini ve çalışma sırasında ortaya çıkan operasyonel hataları tek bir rehberde toplar.

Amaç yalnız sonuç tablosu sunmak değildir. Amaç, benzer bir Türkçe telefon/karşılıklı konuşma ASR araştırmasını yeniden yürütecek kişiye şu soruların cevabını vermektir:

- Hangi yöntem gerçekten fayda verdi?
- Hangi yöntem yalnız belirli bir domain için faydalıydı?
- Hangi yöntem başarısız oldu?
- Başarısızlığın olası nedeni neydi?
- Sonucun geçerli olduğundan nasıl emin olunur?
- Aynı hatalar nasıl önlenir?
- Bir sonraki araştırma hangi sırayla yürütülmelidir?

---

## 1. En önemli sonuç

Bu çalışmanın ana sonucu “tek bir Whisper adapterı her yerde daha iyi oldu” değildir.

Daha doğru sonuç şudur:

> Türkçe telefon ve karşılıklı konuşma başarısı; LoRA kapsamı, veri dağılımı, staged adaptation, telefon-benzeri augmentasyon, decoding ve değerlendirme panelinin birlikte tasarlanmasına bağlıdır. Hedef-domain iyileşmesi, temiz/genel Türkçe domainlerinde negatif transfer oluşturabilir.

Kontrollü seride en iyi Phone sonucu:

- **A7 step-200 normalized WER:** `0.154285`

A7’nin kendi en iyi robustness sonucu:

- **A7 step-150 normalized WER:** `0.147578`

Ancak A4 robustness tarafında yaklaşık `0.1441` ile güçlü bir Pareto adayı olarak kalmıştır. Bu nedenle tek bir birleşik skorla “mutlak kazanan” seçmek doğru değildir.

---

## 2. İki ayrı deney dönemini karıştırmama kuralı

### 2.1. Legacy seri

Legacy seri, ilk geniş araştırma dönemidir. Veri oranı, balanced-phone continuation, telefon augmentasyonu, VAD/segmentasyon ve repeat-safe decoding gibi fikirlerin ilk kez görüldüğü dönemdir.

Legacy isimleri:

- `Legacy-H0`: Base Whisper
- `Legacy-H1`: MediaSpeech-only LoRA
- `Legacy-H2`: General Turkish LoRA
- `Legacy-H3`: Balanced-phone continuation
- `Legacy-H4`: Repeat-safe decode

### 2.2. Kontrollü A0–A7 serisi

Yeni seri, aynı frozen evaluation protokolü, sabit LoRA ayarları, prediction artefaktları ve hashlerle yürütülen kontrollü karşılaştırmadır.

- `A0`: base model
- `A2`: encoder+decoder Q/V
- `A3`: encoder-only + replay
- `A4`: decoder-only
- `A5`: encoder-only, temiz schedule
- `A6`: encoder+decoder, temiz schedule
- `A7`: A2 parent üzerinden staged source-anchored balanced-phone continuation

Legacy metrikleri yeni seriyle doğrudan tek tabloda kıyaslanmamalıdır. Veri, evaluation seti ve inference hattı farklıdır.

---

## 3. Hızlı karar tablosu

| Yöntem | Sonuç | Karar | Neden/yorum |
|---|---|---|---|
| MediaSpeech-only LoRA | Aynı domain ölçümünde dahi kötüleşme | Başarısız negatif kontrol | Veri çeşitliliği yetersiz, schedule/domain dengesi zayıf, güçlü base model kolayca bozulabiliyor |
| Common Voice ağırlıklı genel LoRA | Common Voice iyileşti, MediaSpeech kötüleşti | Domain-bağımlı | Model baskın veri dağılımına uydu; “genel Türkçe” etiketi konuşma tarzı çeşitliliğini garanti etmedi |
| Balanced-phone continuation | Eğitim dağılımına yakın testte güçlü iyileşme | Başarılı fakat genelleme maliyetli | Veri dengesi ve staged adaptation hedef-domain lehine çalıştı |
| Repeat-safe decode | Uzun çağrıda tekrar döngüsünü ciddi azalttı | Başarılı tarihsel bulgu | Decode hatası model kazanımını silebiliyor |
| Encoder+decoder Q/V LoRA (A2) | Phone/robustness iyileşti; FLEURS geriledi | Başarılı domain adayı | Hedef-domain kazanımı ile genel-domain maliyet birlikte oluştu |
| Encoder-only + %10 replay (A3) | Robustness iyileşti, CV Scripted ciddi kötüleşti | Sınırlı/negatif transferli | Replay oranı veya içeriği forgetting’i önlemeye yetmedi |
| Decoder-only (A4) | Güçlü Phone ve en iyi robustness adaylarından biri | Başarılı Pareto adayı | Dilsel/çıktı tarafı adaptasyonu telefon hatalarını etkili biçimde düzeltti |
| Encoder-only temiz schedule (A5) | Phone iyileşti, A4 robustness geçilemedi | Sınırlı fayda | Akustik adaptasyon tek başına yeterli olmadı |
| Encoder+decoder temiz schedule (A6) | A5’ten farklı sonuç; ek sinerji kesin değil | Inconclusive | Daha geniş LoRA kapsamı otomatik sinerji üretmedi |
| Staged A7 | En iyi kontrollü Phone sonucu | Başarılı | Parent continuation + source anchor + telefon-benzeri schedule birlikte işe yaradı |
| A7 augmentasyonlarının bağımsız etkisi | İzole edilmedi | Inconclusive | Aynı deneyde parent, schedule, source dengesi ve çoklu augmentasyon birlikte değişti |
| %10 clean replay | CV Scripted korumasında yetersiz | Başarısız koruma | Replay varlığı tek başına yeterli değil; içerik/oran/katman kapsamı önemli |
| D3 decode profili | Desteklenen ve karşılaştırılabilir profil | Korundu | Evaluation standardizasyonu sağladı |
| MEM0 memory profili | Tahminleri değiştirmeyen güvenli profil | Korundu | Hız/bellek optimizasyonu kaliteyi değiştirmedi |
| MEM2 | İlk sıcak-cache microbenchmarkında yaklaşık %32,12; interleaved doğrulamada anlamlı kazanç yok | Microbenchmark olumlu, deployment belirsiz; canonical değil | Fixed-order/warm-up etkisi ayrıştırıldığında MEM0 karşısında promotion eşiği geçilmedi |
| MEM3/MEM4 | Batch’e göre prediction değişimi | Reddedildi | Kalite parity bozuldu; üretim güveni düşürdü |
| İkinci decode/retry | Tetiklenmedi veya bilgi kazancı üretmedi | Reddedildi | Karmaşıklık ekledi, ölçülebilir fayda göstermedi |
| Deterministic ITN | Güvenli dönüşüm bulunamadı | Reddedildi | Yanlış normalizasyon kritik sayı/tarih/tutar hatası oluşturabilir |
| N-best yaklaşımı | Gerçek bağımsız aday üretilemedi | Reddedildi | Yeniden sıralanacak anlamlı aday çeşitliliği yoktu |
| 0.75x speed perturbation | Tarihsel olarak olumlu; A7 entegrasyonunda kullanıldı | Faydalı aday, bağımsız nedensellik yok | A7’de tek başına ayrıştırılmadı |
| Phone-band/G.711 benzetimi | Telefon dayanıklılığına katkı adayı | Faydalı entegrasyon bileşeni | Fazla uygulanırsa temiz domaini bozabilir |

---

## 4. Legacy seride neler öğrenildi?

### 4.1. MediaSpeech-only LoRA neden başarısız oldu?

Legacy-H1 sonucunda MediaSpeech testinde normalize WER yaklaşık `0.1558 → 0.2162` kötüleşti. Normalize CER de `0.0916 → 0.1495` bozuldu.

Olası nedenler:

1. **Güçlü base modelin bozulması:** Whisper large-v3-turbo zaten iyi bir başlangıç modelidir. Küçük veya dengesiz fine-tuning kolayca catastrophic forgetting oluşturabilir.
2. **Veri hacmi tek başına yeterli değil:** Aynı dilde veri kullanmak, akustik ve dilsel çeşitliliği garanti etmez.
3. **Tek domain baskısı:** MediaSpeech’in konuşma tarzı, hedef telefon/karşılıklı konuşma koşullarının tamamını temsil etmez.
4. **Epoch ve LR hassasiyeti:** Uzun veya agresif eğitim mevcut genel yetenekleri bozabilir.
5. **Evaluation yakınlığı yanıltıcı olabilir:** Aynı isimli domain içinde bile train/test alt dağılımları farklı olabilir.

Pratik ders:

> İlk fine-tuning mutlaka base modele karşı küçük, frozen ve domain-ayrımlı evaluation ile ölçülmelidir. “Loss düştü” sonucu başarı değildir.

### 4.2. General Turkish LoRA neden yalnız Common Voice’ta iyi çalıştı?

Legacy-H2’de Common Voice normalized WER `0.1837 → 0.1368` iyileşirken MediaSpeech `0.1601 → 0.1718` kötüleşti.

Olası neden:

- Common Voice ağırlığı modelin okunmuş/temiz söyleyişe uyumunu artırdı.
- “Türkçe” ortaklığı, okuma konuşması ile serbest/medya/telefon konuşmasının aynı problem olduğu anlamına gelmez.
- Model veri miktarından çok veri dağılımına uydu.

Pratik ders:

> Veri setlerini yalnız dil etiketiyle değil, konuşma tarzı, kanal, spontaneite, gürültü ve utterance uzunluğuyla sınıflandır.

### 4.3. Balanced-phone continuation neden işe yaradı?

Legacy-H3, Common Voice ağırlığını azaltıp MediaSpeech etkisini artırdı; telefon bandı ve noise/gain augmentasyonu ekledi. Eğitim dağılımına yakın hızlı testte:

- Common Voice WER yaklaşık `0.1837 → 0.1241`
- MediaSpeech WER yaklaşık `0.1601 → 0.1366`

Bu sonuç, tek bir yöntemin değil aşağıdaki bileşimin faydalı olabileceğini gösterdi:

- genel adapterdan devam etmek,
- veri oranını hedef domaine yaklaştırmak,
- düşük learning rate kullanmak,
- telefon benzetimi eklemek,
- eğitimi aşamalı yürütmek.

Ancak dış doğrulamada balanced-phone model baseline’dan kötüydü. Bu nedenle yöntem “genel Türkçe iyileştirme” değil, **domain adaptation** olarak yorumlanmalıdır.

### 4.4. Repeat-safe decode neden bu kadar etkiliydi?

Uzun telefon örneğinde tekrar döngüsü oluşmuştu. Repeat-safe decoding ile normalize WER yaklaşık `0.8469 → 0.6466` iyileşti.

Kullanılan tarihsel profil:

- `no_repeat_ngram_size = 4`
- `repetition_penalty = 1.08`
- `chunk_s = 25`

Olası neden:

- Uzun seslerde decoder kendi çıktısına kilitlenebilir.
- Hatalı segment/chunk sınırları tekrar üretimini besleyebilir.
- Fine-tuned model iyi olsa bile decode ayarı sonucu bozabilir.

Sınırlama:

- Repeat suppression meşru tekrarları da silebilir.
- Bu nedenle temiz kısa benchmarklarda varsayılan olarak uygulanmamalı; uzun çağrı koşulu olarak ayrı test edilmelidir.

---

## 5. Kontrollü seride hangi modelleme yöntemleri işe yaradı?

## 5.1. A0: Base modelin önemi

A0 yalnız başlangıç değildir; güçlü bir güvenlik referansıdır.

A0 örnek sonuçları:

- Clean: `0.16255`
- Phone: `0.17568`
- G.711: `0.14574`
- Robustness: `0.16163`
- CV Scripted: `0.15560`
- FLEURS: `0.10288`

Ders:

> Fine-tuned model hedef domaine birkaç puan kazandırırken genel domaini ciddi bozuyorsa, base model hâlâ routing/fallback adayıdır.

## 5.2. A2: Encoder+decoder Q/V LoRA

A2:

- Clean: `0.13823`
- Phone: `0.17082`
- G.711: `0.13893`
- Robustness: `0.14655`
- CV Scripted: `0.15369`
- FLEURS: `0.17693`

İşe yarayan taraf:

- Clean, Phone, G.711 ve robustness iyileşti.

İşe yaramayan taraf:

- FLEURS ciddi geriledi.

Yorum:

- Encoder+decoder adaptasyonu hedef domain için güçlü bir başlangıç parentı olabilir.
- Ancak birleşik scope genel genellemeyi otomatik korumaz.
- A7’nin A2’den başlaması, A2’nin yalnız “başarısız genel model” değil, iyi bir staged parent olduğunu gösterdi.

## 5.3. A3: Encoder-only + replay

A3 step-50:

- Clean: `0.142539`
- Phone: `0.157342`
- G.711: `0.147126`
- CV Scripted: `0.235323`
- FLEURS: `0.070047`

Robustness kazancı istatistiksel olarak desteklendi; fakat CV Scripted ağır geriledi.

Neden replay işe yaramamış olabilir?

1. `%10` oran yetersiz olabilir.
2. Replay örnekleri hedef forgetting alanını temsil etmiyor olabilir.
3. Encoder-only scope akustik temsili hedef domaine fazla çekmiş olabilir.
4. Replay schedule içinde doğru zamanlarda veya yeterli çeşitlilikte yer almamış olabilir.
5. Genel-domain korunumu tek metrikle ölçülmüş olabilir; domain çeşitliliği yetersiz kalmış olabilir.

Ders:

> Replay bir checkbox değildir. Kaynağı, oranı, dağılımı, schedule konumu ve hangi forgetting türünü koruduğu önceden tanımlanmalıdır.

## 5.4. A4: Decoder-only neden güçlüydü?

A4:

- En iyi Phone: step-050, yaklaşık `0.158385`
- En iyi robustness: step-200, yaklaşık `0.1441`

Önemli gözlem:

- Erken checkpoint Phone için,
- geç checkpoint robustness için daha iyi oldu.

Bu, checkpoint seçiminin tek validation loss üzerinden yapılmaması gerektiğini gösterir.

Decoder-only yaklaşımın olası avantajları:

- Türkçe çıktı kalıpları ve telefon koşullarında sık hata yapılan kelime dizileri doğrudan decoder tarafında adapte olmuş olabilir.
- Akustik encoderı daha az bozduğu için bazı genel yetenekler korunmuş olabilir.
- Daha az trainable parametreyle daha stabil optimizasyon sağlamış olabilir.

Sınırlama:

- A4 schedule’ında 52 boş-hedef exposure vardı.
- Audit bunun geniş sonuçları açıklamak için çok seyrek olduğunu gösterdi; yine de A4 ile sonraki temiz schedule deneyleri birebir matched değildir.

## 5.5. A5: Encoder-only temiz schedule

A5:

- En iyi Phone: yaklaşık `0.1580`
- En iyi robustness: yaklaşık `0.1475`

Sonuç:

- Encoder-only yaklaşım Phone’u iyileştirdi.
- A4 robustness seviyesini geçemedi.

Olası yorum:

- Telefon hatalarının tamamı akustik değildir.
- Decoderın dilsel/sekans tarafı bazı kritik hatalarda daha önemli olabilir.
- Encoder adaptasyonu tek başına hedef domainin sözcük dizisi ve tekrar davranışını çözemeyebilir.

## 5.6. A6: Encoder+decoder temiz schedule

A6:

- En iyi Phone: `0.157203`
- En iyi robustness: yaklaşık `0.1448`

İlk analizde A5 ile tamamen aynı olduğu sanıldı. Bu sonuç yanlıştı; analiz scripti A5 yolunu da A6’ya çevirerek A6’yı kendisiyle karşılaştırmıştı.

Düzeltme sonrası:

- `4.059` prediction farklıydı.
- `27/28` targetta aggregate metric farklıydı.

Bilimsel sonuç:

- Decoder eklemek gerçekten predictionları değiştirdi.
- Ancak A4/A5 üzerinde açık ve büyük bir combination synergy kanıtlanmadı.

Ders:

> “CI=0” gibi aşırı temiz sonuçlar özellikle şüpheyle incelenmelidir. Prediction dosyaları satır bazında karşılaştırılmalı ve metrikler bağımsız yeniden hesaplanmalıdır.

## 5.7. A7: Staged domain adaptation neden en iyi Phone sonucunu verdi?

A7 bileşenleri:

- parent: A2 encoder+decoder Q/V adapter
- TSC: clean/read iddiası yapılmadan değiştirilmemiş source anchor
- phone-like kaynaklar: MediaSpeech + CV Spontaneous
- schedule: `3.200` occurrence
- TSC anchor: `1.067`
- phone-like: `2.133`
- augmentasyonlar:
  - phone-band,
  - speed `0.75`,
  - noise/gain,
  - phone-band + noise/gain
- düşük learning rate continuation

Sonuç:

- En iyi Phone: step-200 `0.154285`
- En iyi robustness: step-150 `0.147578`

Karşılaştırma:

- A2 Phone: `0.170825 → 0.154285`
- A4 Phone: `0.158385 → 0.154285`
- A6 Phone: `0.157203 → 0.154285`

Neden işe yaramış olabilir?

1. **Staged continuation:** Model sıfırdan domain adaptation yapmak yerine işe yarayan A2 temsilinden devam etti.
2. **Source anchor:** Bütün schedule telefonlaştırılmadı; değiştirilmemiş bir kaynak dağılımı korundu.
3. **Phone-like yoğunluk:** Hedef domain schedule içinde çoğunluk hâline getirildi.
4. **Çoklu akustik varyasyon:** Telefon bandı, yavaşlatma ve noise koşulları aynı modeli farklı bozulmalara hazırladı.
5. **Düşük LR:** Parent adapter yeteneklerini tamamen silmeden yeni domaine hareket etti.

Neden augmentasyon katkısı hâlâ “inconclusive”?

- Parent adapter değişti.
- Schedule dengesi değişti.
- Source anchor eklendi.
- Birden fazla augmentasyon aynı anda eklendi.

Dolayısıyla A7 **final entegrasyon sistemini** doğrular; tek bir augmentasyonun nedensel katkısını doğrulamaz.

---

## 6. Veri kalitesi hakkında öğrenilenler

Tam audit bulguları:

- Train: `172.238` civarı kayıt
- Validation: `9.081`
- 7 boş train transkripti
- 2 placeholder validation satırı
- Train duplicate transcript kümeleri: 717 / 1.795 satır
- Validation duplicate transcript kümeleri: 14 / 30 satır

Schedule exposure:

- A2: boş/duplicate/placeholder exposure `0/3200`
- A3: duplicate `40/3200`
- A4: empty `52/3200`, duplicate `28/3200`

Sonuç:

- Bu kusurlar gerçekti ve temizlenmeliydi.
- Ancak oranları, A2–A7 arasındaki geniş domain kazanç ve kayıplarını tek başına açıklayacak kadar büyük değildi.

Pratik ders:

1. Veri kusurunu bulunca bütün sonucu ona bağlama.
2. Kusurun schedule içinde gerçekten kaç kez tüketildiğini ölç.
3. Train manifesti ile schedule exposure’ı ayrı audit et.
4. Validation placeholderlarını “küçük oran” diye gizleme; fakat etkisini ölçmeden büyük neden ilan etme.
5. Orijinal immutable manifestleri koru; temizlenmiş yeni sürüm üret.

---

## 7. Augmentasyon rehberi

## 7.1. Phone-band

Kullanılan A7 policy:

1. band-pass `300–3400 Hz`
2. ara örnekleme `8 kHz`
3. model sample rate’ine dönüş
4. universal peak guard

Risk:

- Filtre ve resampling ringing/overshoot üretebilir.
- Giriş clipping yapmasa bile çıkış peak sınırını aşabilir.

## 7.2. Speed 0.75

- Konuşma hızı `0.75x`
- Transcript değişmez
- Effective duration güncellenir
- Resampling sonrası peak kontrol edilir

Olası fayda:

- Yavaş konuşma ve uzatılmış fonem varyasyonlarına dayanıklılık.

Sınırlama:

- A7’de bağımsız ablation yoktur.

## 7.3. Noise/gain

İlk policy:

- `-6, -3, +3, +6 dB`

Sorun:

- Pozitif gain clipping üretti.

Düzeltilmiş policy:

- `0, -3, -6 dB`
- SNR: `10, 15, 20 dB`

## 7.4. Universal peak guard

Yalnız augmented bucketlarda uygulanır:

- `phone_band`
- `speed_075`
- `noise_gain`
- `phone_band_noise_gain`

Unchanged bucketlarda uygulanmaz:

- `tsc_anchor_unchanged`
- `phone_like_unchanged`

Kural:

```text
observed_peak <= 0.98:
    waveform değişmez

observed_peak > 0.98:
    bütün waveform'a yalnız gerekli minimum negatif scalar attenuation uygulanır
```

Yasaklanan çözümler:

- hard clipping
- soft clipping
- limiter
- compressor
- her örneği zorunlu peak normalization

V3 audit:

- `1.493/1.493` augmented occurrence geçti
- max final peak `0.9800000191`
- noise SNR farkı `0.0 dB`
- tetiklenme:
  - phone_band 30
  - speed_075 7
  - noise_gain 6
  - combined 6

Ders:

> Augmentasyonun amacı yeni bozulma üretmektir; kontrolsüz dijital clipping gibi istenmeyen ikinci bir bozulma üretmek değildir.

---

## 8. Inference ve decoding tarafında kararlar

## 8.1. D3 decoding profili

Kontrollü seride desteklenen ortak decoding profilidir. Bütün checkpointler aynı decode ayarlarıyla kıyaslanmıştır.

Ders:

- Model kıyaslarken decode ayarlarını sabit tut.
- En iyi model ile en iyi decode ayarını aynı anda değiştirirsen nedensellik kaybolur.

## 8.2. Repeat-safe decoding

Legacy uzun çağrıda faydalı oldu.

Kullanım alanı:

- uzun ses,
- tekrar döngüsü,
- hallucination riski.

Kullanılmaması gereken durum:

- kısa temiz benchmarklarda otomatik varsayılan,
- meşru tekrarların önemli olduğu transkriptler.

## 8.3. VAD/segmentasyon

Legacy çalışmada uzun çağrı için büyük fark üretmişti. Ancak kontrollü A0–A7 LoRA scope serisinde segmentasyon ayrı tutuldu ve varsayılan deney değişkeni yapılmadı.

Ders:

- VAD/segmentasyonu model eğitiminden ayrı deney olarak tut.
- Aynı anda hem model hem segmentation değiştirerek tek WER sonucu raporlama.

## 8.4. N-best, ITN ve ikinci decode neden bırakıldı?

### N-best

Gerçek bağımsız aday çeşitliliği yoksa yeniden sıralama yalnız görünüşte karmaşık bir sistem üretir.

### Deterministic ITN

Türkçe sayı, tarih, para ve kısaltma dönüşümleri güvenli biçimde çözülemediğinde yanlış “düzeltme” ham ASR hatasından daha tehlikeli olabilir.

### İkinci decode/retry

Tetiklenmeyen veya ölçülebilir bilgi kazancı üretmeyen retry hattı bakım maliyeti yaratır.

---

## 9. Memory ve throughput deneylerinden çıkan dersler

### MEM0

- Tahmin parity’sini koruyan güvenli profil.
- Üretim ve frozen evaluation için referans olarak tutuldu.

### MEM2

- İlk sabit sıralı/sıcak-cache microbenchmarkında prediction parity korunarak yaklaşık `%32,12` hızlanma görüldü.
- Sonraki interleaved cold/warm doğrulama fixed-order ve warm-up etkisini ayırdı; promotion için anlamlı hız kazancı göstermedi.
- Bu nedenle sınıfı `microbenchmark_positive / deployment_inconclusive / not_canonical`dır; doğrudan başarısız sayılmaz, fakat MEM0’ın yerini almaz.

### MEM3/MEM4

- Batch boyutuna göre prediction değişti.
- Hız kazancı olsa bile kalite determinismi bozulduğu için reddedildi.

### P7

- Terminal karar: `PASSED_NO_MEANINGFUL_SPEEDUP`

Ders:

> Hız optimizasyonu yalnız throughput ile değerlendirilmez. Prediction parity, determinism, VRAM, bakım maliyeti ve hata ayıklama zorluğu birlikte değerlendirilmelidir.

---

## 10. Telefon başarısı neden genel Türkçe başarısıyla aynı değil?

Temiz benchmarklar genellikle şunları ölçer:

- düzgün cümle,
- tek konuşmacı,
- net kanal,
- sınırlı kesinti,
- daha düzenli dilbilgisi.

Telefon/karşılıklı konuşma ise şunları içerir:

- “evet”, “hayır”, “tamam” gibi kısa kritik cevaplar,
- hızlı turn-taking,
- yarım kelimeler,
- birbirinin sözünü kesme,
- düşük bant genişliği,
- crosstalk,
- sayı/tutar/tarih,
- özel isim,
- tekrar ve hallucination,
- segment başı/sonu silinmesi.

Bu nedenle iki panel korunmalıdır.

### Telefon/konuşma paneli

- MediaSpeech Phone
- MediaSpeech G.711
- robustness proxy
- CV Spontaneous
- deletion/insertion/substitution
- kısa utterance doğruluğu
- sayı/tarih/tutar/isim hataları, annotation varsa
- tekrar/hallucination

### Genel-domain izleme paneli

- MediaSpeech Clean
- CV Scripted
- FLEURS
- TSC

Karar kuralı:

> Hedef ürün telefon konuşmasıysa genel-domain regresyonu raporla; fakat otomatik hard gate yapma. Buna karşılık kritik operasyonel hata artışı hard gate olabilir.

---

## 11. Araştırma ve yazılım hatalarından çıkarılan operasyonel rehber

## 11.1. Path replacement ile deney yolu türetme

Hata:

- A5 referans yolu string replacement ile A6’ya dönüştü.
- A6 kendisiyle karşılaştırıldı.

Doğru yöntem:

- Her deney yolu explicit config alanı olsun.
- Dosya pathleri programatik string replacement ile üretilmesin.
- Compare scripti iki kaynağın SHA/path bilgisini rapor başına yazsın.

## 11.2. State dosyasına tek başına güvenme

Hata:

- Worker kapandıktan sonra state `RUNNING` kaldı.

Doğru sağlık kontrolü:

1. Gerçek PID ve child process
2. CPU delta
3. GPU utilization ve VRAM
4. Progress dosyasının son yazılma zamanı
5. Checkpoint oluşumu
6. stderr traceback

## 11.3. Debug stop’un full moda sızması

Doğru yöntem:

- Debug stop yalnız explicit `--stop-after-first-backward` flagiyle çalışsın.
- Full mod, hedef step tamamlanmadan exit code 0 dönmesin.
- İlk forward/backward sentinel logları olsun.

## 11.4. Terminal penceresinin kapatılması

Hata:

- Boş görünen terminal kapatıldı; worker da sonlandı.

Doğru yöntem:

- Görünmeyen arka plan process
- stdout/stderr dosyaya redirect
- PID dosyası
- Process tree kontrolü
- Kullanıcıya hangi pencerenin kapatılmaması gerektiğini açıkça söyleme

## 11.5. Resume schedule–weight mismatch

Hata:

- step-150 ağırlıklarıyla schedule step-170’ten devam ettirildi.

Sonuç:

- Ağırlıklarda olmayan 20 optimizer step atlanacaktı.

Doğru yöntem:

- Checkpoint stepi ile schedule indexi çift olarak saklanmalı.
- `optimizer_step=150` için `schedule_index=2400` kullanılmalı.
- Exact optimizer state yoksa resume türü açıkça `ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET` olmalı.

## 11.6. Checkpoint klasörü çakışması

Hata:

- Eski `step-200` klasörü final save’i engelledi.

Doğru yöntem:

- Yeni continuation run dizini
- Geçici dizine yazma
- Dosya doğrulama
- Atomik rename
- Stale checkpointi silmeden arşivleme

## 11.7. Klasörü dosya gibi hashlemek

Hata:

- `adapter/` dizini `read_bytes()` ile hashlenmeye çalışıldı.

Doğru yöntem:

- `adapter_model.safetensors` veya `adapter_model.bin` explicit çözülür.
- Config ayrı hashlenir.
- Birden fazla belirsiz model dosyası varsa açık hata üretilir.

## 11.8. Progress yazımı

Doğru yöntem:

- Her optimizer step sonunda JSONL satırı
- flush/fsync
- step, schedule index, loss, source, augmentation bucket
- resume metadata
- checkpoint bağımsız progress

---

## 12. Önerilen deney yürütme sırası

### Aşama 1 — Problem tanımı

- Hedef domaini açık tanımla.
- “Türkçe ASR” gibi geniş hedef kullanma.
- Telefon, toplantı, okuma, medya veya kısa komut koşulunu ayır.

### Aşama 2 — Frozen evaluation

En az iki panel kur:

- hedef-domain paneli
- genel-domain izleme paneli

Normalization ve sample ID sırası sabitlenmeden training başlatma.

### Aşama 3 — A0 baseline

- Aynı inference hattı
- Aynı decode
- Aynı memory profili
- Prediction JSONL
- Raw/normalized WER/CER

### Aşama 4 — Küçük ablationlar

Önerilen sıra:

1. decoder-only
2. encoder-only
3. encoder+decoder
4. replay/anchor
5. staged continuation

Her turda tek ana değişken değişsin.

### Aşama 5 — Prediction-level analiz

- Sadece aggregate WER’e bakma.
- Kaç prediction değişti?
- Hangi hata türleri düzeldi?
- Deletion mı insertion mı?
- Kısa cevaplar nasıl?

### Aşama 6 — Final entegrasyon

Ancak ablationlardan sonra:

- en iyi parent
- kaynak dengesi
- telefon augmentasyonu
- güvenli decode

birleştirilmelidir.

### Aşama 7 — Durdurma kuralı

Yeni deney yalnız şu koşullarda yapılmalı:

- açık bir bilimsel belirsizliği çözüyor,
- önceki deneylerden ayrıştırılabilir,
- beklenen bilgi kazancı yüksek,
- evaluation bunu ölçebiliyor.

“Başka bir yöntem daha var” tek başına deney gerekçesi değildir.

---

## 13. Yeni bir projede kullanılabilecek pratik reçete

### Güvenli başlangıç

```text
Base Whisper
→ frozen target/general evaluation
→ decoder-only LoRA
→ encoder-only LoRA
→ encoder+decoder LoRA
→ matched comparison
→ staged domain continuation
→ final Pareto selection
```

### Eğitim tarafı

- Base weights frozen
- LoRA rank/alpha/dropout sabit
- Batch ve grad accumulation sabit
- Seed sabit
- Schedule JSONL
- Her checkpointte local validation
- Her checkpoint frozen evaluation adayı

### Değerlendirme tarafı

- Tek WER yerine dataset bazlı tablo
- Raw + normalized WER/CER
- Paired bootstrap
- Prediction hash
- Critical error kategorileri

### Operasyon tarafı

- Tek GPU worker
- Hidden background process
- PID/state/progress/stderr
- Atomic checkpoint
- Resume provenance
- Bağımsız metric recomputation

---

## 14. Yayına hazırlarken neler açıkça yazılmalı?

Mutlaka açıklanmalı:

- Hangi veri açık ve lisanslı?
- Hangi sonuç proxy?
- Gerçek çağrı merkezi verisi kullanılmadı mı?
- Hangi checkpoint authoritative?
- Resume exact mı, optimizer-reset mi?
- Hangi negatif sonuçlar oluştu?
- Hangi analiz hatası düzeltildi?
- Hangi yöntem bağımsız nedensel olarak ölçülmedi?

Kaçınılması gereken ifadeler:

- “Türkçe Whisper genel olarak iyileştirildi.”
- “A7 bütün domainlerde en iyi.”
- “Telefon augmentasyonu kesin olarak X puan kazandırdı.”
- “Proxy sonuç gerçek çağrı merkezi performansını kanıtlar.”

Kullanılması gereken ifade:

> Kontrollü açık-veri proxy değerlendirmesinde staged domain adaptation Phone WER’i iyileştirdi; genel-domain maliyet oluştu ve augmentasyonun bağımsız katkısı ayrıştırılamadı.

---

## 15. Nihai yöntem sınıflandırması

### Başarılı

- Staged domain adaptation
- A2’nin parent olarak kullanılması
- Decoder-only güçlü Pareto yaklaşımı
- Hedef-domain ağırlıklı schedule
- Source anchor yaklaşımı
- D3 + MEM0 standardizasyonu
- Repeat-safe decode, uzun çağrı özelinde
- Prediction-level audit
- Independent metric recomputation
- Universal augmented-output peak guard

### Sınırlı veya domain-bağımlı

- Encoder-only
- Encoder+decoder joint training
- General Turkish LoRA
- 0.75x speed perturbation
- phone-band/noise augmentasyonu
- clean replay

### Başarısız veya reddedilen

- MediaSpeech-only LoRA
- `%10` replay ile genel-domain koruma iddiası
- MEM2 hız optimizasyonu
- MEM3/MEM4 prediction-changing profiller
- güvenli olmayan deterministic ITN
- gerçek aday üretmeyen N-best
- bilgi kazancı üretmeyen ikinci decode
- path replacement tabanlı analiz
- state dosyasına tek başına güvenme
- schedule ve checkpointi ayrı ayrı resume etme

### Bilimsel olarak açık kalanlar

- Hangi A7 augmentasyonu ne kadar katkı verdi?
- Source anchor oranının optimum değeri nedir?
- Gerçek çift konuşmacılı çağrı verisinde model sıralaması değişir mi?
- Sayı/tutar/tarih/isim hatalarında hangi model en iyidir?
- A4 robustness üstünlüğü gerçek çağrı koşullarında korunur mu?

---

## 16. Son karar

Açık-veri deney hattı tamamlanmıştır:

`OPEN_DATA_EXPERIMENT_LINE_COMPLETED`

Yeni açık-veri LoRA deneyi yerine en yüksek değerli sonraki çalışma:

- insan doğrulanmış hedef-domain evaluation,
- konuşmacı/kanal bazlı hata analizi,
- sayı/tutar/tarih/isim ölçümü,
- A0/A4/A7 Pareto karşılaştırmasıdır.

Bu belge, yeni deney üretmek için değil; mevcut kanıtı doğru kullanmak, tekrarlanan hataları önlemek ve benzer ASR çalışmalarını daha kısa yoldan güvenilir biçimde yürütmek için hazırlanmıştır.
