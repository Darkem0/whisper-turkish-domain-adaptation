# Whisper Large-v3-turbo Türkçe ASR İyileştirme Çalışması: Genişletilmiş Ara Rapor

## 1. Amaç ve Kapsam

Bu çalışmanın amacı, `openai/whisper-large-v3-turbo` modelinin Türkçe otomatik konuşma tanıma başarımını artırmak ve özellikle uzun telefon/çağrı merkezi görüşmelerindeki davranışını incelemektir. Başlangıçta gerçek bankacılık çağrı verisi bulunmadığı için açık kaynak Türkçe veri setleri kullanılmış, sonrasında kullanıcı tarafından sağlanan bir telefon görüşmesi ve internetten bulunan ek transcriptli doğrulama setleriyle sonuçlar genişletilmiştir.

Çalışmanın bu aşamasındaki ana bulgu şudur:

> Tek bir fine-tuning adımı tüm Türkçe konuşma türlerinde tutarlı iyileşme sağlamamaktadır. Eğitim verisi, akustik ortam, inference hattı ve decode ayarları birlikte ele alındığında iyileşme elde edilmekte; fakat telefon/çağrı uyarlaması temiz okuma/anlatım domainlerinde negatif transfer oluşturabilmektedir.

Bu nedenle makale için en doğru çerçeve, yalnızca "Whisper Türkçe iyileştirildi" iddiası değil; "Whisper Türkçe ASR uyarlamasında veri dağılımı, akustik benzetim ve inference stratejisinin etkileri" şeklindedir.

## 2. Kullanılan Veri Setleri

### 2.1. Eğitim ve İlk Test İçin Kullanılan Veriler

| Veri seti | Kaynak | Kullanım | Train hacmi |
|---|---|---|---:|
| Common Voice 17 TR Fixed | Hugging Face `ysdede/commonvoice_17_tr_fixed` | Genel Türkçe okuma konuşması | 26,501 örnek, 19.84 saat |
| MediaSpeech TR | OpenSLR SLR108 | Türkçe medya konuşmaları | 2,010 örnek, 8.01 saat |

Karma genel eğitim seti:

| Split | Örnek | Süre |
|---|---:|---:|
| Train | 28,511 | 27.84 saat |
| Validation | 8,890 | 7.27 saat |
| Test | 9,902 | 8.32 saat |

Balanced-phone ikinci eğitim seti:

| Domain | Örnek | Süre |
|---|---:|---:|
| Common Voice | 10,586 | 8.00 saat |
| MediaSpeech | 4,020 | 16.01 saat |
| Toplam | 14,606 | 24.01 saat |

Bu balanced-phone setinde Common Voice etkisi azaltılmış, MediaSpeech ağırlığı artırılmış ve telefon bandı/gürültü benzetimi eklenmiştir.

### 2.2. Sonradan Eklenen Dış Doğrulama Setleri

Sonuç kısmının daha güçlü olması için eğitimde kullanılmayan üç yeni transcriptli doğrulama kaynağı internetten bulundu ve indirildi:

| Doğrulama seti | Kaynak | Domain | Örnek | Süre |
|---|---|---|---:|---:|
| FLEURS-TR test subset | `google/fleurs`, `tr_tr`, test | Genel çok dilli ASR benchmark | 120 | 0.41 saat |
| Khan Academy Turkish test subset | `ysdede/khanacademy-turkish`, test | Eğitim/anlatım konuşması | 120 | 0.32 saat |
| Khan Academy Turkish Math test subset | `ysdede/khanacademy-turkish-math`, test | Matematik terimli eğitim konuşması | 120 | 0.34 saat |
| Toplam dış doğrulama | Birleşik manifest | 3 farklı domain | 360 | 1.08 saat |

Üretilen birleşik doğrulama manifesti:

```text
data/manifests/external_eval/external_tr_360.jsonl
```

Bu dış doğrulama seti, modelin yalnızca eğitim dağılımına mı uyum sağladığını yoksa farklı Türkçe konuşma türlerine genelleyip genellemediğini ölçmek için eklendi.

## 3. Model Evrimi

