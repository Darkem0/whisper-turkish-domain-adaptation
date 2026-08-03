# A7 Tarzı Gerçek Veri Uyarlaması — Hızlı ve Güvenli Uygulama Rehberi

Bu belge, açık-veri A7 deneyinde işe yarayan staged domain-adaptation yaklaşımını gerçek telefon veya çağrı verisine taşımak için hazırlanmış pratik bir yol haritasıdır.

> Kapsam sınırı: A7 açık veri telefon proxylerinde başarılı oldu. Aynı yapı gerçek çağrı verisinde henüz doğrulanmış değildir. Bu rehber bir başlangıç planıdır; gerçek sonuç, insan-doğrulanmış hedef-domain değerlendirmeyle belirlenmelidir.

---

## 1. Amaç

En kısa sürede şu soruya güvenilir cevap vermek:

> Base Whisper, A4 decoder-only ve A7 staged-adaptation adaylarından hangisi gerçek hedef konuşmada en düşük operasyonel hatayı veriyor; A7 tarzı yeni continuation bu sonucu daha da iyileştiriyor mu?

Bu amaç için yüzlerce rastgele deneme yerine az sayıda, yüksek bilgi değerli koşul kullanılır.

---

## 2. Önerilen adaylar

İlk karşılaştırmada en az şu üç aday bulunmalıdır:

| Aday | Rol |
|---|---|
| A0 base | Adaptasyonun gerçekten fayda sağlayıp sağlamadığını gösterir |
| A4 decoder-only | Güçlü robustness Pareto adayı |
| A7 step-200 | En iyi kontrollü Phone proxy sonucu |

Yeni gerçek-data continuation dördüncü adaydır:

| Aday | Rol |
|---|---|
| A7-Real | Gerçek hedef veri üzerinde staged continuation |

A7 checkpointine erişilemiyorsa başlangıç:

- A2 gibi doğrulanmış genel/telefon parent adapter veya
- fresh base + kısa A2-benzeri hazırlık aşaması

olabilir. Parent seçimi ayrı bir deney değişkeni olarak kaydedilmelidir.

---

## 3. Veri seti tasarımı

### 3.1. Bölme birimi

Segment değil, mümkün olan en üst konuşma grubu kullanılmalıdır:

1. müşteri/konuşmacı kimliği hash’i,
2. çağrı kimliği,
3. recording ID,
4. kaynak kayıt grubu.

Aynı çağrının farklı segmentleri train ve test arasında bulunmamalıdır.

### 3.2. Dört veri bölümü

| Bölüm | Amaç | Kullanım |
|---|---|---|
| Train target | Gerçek hedef-domain adaptasyonu | Eğitim |
| Anchor | Genel Türkçe/korunacak davranış | Eğitim karışımı |
| Development | Checkpoint seçimi ve hata analizi | Tekrarlı değerlendirme |
| Final holdout | Nihai model kararı | Bir kez, shortlist kilitlendikten sonra |

### 3.3. İnsan doğrulaması

Development ve final holdout referansları:

- insan tarafından yazılmış veya tamamen düzeltilmiş,
- annotation policy sürümü belli,
- kanal rolü belli,
- sayı/tarih/tutar politikası belli,
- anlaşılmayan ve overlap alanları işaretlenmiş

olmalıdır.

Model-only pseudo-label final gold referans değildir.

---

## 4. Gerçek çağrı için annotation standardı

Aşağıdakileri eğitim ve değerlendirme öncesinde kilitle:

- dolgu kelimeleri yazılacak mı,
- tekrarlar korunacak mı,
- yarım kelimeler nasıl gösterilecek,
- sayılar surface form mu, rakam mı,
- para birimi nasıl yazılacak,
- tarih formatı,
- özel isim ve yabancı ürün adı politikası,
- anlaşılmayan ses etiketi,
- overlap/crosstalk etiketi,
- segment başı/sonu kesilme etiketi,
- noktalama ve casing.

Önerilen üç katman:

1. **Verbatim reference** — duyulan biçim.
2. **Canonical ASR reference** — WER/CER için standardize edilmiş biçim.
3. **Entity-normalized output** — sayı, tutar, tarih ve downstream kullanım.

Bu katmanlar birbirine karıştırılmamalıdır.

---

## 5. A7-Real başlangıç schedule’ı

