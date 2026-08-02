# ChatGPT Hafızası Kapsamı, Kanıt Kaynakları ve Redaksiyon Politikası

Bu belge, `complete_whisper_experience_archive.md` ve bağlantılı zaman çizelgesinin hangi kaynaklardan oluşturulduğunu, hangi bilgilerin yayımlanmadığını ve “bütün ChatGPT hafızası” ifadesinin teknik sınırını açıklar.

## 1. Kapsam beyanı

Arşiv aşağıdaki erişilebilir kaynakların sentezidir:

1. Bu ChatGPT projesindeki konuşma geçmişi ve proje özeti.
2. Kullanıcıyla önceki konuşmalardan kalıcı kişisel bağlama aktarılmış Whisper/ASR kayıtları.
3. Kullanıcının File Library alanındaki Whisper raporları, handoff belgeleri, PowerShell çıktıları ve araştırma metinleri.
4. Yerel proje sonuçlarından kullanıcı tarafından sohbetlere taşınan metrikler, hashler, checkpoint bilgileri ve hata günlükleri.
5. GitHub deposunda daha önce yayımlanan A0–A7 araştırma belgeleri.

Bu kapsam geniştir; ancak aşağıdakilerin eksiksiz olduğu garanti edilemez:

- silinmiş sohbetler,
- kalıcı hafızaya aktarılmamış eski mesajlar,
- File Library’ye yüklenmemiş yerel dosyalar,
- indekslenmemiş veya erişim süresi dolmuş ekler,
- başka hesaplarda yürütülmüş çalışmalar,
- artık diskte bulunmayan eski Codex çalışma klasörleri.

Bu nedenle doğru ifade:

> Erişilebilen ChatGPT hafızası, yüklenmiş raporlar ve doğrulanabilir proje artefaktları kapsamındaki en geniş Whisper arşivi.

Yanlış ifade:

> OpenAI sistemlerinde geçmişte var olmuş her sohbetin eksiksiz dökümü.

---

## 2. Kaynak aileleri

### 2.1. Kontrollü deney artefaktları

En yüksek kanıt düzeyi:

- A0–A7 frozen evaluation sonuçları,
- prediction JSONL ve hash kayıtları,
- checkpoint mapping ve adapter SHA,
- training/evaluation progress,
- D0–D7 decode sonuçları,
- P3–P7 kalite ve memory deneyleri,
- A5–A6 path bug düzeltme kayıtları,
- A7 resume ve final integrity kayıtları.

Bu kaynaklar `A — artefakt doğrulamalı` olarak sınıflandırılır.

### 2.2. Legacy genişletilmiş rapor

Eski açık veri deneyleri şu bilgileri sağlar:

- Common Voice ve MediaSpeech eğitim hacimleri,
- MediaSpeech-only LoRA negatif sonucu,
- general checkpointin domain ayrışması,
- balanced-phone continuation,
- uzun çağrıda repeat-safe decode,
- FLEURS/Khan external360 negatif transferi.

Ancak eski checkpoint, manifest ve prediction dosyalarının bir bölümü daha sonraki disk denetiminde bulunamamıştır. Bu nedenle `B — arşiv raporu doğrulamalı` sınıfındadır.

### 2.3. ChatGPT konuşma hafızası

Aşağıdaki dönemler çoğunlukla konuşma hafızasından gelir:

- 2025 kişisel large-v3 epoch denemeleri,
- Ocak 2026 large-v2 LoRA eğitimi,
- gerçek çağrı üzerinde large-v3/large-v2/fine-tuned sıralaması,
- GB10 ARM64/CUDA runtime tecrübeleri,
- I3R vendor decode zinciri,
- stereo kanal ayrımı ve timestamp repair,
- üretim containerı RAM/tmpfs ve servis gözlemleri,
- LLM ile semantik transcript değerlendirmesi.

Bu bilgiler `C — konuşma hafızası` sınıfındadır. Sayısal iddia yalnız hafızada açık biçimde korunmuşsa verilir; eksik alanlar tahmin edilmez.

### 2.4. Derin araştırma raporları

Araştırma belgeleri şu yöntemleri kapsar:

- açık Türkçe veri kaynakları,
- LoRA, AdaLoRA, DoRA ve layer-selective PEFT,
- SpecAugment, codec/noise augmentation,
- external LM ve contextual biasing,
- VAD, denoise, beamforming ve separation,
- forced alignment ve diarization,
- distillation, quantization ve speculative decoding,
- multi-ASR fusion ve audio-aware pseudo-labeling.

Bu yöntemler, proje artefaktıyla çalıştırılmadıysa `R — araştırıldı, uygulanmadı` olarak işaretlenir.

---

## 3. Kanıt öncelik sırası

Çelişkili bilgi bulunduğunda şu sıra kullanılır:

1. Prediction/checkpoint artefaktı ve SHA.
2. Yeniden hesaplanmış metric tablosu.
3. Training/evaluation progress ve terminal integrity raporu.
4. Düzeltilmiş final proje raporu.
5. Eski arşiv raporu.
6. ChatGPT konuşma hafızası.
7. Plan veya araştırma önerisi.

Örnek: A5–A6 ilk analizinde iki deney eşit görünüyordu. Prediction düzeyindeki yeniden inceleme 4.059 farklı tahmin ve 27/28 farklı aggregate metric gösterdi. Eski zero-delta iddiası iptal edildi.

Örnek: P7 ham benchmark MEM2 için `%32,12` hızlanma ve aynı prediction hash gösterirken, proje özeti MEM2’yi “anlamlı değil” diye sınıflandırdı. Arşiv bu çatışmayı silmek yerine MEM2’yi `microbenchmark-positive / deployment-inconclusive` olarak kaydetti.

---

## 4. Birleştirilmeyen deney kimlikleri

Aynı A0/A1/A2 adları farklı dönemlerde farklı şeyler için kullanılmıştır.

Bu nedenle:

- Eski seri `Legacy-H0`–`Legacy-H4`,
- Yeni kontrollü seri `A0`–`A7`

olarak ayrı tutulur.

Örneğin legacy A3 balanced-phone continuation, kontrollü A3 encoder-only + replay ile aynı deney değildir.

---

## 5. Redaksiyon politikası

Public GitHub belgelerinde aşağıdakiler çıkarılır veya genelleştirilir.

### 5.1. Kişisel ve müşteri verisi

- telefon numaraları,
- e-posta adresleri,
- gerçek kişi adları,
- müşteri/temsilci konuşma içerikleri,
- hesap, kart, IBAN ve finansal bilgiler,
- çağrı kayıtlarının dosya adları ve kimlikleri.

### 5.2. Şirket altyapısı

- özel IP adresleri,
- UNC/network-share yolları,
- sunucu ve kullanıcı adları,
- özel API portları,
- proje/activity kimlikleri,
- veritabanı tablo/kolon ayrıntıları,
- dahili servis topolojisi,
- deployment secrets.

### 5.3. Yerel sistem ayrıntıları

- tam Windows/Linux mutlak yolları,
- erişim tokenları,
- SSH bilgileri,
- cache içinde özel dosya adları,
- lisansı veya paylaşım izni belirsiz veri kopyaları.

### 5.4. Model ve veri artefaktları

- özel checkpointler,
- ham sesler,
- özel transkriptler,
- lisansı doğrulanmamış veri dosyaları,
- üretim loglarının ham kopyaları.

Teknik olarak gerekli olduğunda yalnız göreli veya anonimleştirilmiş yol kullanılır:

```text
runs/A7/.../step-200
```

yerel kullanıcı dizini yayımlanmaz.

---

## 6. Korunan teknik ayrıntılar

Redaksiyon, araştırmanın teknik değerini ortadan kaldırmamalıdır. Şunlar korunur:

- model ailesi ve framework,
- genel donanım sınıfı,
- LoRA scope/rank/alpha/dropout,
- batch ve gradient accumulation,
- learning rate ve optimizer step,
- veri kaynağının kamuya açık adı,
- anonimleştirilmiş veri hacmi,
- WER/CER sonuçları,
- checkpoint numarası,
- adapter SHA,
- hata sınıfı ve düzeltme yöntemi,
- pipeline mimarisi,
- başarısızlık ve negatif transfer,
- araştırıldı/uygulandı ayrımı.