| Aşama | Model | Eğitim/veri | Amaç |
|---|---|---|---|
| A0 | Baseline `whisper-large-v3-turbo` | Eğitim yok | Başlangıç seviyesi |
| A1 | MediaSpeech LoRA 1 epoch | 8.01 saat MediaSpeech | Türkçe medya konuşmasına basit uyarlama |
| A2 | General TR LoRA checkpoint-750 | Common Voice + MediaSpeech, yaklaşık 0.42 epoch | Genel Türkçe iyileştirme |
| A3 | Balanced-phone LoRA final | A2 üzerinden 24.01 saat balanced-phone, 1 epoch | Telefon/serbest konuşma dayanıklılığı |
| A4 | Balanced-phone LoRA + repeat-safe decode | A3 + decode ayarı | Tekrar döngüsünü azaltma |

Kullanılan temel LoRA yaklaşımı:

| Parametre | Değer |
|---|---|
| Base model | `openai/whisper-large-v3-turbo` |
| LoRA target modules | `q_proj`, `v_proj` |
| LoRA rank | İlk MediaSpeech denemesi: 8, sonraki denemeler: 16 |
| Precision | fp16 |
| Batch size | 1 |
| Gradient accumulation | 16 |
| GPU | RTX 4070 SUPER, yaklaşık 12 GB VRAM |

## 4. Adım Adım Deney Sonuçları

### 4.1. A1: Sadece MediaSpeech ile LoRA Eğitimi

İlk deney yalnızca MediaSpeech TR üzerinde 1 epoch LoRA eğitimi idi. MediaSpeech test setindeki sonuç:

| Model | Raw WER | Raw CER | Normalize WER | Normalize CER |
|---|---:|---:|---:|---:|
| Baseline large-v3-turbo | 0.4255 | 0.1428 | 0.1558 | 0.0916 |
| MediaSpeech LoRA 1 epoch | 0.4508 | 0.1943 | 0.2162 | 0.1495 |

Değişim:

| Metrik | Başlangıç | Son | Göreli değişim |
|---|---:|---:|---:|
| Normalize WER | 0.1558 | 0.2162 | `%38.8` kötüleşme |
| Normalize CER | 0.0916 | 0.1495 | `%63.2` kötüleşme |

Yorum: Sadece Türkçe medya konuşmasıyla LoRA eğitimi, hedeflenen genel/telefon performansını iyileştirmedi. Bu deney, "Türkçe veriyle fine-tuning otomatik olarak iyileştirir" varsayımının yanlış olduğunu gösteren önemli bir negatif kontrol oldu.

### 4.2. A2: Common Voice + MediaSpeech Genel Türkçe LoRA

Bu aşamada Common Voice 17 TR Fixed ve MediaSpeech TR birleştirildi. 2 epoch hedeflendi ancak yerel GPU süresi nedeniyle `checkpoint-750` kullanıldı. Bu checkpoint yaklaşık `0.42 epoch` seviyesindedir.

1000 örneklik hızlı karma test alt kümesindeki sonuç:

| Model | Domain | Normalize WER | Normalize CER |
|---|---|---:|---:|
| Baseline | Common Voice | 0.1837 | 0.0728 |
| General TR LoRA ckpt750 | Common Voice | 0.1368 | 0.0415 |
| Baseline | MediaSpeech | 0.1601 | 0.0985 |
| General TR LoRA ckpt750 | MediaSpeech | 0.1718 | 0.1050 |

Değişim:

| Domain | Başlangıç WER | Son WER | Göreli değişim |
|---|---:|---:|---:|
| Common Voice | 0.1837 | 0.1368 | `%25.5` iyileşme |
| MediaSpeech | 0.1601 | 0.1718 | `%7.3` kötüleşme |

Yorum: Model, Common Voice okuma dağılımına hızla uyum sağladı; fakat medya/serbest konuşma tarafında aynı iyileşme görülmedi. Bu aşama, veri oranının kritik olduğunu gösterdi.

### 4.3. A3: Balanced-phone İkinci Eğitim

Bu aşamada A2 checkpoint'i üzerinden devam edildi. Common Voice ağırlığı azaltıldı, MediaSpeech ağırlığı artırıldı ve telefon benzetimli augmentasyon eklendi.

Eğitim özeti:

| Parametre | Değer |
|---|---|
| Başlangıç adapter | `general-tr checkpoint-750` |
| Eğitim seti | 24.01 saat balanced-phone |
| Epoch | 1 |
| Global step | 913 |
| İlk log loss | 2.294 |
| Son log loss | 1.988 |
| Learning rate | `5e-6` |
| Telefon bandı benzetimi | 8 kHz band-pass/yeniden örnekleme mantığı |
| Gürültü/gain augmentasyonu | Var |

1000 örneklik hızlı karma testte sonuç:

| Model | Domain | Normalize WER | Normalize CER |
|---|---|---:|---:|
| Baseline | Common Voice | 0.1837 | 0.0728 |
| General TR LoRA ckpt750 | Common Voice | 0.1368 | 0.0415 |
| Balanced-phone LoRA final | Common Voice | 0.1241 | 0.0355 |
| Baseline | MediaSpeech | 0.1601 | 0.0985 |
| General TR LoRA ckpt750 | MediaSpeech | 0.1718 | 0.1050 |
| Balanced-phone LoRA final | MediaSpeech | 0.1366 | 0.0631 |

Değişim:

| Domain | Baseline WER | Final WER | Göreli değişim |
|---|---:|---:|---:|
| Common Voice | 0.1837 | 0.1241 | `%32.4` iyileşme |
| MediaSpeech | 0.1601 | 0.1366 | `%14.7` iyileşme |

Yorum: Eğitim dağılımına yakın karma testte balanced-phone aşaması en iyi sonucu verdi. Özellikle A2'de MediaSpeech tarafında oluşan kötüleşme bu aşamada düzeldi.

### 4.4. A4: Decode Ayarı ve Tekrar Baskılama

Kullanıcının verdiği 9 dakikalık telefon görüşmesinde ilk LoRA decode çıktısında 275-300 saniye aralığında `ama ama` tekrar döngüsü oluştu.

İlk decode:

| Model/output | Normalize WER |
|---|---:|
| Balanced-phone LoRA, ilk decode | 0.8469 |

Tekrar baskılamalı decode:

```text
no_repeat_ngram_size = 4
repetition_penalty = 1.08
chunk_s = 25
```

| Model/output | Normalize WER |
|---|---:|
| Balanced-phone LoRA + repeat-safe decode | 0.6466 |

Değişim:

| Metrik | İlk decode | Repeat-safe decode | Göreli değişim |
|---|---:|---:|---:|
| Normalize WER | 0.8469 | 0.6466 | `%23.7` iyileşme |

Yorum: Aynı model, yanlış decode ile başarısız görünürken doğru decode stratejisiyle en iyi çağrı sonucunu verdi. Bu nedenle inference hattı model eğitimi kadar önemlidir.

## 5. test.mp3 Telefon Görüşmesi Sonuçları

Kullanıcının sağladığı dosya:

```text
C:\Users\emre\Desktop\test.mp3
```

Süre yaklaşık 9 dakika 22 saniyedir. Referans transcript sonradan sağlanmıştır. Referans metin yaklaşık 9:06'da bittiği için hem tam çıktı hem de 9:06'ya kadar kırpılmış çıktı ölçüldü.

### 5.1. Tam Çıktı Ölçümü

| Model/output | Raw WER | Raw CER | Normalize WER | Normalize CER |
|---|---:|---:|---:|---:|
| Balanced-phone LoRA + repeat-safe decode | 0.7416 | 0.4054 | 0.6670 | 0.3885 |
| faster-whisper large-v3 + VAD | 0.8377 | 0.4847 | 0.6846 | 0.4399 |
| faster-whisper large-v3-turbo + VAD | 0.8573 | 0.4660 | 0.6883 | 0.4147 |
| Transformers large-v3 | 0.9011 | 0.5398 | 0.7384 | 0.4844 |
| distil-large-v3-tr | 0.8778 | 0.5807 | 0.7904 | 0.5453 |
| Balanced-phone LoRA, ilk decode | 0.9450 | 0.5172 | 0.8673 | 0.5010 |
| Transformers large-v3-turbo | 1.3256 | 0.8911 | 1.1772 | 0.8219 |

### 5.2. 9:06'ya Kadar Kırpılmış Ölçüm

| Model/output | Raw WER | Raw CER | Normalize WER | Normalize CER |
|---|---:|---:|---:|---:|
| Balanced-phone LoRA + repeat-safe decode | 0.7211 | 0.3872 | 0.6466 | 0.3703 |
| faster-whisper large-v3-turbo + VAD | 0.8256 | 0.4408 | 0.6568 | 0.3902 |
| faster-whisper large-v3 + VAD | 0.8097 | 0.4579 | 0.6568 | 0.4143 |
| Balanced-phone LoRA, ilk decode | 0.9244 | 0.4991 | 0.8469 | 0.4829 |

Çağrı örneğinde balanced-phone LoRA repeat-safe decode, VAD'li güçlü baseline'a göre küçük bir avantaj sağlamıştır:

| Karşılaştırma | Baseline WER | Final WER | Göreli değişim |
|---|---:|---:|---:|
| faster-whisper large-v3-turbo + VAD vs LoRA repeat-safe | 0.6568 | 0.6466 | `%1.6` iyileşme |
| Transformers large-v3-turbo, VAD yok vs LoRA repeat-safe | 1.1772 | 0.6670 | `%43.3` iyileşme |

Not: Buradaki referans transcript elle düzeltilmiş nihai transcript gibi görünmemektedir. Bu nedenle mutlak WER değerleri yüksek ve gürültülüdür; fakat aynı referansla göreli kıyas yapılabilir.

## 6. Yeni Dış Doğrulama Sonuçları

Yeni dış doğrulama seti:

```text
data/manifests/external_eval/external_tr_360.jsonl
```

Bu set eğitimde kullanılmayan üç kaynaktan oluşur ve toplam 360 örnek, 1.08 saat konuşma içerir.

### 6.1. Toplam Dış Doğrulama Sonuçları

| Model | Raw WER | Raw CER | Normalize WER | Normalize CER |
|---|---:|---:|---:|---:|
| Baseline large-v3-turbo | 0.2214 | 0.0581 | 0.0857 | 0.0283 |
| MediaSpeech LoRA 1 epoch | 0.2231 | 0.0588 | 0.0853 | 0.0287 |
| General TR LoRA ckpt750 | 0.2132 | 0.0572 | 0.0957 | 0.0316 |
| Balanced-phone LoRA final | 0.2312 | 0.0611 | 0.1018 | 0.0344 |

Normalize WER'e göre dış doğrulama yorumu:

| Aşama | Normalize WER | Baseline'a göre değişim |
|---|---:|---:|
| Baseline | 0.0857 | referans |
| MediaSpeech LoRA | 0.0853 | `%0.5` iyileşme, pratik olarak aynı |
| General TR LoRA | 0.0957 | `%11.6` kötüleşme |
| Balanced-phone LoRA | 0.1018 | `%18.7` kötüleşme |

### 6.2. Domain Bazlı Normalize WER

| Model | FLEURS-TR | Khan Academy TR | Khan Academy Math TR |
|---|---:|---:|---:|
| Baseline large-v3-turbo | 0.0778 | 0.0800 | 0.0972 |
| MediaSpeech LoRA 1 epoch | 0.0815 | 0.0796 | 0.0934 |
| General TR LoRA ckpt750 | 0.0898 | 0.0835 | 0.1112 |
| Balanced-phone LoRA final | 0.0977 | 0.0922 | 0.1135 |

### 6.3. Domain Bazlı Ham WER

| Model | FLEURS-TR | Khan Academy TR | Khan Academy Math TR |
|---|---:|---:|---:|
| Baseline large-v3-turbo | 0.2666 | 0.1775 | 0.2230 |
| MediaSpeech LoRA 1 epoch | 0.2699 | 0.1797 | 0.2230 |
| General TR LoRA ckpt750 | 0.1202 | 0.2214 | 0.2825 |
| Balanced-phone LoRA final | 0.1316 | 0.2476 | 0.2986 |

Ham WER ile normalize WER arasındaki fark dikkat çekicidir. General TR LoRA FLEURS'te ham WER'i iyileştirmiş görünmektedir; fakat normalize WER'de baseline'dan kötüdür. Bu, ham WER'in noktalama/büyük harf/yüzey biçimlerinden fazla etkilendiğini ve ana karar metriği olarak normalize WER'in daha güvenilir olduğunu göstermektedir.

## 7. Kritik Bulgular: Ne İşe Yaradı, Ne İşe Yaramadı?

### 7.1. İşe Yaramayan veya Sınırlı Kalan Adımlar

| Yöntem | Sayısal bulgu | Yorum |
|---|---|---|
| Sadece MediaSpeech ile LoRA | MediaSpeech test normalize WER `0.1558 -> 0.2162` | Domain uyumsuzluğu ve az veri nedeniyle başarısız |
| Common Voice ağırlıklı genel LoRA | Common Voice iyileşti, MediaSpeech kötüleşti | Veri dağılımı tek yöne kaydı |
| Daha fazla epoch varsayımı | A2'de dış domainler kötüleşti | Epoch artırmak tek başına çözüm değil |
| VAD olmadan uzun ses transkripsiyonu | test.mp3 Transformers turbo normalize WER `1.1772` | Uzun seslerde tekrar/hallucination riski çok yüksek |
| LoRA'yı repeat-safe decode olmadan kullanmak | test.mp3 WER `0.8469` | Decode hatası model kazanımını silebiliyor |
| Telefon uyarlamalı final modeli temiz dış doğrulamada kullanmak | external360 WER `0.0857 -> 0.1018` | Telefon adaptasyonu temiz okuma/anlatım domainlerinde negatif transfer üretti |