A7’de 3.200 occurrence içinde yaklaşık üçte bir anchor ve üçte iki phone-like veri kullanıldı. Gerçek projede başlangıç şablonu:

| Kova | Başlangıç oranı |
|---|---:|
| Değişmemiş anchor | `%25–35` |
| Değişmemiş gerçek target | `%20–30` |
| Phone/codec bozulması | `%15–25` |
| Speed perturbation | `%5–10` |
| Noise/gain | `%5–10` |
| Combined gerçekçi bozulma | `%5–10` |

Oranlar öneridir; A7’nin evrensel optimum oranları değildir.

### Anchor nasıl seçilir?

Anchor:

- hedef dışı ama korunması gereken Türkçe davranışı,
- genel kelime dağarcığını,
- temiz telaffuzu,
- kritik entity biçimlerini

korumalıdır.

Aynı veriyi kör biçimde tekrar etmek yerine kaynak ve konuşmacı çeşitliliği hedeflenmelidir.

---

## 6. Augmentasyon politikası

### 6.1. Kural

Augmentasyon gerçek üretim dağılımını taklit etmelidir. “Daha fazla bozulma daha iyi” değildir.

Önce gerçek kayıt envanteri çıkar:

- sample rate,
- codec,
- kanal yapısı,
- RMS/peak,
- SNR,
- packet/gap belirtileri,
- crosstalk,
- sessizlik oranı,
- konuşma hızı.

### 6.2. Başlangıç augmentasyonları

- Telefon bandı veya gerçek codec filtresi
- G.711 A-law/μ-law, gerçekten kullanılıyorsa
- Sınırlı speed perturbation: örneğin `0.90–1.10`; A7’deki `0.75` yalnız gerçek yavaşlama ihtiyacı varsa korunmalı
- Ölçülmüş dağılıma uygun noise SNR
- Negatif veya sınırlı gain
- Gerçekçi combined transform

### 6.3. Güvenlik kapıları

Her augmented occurrence:

- deterministic,
- finite,
- non-silent,
- beklenen duration,
- doğru transcript,
- final peak `<= 0.98` civarı,
- noise kullanıldıysa hedef SNR toleransı

kapılarından geçmelidir.

Hard clipping, limiter ve sessiz normalization ile hatayı gizleme.

---

## 7. Model ve eğitim yapılandırması

A7’den türetilmiş başlangıç:

```text
base_model: openai/whisper-large-v3-turbo
initialization: validated parent adapter continuation
lora_scope: encoder + decoder q_proj/v_proj
rank: 16
alpha: 32
dropout: 0.05
base_weights: frozen
precision: fp16
batch_size: 1
gradient_accumulation: 16
optimizer: AdamW
learning_rate: 5e-6
scheduler: linear
warmup_steps: 20
optimizer_steps: 200
checkpoints: 50, 100, 150, 200
```

Bu ayarlar doğrudan uzun eğitim için değil, ilk eleme için kullanılmalıdır.

### Neden önce 200 step?

- hızlı checkpoint trajectory verir,
- erken overfit sinyalini gösterir,
- gerçek dev set üzerinde yönü doğrular,
- yanlış veri veya annotation politikasını erken yakalar.

200 step sonucunda eğri hâlâ belirgin iyileşiyorsa, ayrı yetkilendirilmiş uzun koşu yapılabilir.

---

## 8. Preflight ve smoke

Tam eğitimden önce:

1. Manifest ve audio hash doğrulaması
2. Train/dev/final overlap kontrolü
3. Kanal rolü kontrolü
4. Empty transcript kontrolü
5. 32 microbatch’lik 2-step smoke
6. Encoder ve decoder LoRA gradient kontrolü
7. Finite loss
8. OOM/NaN/Inf kontrolü
9. Augmentasyon kova temsili
10. Adapter save/load ve SHA kontrolü

Smoke checkpointi tam eğitime taşınmamalıdır.

---

## 9. Decode sözleşmesi

Model karşılaştırmasında decode değişmemelidir.

Başlangıç:

- D3-benzeri sabit deterministic profile
- aynı language/task
- aynı normalization
- aynı VAD/segmentasyon
- aynı timestamp policy
- aynı attention mask davranışı

Uzun çağrı için secondary repeat-safe profile ayrıca ölçülebilir; primary sonuçla karıştırılmamalıdır.