---

## 7. Yayımlanabilirlik sınıfları

| İçerik | Public repo | Açıklama |
|---|---:|---|
| A0–A7 aggregate WER/CER | Evet | Açık veri proxy sonuçları |
| LoRA yapılandırması | Evet | Genel araştırma bilgisi |
| Hata ve resume dersleri | Evet | Özel yol/host redakte edilerek |
| Public veri seti adları | Evet | Lisans notlarıyla |
| Final adapter SHA | Evet | Model dosyası yayımlanmıyor |
| Ham prediction metinleri | Genellikle hayır | Veri lisansı ve içerik riski |
| Özel çağrı ses/transkript | Hayır | PII ve şirket verisi |
| Dahili servis/API ayrıntısı | Hayır | Güvenlik ve gizlilik |
| Tam yerel klasör yapısı | Hayır | Kullanıcı/makine bilgisi |
| Araştırma önerileri | Evet | Denenmiş gibi sunulmadan |

---

## 8. Bilimsel iddia politikası

Her iddia şu sorularla kontrol edilir:

1. Bu yöntem gerçekten çalıştırıldı mı?
2. Aynı değerlendirme protokolünde mi ölçüldü?
3. Sonuç aggregate tablo mu, prediction’dan yeniden hesaplandı mı?
4. Checkpoint ve dataset mapping doğrulandı mı?
5. Sonuç açık veri proxy’si mi, gerçek çağrı mı?
6. Genel-domain maliyet raporlandı mı?
7. Tek seed veya resume sınırlaması var mı?

Bu sorulardan biri belirsizse dil yumuşatılır:

- “kanıtlandı” yerine “desteklendi”,
- “başarılı” yerine “hedef proxy’de iyileşti”,
- “üretim modeli” yerine “araştırma adayı”,
- “gerçek çağrı performansı” yerine “telefon-benzeri açık veri proxy’si”.

---

## 9. Bilinen boşluklar

Arşivde eksik olabilecek başlıca alanlar:

- 2025 large-v3 kişisel veri deneylerinin tam metrikleri,
- Ocak 2026 large-v2 deneyinin özgün checkpoint/prediction dosyaları,
- bazı eski I3R pipeline script sürümleri,
- bazı üretim diarization testlerinin ölçüm tabloları,
- legacy çalışmanın kaybolmuş manifest ve adapter dosyaları,
- gerçek çağrı için insan doğrulanmış geniş gold test seti,
- çoklu seed sonuçları,
- pseudo-label mimarisinin deneysel sonucu.

Eksik bilgi uydurulmaz; `UNKNOWN`, `NOT_AVAILABLE`, `NOT_EVALUATED` veya `RESEARCHED_NOT_EXECUTED` olarak tutulur.

---

## 10. Güncelleme prosedürü

Yeni bir eski sohbet veya yerel artefakt bulunduğunda:

1. Kaynak türü belirlenir.
2. Özel veri redakte edilir.
3. Deney kimliği mevcut serilerle karıştırılmaz.
4. Hash veya prediction varsa authoritative kayıtla karşılaştırılır.
5. Çelişki discrepancy loguna yazılır.
6. Eski yanlış iddia silinmek yerine `SUPERSEDED` olarak işaretlenir.
7. Timeline, method matrix ve complete archive birlikte güncellenir.

---

## 11. Son kapsam bildirimi

Bu yayın, erişilebilen kaynaklar içinde Whisper çalışmalarının en geniş bütünleşik kaydıdır. Bununla birlikte ChatGPT’nin bütün tarihsel sistem veritabanına doğrudan erişildiği veya silinmiş her sohbetin kurtarıldığı iddia edilmez.

Yayınlanan arşiv şu üç şeyi açıkça ayırır:

- gerçekten çalıştırılmış ve artefaktla doğrulanmış deneyler,
- eski rapor veya konuşma hafızasında kalan deneyimler,
- yalnız araştırılmış gelecek yöntemleri.