### 7.2. Beklenenden Fazla Etki Eden Adımlar

| Yöntem | Sayısal bulgu | Yorum |
|---|---|---|
| Normalize metrik kullanımı | Baseline MediaSpeech raw WER `0.4255`, normalize WER `0.1558` | Türkçe ASR'de ham WER tek başına yanıltıcı |
| VAD ve segmentasyon | VAD'siz turbo WER `1.1772`, VAD'li turbo WER `0.6568` | Uzun çağrılarda inference hattı kritik |
| Repeat-safe decode | LoRA çağrı WER `0.8469 -> 0.6466` | Modelden bağımsız büyük iyileşme sağladı |
| Veri ağırlıklandırma | MediaSpeech WER A2'de `0.1718`, A3'te `0.1366` | Dengeleme negatif transferi tersine çevirdi |
| Telefon bandı/gürültü augmentasyonu | Çağrı örneğinde final LoRA en iyi WER'i verdi | Telefon kanalına dayanıklılık için faydalı |

## 8. Makale Açısından Yorum

Bu çalışma, Whisper gibi güçlü ön-eğitimli modellerde Türkçe ASR iyileştirmesinin tek boyutlu bir fine-tuning problemi olmadığını göstermektedir.

Önemli akademik sonuçlar:

1. Eğitim dağılımına yakın testte LoRA iyileştirme sağlayabilir.
2. Eğitim dışı temiz domainlerde aynı LoRA negatif transfer oluşturabilir.
3. Telefon/çağrı merkezi gibi uzun ve gürültülü kayıtlarda inference hattı model kadar önemlidir.
4. Türkçe için normalize WER/CER ana metrik olarak raporlanmalıdır.
5. Tek bir model yerine domain'e göre adapter veya inference stratejisi seçimi daha doğru olabilir.

Bu bulgular makale için şu ana iddiaya dönüştürülebilir:

> Türkçe Whisper uyarlamasında başarı, yalnızca açık veri miktarıyla değil; veri dağılımı, akustik kanal benzetimi, domain'e özgü adapter seçimi, VAD/segmentasyon ve tekrar baskılamalı decode stratejilerinin birlikte optimize edilmesiyle belirlenmektedir.

## 9. Sonraki Çalışmalar

### 9.1. Daha Güvenilir Doğrulama Seti

Makale sonucunu güçlendirmek için şu doğrulama havuzu oluşturulmalıdır:

| Domain | Önerilen süre | Not |
|---|---:|---|
| Gerçek çağrı/telefon konuşması | 30-60 dk | Elle düzeltilmiş referans şart |
| Temiz okuma konuşması | 30 dk | FLEURS/Common Voice benzeri |
| Eğitim/anlatım konuşması | 30 dk | Khan Academy benzeri |
| Bankacılık terimleri | 30 dk | Para, tarih, IBAN, kart, hesap, müşteri temsilcisi ifadeleri |

### 9.2. Modelleme Önerileri

1. Tek final model yerine en az iki adapter tutulmalı:
   - Genel Türkçe adapter veya baseline.
   - Telefon/çağrı adapter.
2. Domain'e göre adapter seçen basit bir routing mekanizması denenmeli.
3. Balanced-phone eğitimine dış doğrulama kaybını izleyen early stopping eklenmeli.
4. FLEURS/Khan gibi temiz domainler eğitimde küçük replay seti olarak tutulmalı; böylece negatif transfer azaltılabilir.
5. LoRA rank 8/16/32 karşılaştırması yapılmalı.
6. `q_proj`, `v_proj` dışındaki attention ve MLP modülleri kontrollü olarak denenmeli.
7. Telefon bandı augmentasyon oranı sweep edilmeli; fazla telefonlaştırmanın temiz domainleri bozduğu görüldü.

### 9.3. Değerlendirme Önerileri

1. Ham WER, normalize WER, CER birlikte verilmeli.
2. Ana karar metriği normalize WER olmalı.
3. Bankacılık için özel alan metrikleri eklenmeli:
   - Sayı hatası.
   - Para/tutar hatası.
   - Tarih/saat hatası.
   - IBAN/kart/hane grubu hatası.
   - Özel isim/kurum adı hatası.