---

## 10. Gerçek hedef metrikleri

### 10.1. Ana ASR metrikleri

- raw/normalized WER
- raw/normalized CER
- call-level macro WER
- duration-weighted WER
- median call/segment WER
- deletion/insertion/substitution rate

### 10.2. Kanal bazlı

- agent WER/CER
- customer WER/CER
- agent–customer farkı
- birleşik çağrı sonucu

### 10.3. Operasyonel içerik

- sayı doğruluğu
- para tutarı doğruluğu
- tarih doğruluğu
- uzun rakam dizisi doğruluğu
- kişi/kurum/ürün adı doğruluğu
- domain terimi doğruluğu

### 10.4. Güvenilirlik

- empty output
- hallucination
- repetition loop
- wrong-language output
- segment başı/sonu kaybı
- kanal karışması
- crosstalk alt kümesi
- kısa cevap deletion

---

## 11. Checkpoint seçimi

Tek bir birleşik skor yerine Pareto seçimi kullan.

Örnek karar sırası:

1. Kritik operasyonel hata artmıyor mu?
2. Customer kanalında iyileşme var mı?
3. Sayı/tutar/tarih/isim doğruluğu artıyor mu?
4. Call-level macro WER iyileşiyor mu?
5. Agent tarafında kabul edilemez kayıp var mı?
6. Genel Türkçe holdout maliyeti kabul edilebilir mi?
7. Latency ve VRAM uygun mu?

A7 deneyinde Phone ve robustness için farklı checkpointler öne çıktı. Gerçek veride de tek checkpoint bütün alt gruplarda en iyi olmayabilir.

---

## 12. Hızlı deney matrisi

İlk tur için yalnız dört koşul yeterlidir:

| ID | Model | Eğitim |
|---|---|---|
| R0 | A0 base | Yok |
| R1 | A4 | Yok; mevcut aday evaluation |
| R2 | A7 | Yok; mevcut aday evaluation |
| R3 | A7-Real | 200-step gerçek-data continuation |

Sonra yalnız şu durumda ek deney yap:

- R3 hedef metriği iyileştiriyor ama spesifik bir kritik alt grupta bozuluyorsa,
- hangi tek müdahalenin bunu düzelteceğine dair net hipotez varsa.

Rastgele A8–A20 serisi başlatma.

---

## 13. Resume ve checkpoint

A7’de yaşanan hataları tekrar etmemek için checkpointte şunları sakla:

- adapter model/config,
- optimizer,
- scheduler,
- gradient scaler,
- RNG state,
- global optimizer step,
- microbatch/schedule index,
- source checkpoint,
- manifest/schedule/augmentation hashleri.

Resume sırasında:

- ağırlık step’i,
- scheduler step’i,
- schedule index

aynı noktadan gelmelidir.

Exact state yoksa `ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET` açıkça yazılmalıdır.

---

## 14. En kısa üretim yolu

```text
Gün 1: codec/channel/annotation audit + dev/final split
Gün 2: A0/A4/A7 baseline evaluation
Gün 3: A7-Real schedule + augmentation preflight + smoke
Gün 4: 200-step training ve checkpoint dev evaluation
Gün 5: hata analizi, shortlist lock, final holdout
```

Bu süreler veri boyutu ve donanıma bağlı operasyonel plan örneğidir; garanti edilen süre değildir.

---

## 15. Stop kuralları

Aşağıdakilerden biri varsa eğitimi uzatma:

- dev Phone WER iyileşmiyor,
- kritik entity hatası artıyor,
- deletion belirgin yükseliyor,
- customer tarafı bozuluyor,
- hallucination/repetition artıyor,
- checkpoint trajectory düzleşiyor veya geri dönüyor,
- general holdout kaybı iş gereksinimini aşıyor.

Uzun eğitim ancak kısa koşu net fayda gösterirse yapılmalıdır.

---

## 16. Nihai öneri

> Gerçek telefon verisi geldiğinde en hızlı güvenli yol, A0/A4/A7’yi aynı insan-doğrulanmış dev sette ölçmek, A7’yi parent olarak düşük learning rate ile 200-step staged continuation yapmak, yaklaşık üçte bir anchor korumak ve model seçimini Phone WER’den daha geniş operasyonel hata paneliyle vermektir.