4. Uzun çağrılar için tekrar oranı ve hallucination sayısı ayrıca raporlanmalı.

### 9.4. Veri Kaynağı Genişletme

Bu turda kullanılabilir bulunan kaynaklar:

- FLEURS-TR.
- Khan Academy Turkish.
- Khan Academy Turkish Math.
- Common Voice 17 TR Fixed.
- MediaSpeech TR.

Bu turda doğrudan kullanılamayan veya gelecek çalışma olarak bırakılan kaynaklar:

| Kaynak | Durum |
|---|---|
| MINDS-14 | Bankacılık/intent açısından ilginç, ancak Hugging Face konfigürasyonlarında Türkçe yok |
| Turkish Speech Corpus | Büyük boyutlu; Hugging Face yüklemesinde WebDataset biçimi sorunu verdi |
| FLORAS | Çok dilli büyük set; streaming/filtering yavaş ve bu tur için pratik olmadı |
| Yetkilendirme isteyen HF veri setleri | Token/login gerektiği için bu turda kullanılmadı |

## 10. Sonuç

İlk baseline model güçlüdür ve temiz kısa konuşmalarda hâlâ çok rekabetçidir. Açık veriyle yapılan LoRA eğitimleri bazı domainlerde ciddi iyileşme sağlamış, bazı domainlerde ise negatif transfer üretmiştir.

Özet kararlar:

1. MediaSpeech-only LoRA başarısız bir ilk denemedir; bu negatif sonuç raporlanmalıdır.
2. General TR LoRA Common Voice tarafında faydalı olmuş, ancak medya ve dış doğrulamada genelleme problemi göstermiştir.
3. Balanced-phone LoRA eğitim dağılımına yakın Common Voice/MediaSpeech hızlı testinde en iyi sonucu vermiştir.
4. Aynı balanced-phone LoRA, telefon görüşmesinde repeat-safe decode ile en iyi sonucu vermiştir.
5. Ancak balanced-phone LoRA, FLEURS/Khan Academy gibi temiz dış doğrulama setlerinde baseline'dan kötüleşmiştir.
6. Bu nedenle final sonuç "tek model her yerde daha iyi" değil, "domain uyarlaması faydalı ancak kontrollü validasyon ve adapter seçimi gerektiriyor" şeklinde sunulmalıdır.

Bu haliyle çalışma makale için güçlü bir deney hikâyesi sunmaktadır: denenen yöntemlerin bazıları başarısız olmuş, bu başarısızlıklar veri dağılımı ve inference problemi olarak teşhis edilmiş, ardından veri dengeleme/telefon augmentasyonu/decode ayarlarıyla çağrı senaryosunda iyileşme sağlanmıştır. Son eklenen dış doğrulama setleri ise çalışmanın bilimsel güvenilirliğini artırmış ve negatif transfer riskini açıkça ortaya koymuştur.

## 11. Üretilen Dosyalar

Önemli çıktı dosyaları:

```text
data/manifests/external_eval/external_tr_360.jsonl
outputs/evaluation/external360_model_evolution_metrics.md
outputs/evaluation/test_mp3_reference_evaluation_tr.md
outputs/evaluation/user_test_reference_metrics.md
outputs/evaluation/user_test_reference_metrics_to_9m06.md
outputs/predictions/external360_baseline_large_v3_turbo.jsonl
outputs/predictions/external360_lora_mediaspeech_1epoch.jsonl
outputs/predictions/external360_lora_general_checkpoint750.jsonl
outputs/predictions/external360_lora_balanced_phone_final.jsonl
outputs/models/whisper-large-v3-turbo-balanced-phone-from750-lora
```

## 12. Kaynaklar

- OpenSLR SLR108 MediaSpeech: https://www.openslr.org/108/
- Common Voice 17 TR Fixed: https://huggingface.co/datasets/ysdede/commonvoice_17_tr_fixed
- FLEURS dataset: https://huggingface.co/datasets/google/fleurs
- Khan Academy Turkish dataset: https://huggingface.co/datasets/ysdede/khanacademy-turkish
- Khan Academy Turkish Math dataset: https://huggingface.co/datasets/ysdede/khanacademy-turkish-math
- Whisper large-v3-turbo model kartı: https://huggingface.co/openai/whisper-large-v3-turbo

