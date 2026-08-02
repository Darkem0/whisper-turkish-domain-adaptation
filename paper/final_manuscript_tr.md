# Türkçe Telefon-Benzeri Konuşmalar için Whisper Large-v3-Turbo Uyarlaması

## LoRA kapsamı, staged domain adaptation, telefon augmentasyonu, decoding ve negatif transfer üzerine açık-veri çalışması

**Yazar:** Emre Aslan  
**Araştırma deposu:** `Darkem0/whisper-turkish-domain-adaptation`

---

## Öz

Bu çalışma, `openai/whisper-large-v3-turbo` modelinin Türkçe telefon-benzeri ve karşılıklı konuşma koşullarına uyarlanmasını inceler. Araştırma iki dönemden oluşur: tarihsel Legacy deneyler ve ortak frozen evaluation altında yürütülen kontrollü A0–A7 serisi. Kontrollü seride encoder-only, decoder-only ve encoder+decoder LoRA kapsamları; replay, temiz schedule, parent-adapter continuation, kaynak ankrajı ve telefon odaklı augmentasyonlar karşılaştırılmıştır. Değerlendirme; MediaSpeech Clean, Phone ve G.711, CV Scripted, FLEURS, CV Spontaneous ve TSC üzerinde raw/normalized WER ve CER ile yapılmıştır.

En iyi kontrollü Phone sonucu, A2 adapterından staged continuation ile geliştirilen A7 step-200 tarafından `0.1542845` normalized WER olarak elde edilmiştir. A7, A2 (`0.170825`), decoder-only A4 (`0.158385`) ve temiz encoder+decoder A6 (`0.157203`) Phone sonuçlarını geçmiştir. Buna karşılık CV Scripted performansında genel-domain maliyet görülmüştür. A7’nin en iyi robustness proxy sonucu step-150’de `0.1475780` olmuştur; A4 robustness tarafında güçlü bir Pareto adayı olarak kalmıştır.

Sonuçlar, staged domain adaptation’ın telefon proxy’sinde fayda sağlayabildiğini; ancak tek adapterın bütün Türkçe konuşma türlerinde üstün olmadığını göstermektedir. Ayrıca decoding, segmentasyon, kanal ayrımı, prediction provenance ve checkpoint bütünlüğü model eğitimi kadar kritik bulunmuştur. Augmentasyonlar A7 entegrasyonunun parçasıdır; bağımsız nedensel katkıları bu tasarımda ayrıştırılmadığı için `inconclusive` olarak raporlanır.

**Anahtar kelimeler:** Whisper, Türkçe ASR, LoRA, telefon konuşması, domain adaptation, negatif transfer, WER, stereo kanal ayrımı, decoding.

---

## 1. Giriş

Whisper modelleri çok dilli ve güçlü başlangıç noktalarıdır; ancak telefon bandı, spontane konuşma, kısa geri bildirimler, gürültü, kanal sızıntısı ve uzun-form decoding gibi koşullar temiz okuma konuşmasından farklı hata profilleri üretir. Türkçe telefon senaryosunda yalnız ortalama WER değil; deletion, kısa utterance kaybı, tekrar döngüsü, sayı/tarih/tutar ve özel isim hataları da operasyonel önem taşır.

Bu çalışmanın temel sorusu “Whisper Türkçe veriyle fine-tune edilirse genel olarak iyileşir mi?” değildir. Araştırma şu sorulara odaklanır:

1. Encoder ve decoder LoRA kapsamları telefon proxy performansını nasıl etkiler?
2. Replay veya staged continuation genel-domain forgetting’i azaltır mı?
3. Telefon bandı, speed ve noise/gain augmentasyonlarını içeren final entegrasyon hedef proxy’de kazanım üretir mi?
4. Model, decoding ve veri hattı sonuçları nasıl birlikte değerlendirilmelidir?
5. Negatif ve teknik hatalar güvenilir bir araştırma kaydına nasıl dönüştürülmelidir?

---

## 2. Araştırma dönemleri

### 2.1. Legacy seri

Legacy-H0–H4 serisi, Common Voice, MediaSpeech, FLEURS ve Khan Academy kaynaklarıyla yürütülen önceki çalışmaları kapsar.

- **Legacy-H1 MediaSpeech-only LoRA:** MediaSpeech normalized WER `0.1558 → 0.2162`; negatif kontrol.
- **Legacy-H2 General Turkish LoRA:** Common Voice iyileşti, MediaSpeech kötüleşti; veri oranı etkisi.
- **Legacy-H3 balanced-phone continuation:** Eğitim dağılımına yakın Common Voice/MediaSpeech testinde iyileşme; external360 temiz dış-domain setinde `0.0857 → 0.1018` kötüleşme.
- **Legacy-H4 repeat-safe decode:** Uzun telefon örneğinde normalized WER `0.8469 → 0.6466`.

Bu seri, hedef-domain kazancı ile genel-domain maliyetin aynı anda oluşabileceğini ve decoding politikasının model kazancını örtebileceğini gösteren tarihsel temel oldu. Legacy artefakt zincirinin bir bölümü daha sonra erişilemediğinden bu sonuçlar kontrollü A0–A7 serisiyle havuzlanmaz.

### 2.2. Kontrollü A0–A7 seri

Kontrollü seride ortak ilkeler:

- plain Hugging Face Transformers Whisper,
- `openai/whisper-large-v3-turbo`,
- LoRA/PEFT,
- base ağırlıkları frozen,
- rank 16, alpha 32, dropout 0.05,
- batch size 1, gradient accumulation 16,
- FP16,
- sabit frozen evaluation,
- prediction JSONL ve SHA-256,
- raw ve normalized WER/CER,
- checkpoint 50/100/150/200,
- ortak D3 decoding ve MEM0 canonical memory profili.

---

## 3. Veri ve değerlendirme

Frozen evaluation paneli:

| Panel | Veri setleri | Amaç |
|---|---|---|
| Telefon/karşılıklı konuşma | MediaSpeech Phone, MediaSpeech G.711, robustness proxy, CV Spontaneous | Hedef-domain proxy |
| Genel Türkçe izleme | MediaSpeech Clean, CV Scripted, FLEURS, TSC | Negatif transfer ve genelleme |

Robustness proxy, Phone ve G.711 sonuçlarını bir araya getirir. CV Spontaneous örnek sayısı küçüktür ve report-only yorumlanır.

Normalized WER/CER, Türkçe noktalama ve yüzey biçimi farklılıklarının raw WER’i şişirmesini azaltmak için ana karar metriğidir; raw metrikler de birlikte korunur.

---

## 4. Kontrollü deneyler

### A0 — Base referans

A0, adaptasyonsuz modeldir. Phone normalized WER yaklaşık `0.17569` olarak ölçülmüştür.

### A2 — Encoder+decoder Q/V LoRA

A2, hedef proxy’lerde iyileşme üretmiş, Phone WER’i `0.170825` olmuştur. Buna karşılık FLEURS tarafında ciddi regresyon görülmüştür. A2 production’a promote edilmemiş; A7 staged continuation için parent olarak kullanılmıştır.

### A3 — Encoder-only + %10 replay

A3 hedef robustness tarafında kazanç üretmiş, ancak CV Scripted performansı belirgin biçimde kötüleşmiştir. %10 replay genel-domain forgetting’i önlemeye yetmemiştir. Terminal karar `A3_V2_NO_PROMOTABLE_CHECKPOINT` olmuştur.

### A4 — Decoder-only, zero replay

A4 güçlü Phone ve robustness adayıdır:

- en iyi Phone: step-050, `0.158385`,
- en iyi robustness: yaklaşık `0.1441`.

A4, final A7’den sonra da robustness bakımından Pareto-optimal aday olarak kalmıştır.

### A5 — Encoder-only, temiz schedule

A5 boş-transkriptlerden arındırılmış train manifesti ve zero replay ile çalıştırılmıştır. En iyi Phone sonucu yaklaşık `0.157968`; en iyi robustness yaklaşık `0.1475` olmuştur. A4 robustness seviyesini geçememiştir.

### A6 — Encoder+decoder, temiz schedule

A6, A5 ile matched veri/schedule üzerinde daha geniş LoRA kapsamını test etmiştir. En iyi Phone sonucu `0.157203` olmuştur. İlk analizde A5 ve A6’nın eşit olduğu raporlanmış, daha sonra path replacement hatası nedeniyle A6’nın kendisiyle karşılaştırıldığı bulunmuştur. Düzeltme sonrasında 4.059 prediction farkı ve 27/28 hedefte farklı aggregate metric doğrulanmıştır.

### A7 — Staged source-anchored balanced-phone integration

A7:

- A2 parent adapterından devam eder,
- TSC’yi yalnız değiştirilmemiş source anchor olarak kullanır,
- MediaSpeech ve CV Spontaneous kaynaklarını phone-like population olarak dengeler,
- phone-band, `0.75x` speed, noise/gain ve combined augmentasyon kullanır,
- learning rate `5e-6`,
- 200 optimizer step ve 3.200 occurrence hedefler.

A7 augmentasyon schedule’ı:

| Kova | Occurrence |
|---|---:|
| TSC unchanged anchor | 1.067 |
| Phone-like unchanged | 640 |
| Phone-band | 640 |
| Speed 0.75 | 320 |
| Noise/gain | 267 |
| Phone-band + noise/gain | 266 |

Augmentasyon V1/V2’de clipping ve resampling overshoot tespit edilmiştir. V3 universal peak guard yalnız augmented bucketlara uygulanmış; 1.493/1.493 occurrence deterministic, finite ve non-silent olarak doğrulanmıştır.

A7 eğitimi terminal penceresinin kapanmasıyla kesilmiş; final step-200, step-150 adapterından `ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET` ile tamamlanmıştır. Schedule 2.400 indeksinden 3.200’e kadar doğru konumdan devam etmiştir. Bu exact optimizer-state resume değildir ve sınırlama olarak korunur.

---

## 5. Sonuçlar

### 5.1. Phone karşılaştırması

| Model | Checkpoint | Normalize Phone WER |
|---|---:|---:|
| A0 | base | `0.17569` |
| A2 | base | `0.170825` |
| A4 | step-050 | `0.158385` |
| A5 | step-100 | `0.157968` |
| A6 | step-200 | `0.157203` |
| **A7** | **step-200** | **`0.1542845`** |

A7’nin point-estimate iyileşmesi:

- A0’a göre `−0.021405`,
- A2’ye göre `−0.016540`,
- A4’e göre `−0.004100`,
- A6’ya göre `−0.002919`.

A7, kontrollü seride en iyi Phone sonucunu üretmiştir.

### 5.2. A7 checkpoint trajectory

| Hedef | En iyi checkpoint | Normalize WER |
|---|---:|---:|
| MediaSpeech Clean | step-200 | `0.134339` |
| MediaSpeech Phone | step-200 | `0.154285` |
| MediaSpeech G.711 | step-150 | `0.140802` |
| Robustness proxy | step-150 | `0.147578` |

Tek checkpoint bütün hedeflerde en iyi değildir.

### 5.3. Genel-domain maliyet

A7, CV Scripted’da A0/A2 seviyesini koruyamamıştır. Bu nedenle bilimsel sınıflandırma:

- `staged_domain_adaptation_supported`,
- `staged_domain_adaptation_with_general_domain_cost`,
- `augmentation_contribution_inconclusive`.

A7 tasarımı parent continuation, source rebalancing ve çoklu augmentasyonu aynı anda değiştirir. Bu nedenle kazancın yalnız augmentasyondan geldiği iddia edilmez.

---

## 6. Decoding ve memory sonuçları

D0–D7 karşılaştırmasında D3 desteklenen decode profili olmuş, normalized WER `0.156021` olarak kaydedilmiştir.

P4–P6:

- ikinci decode tetiklenmemiş,
- güvenli deterministic ITN dönüşümü bulunmamış,
- gerçek n-best çeşitliliği oluşmamıştır.

P7 memory benchmarkında:

- MEM1 küçük eşit-output hız kazancı,
- MEM2 küçük benchmarkta aynı prediction ile yaklaşık `%32,12` hızlanma,
- MEM3/MEM4 daha yüksek hız fakat prediction drift

göstermiştir. MEM2 `microbenchmark-positive / deployment-inconclusive`; MEM3/MEM4 `rejected_due_to_prediction_drift` olarak sınıflandırılır. Bilimsel karşılaştırılabilirlik için MEM0 canonical kalır.

---

## 7. Mühendislik ve araştırma güvenilirliği

Çalışma boyunca kritik bulgular:

1. Validation loss, hedef-domain kaliteyi tek başına belirlemez.
2. Fiziksel stereo kanal bilgisi varsa diarization’dan önce kullanılmalıdır.
3. Uzun-form ASR’de VAD/segmentasyon ve decode model kadar etkili olabilir.
4. `.wav` uzantısı gerçek codec ve sample rate kalitesini garanti etmez.
5. Prediction hash ve bağımsız metric recomputation zorunludur.
6. State/PID dosyası tek başına process gerçeği değildir.
7. Checkpoint ağırlığı ile schedule konumu aynı step’ten resume edilmelidir.
8. Atomic checkpoint save ve izole continuation run dizini gerekir.
9. Hız optimizasyonu prediction eşitliğini bozuyorsa aynı deney koşulu değildir.
10. Negatif transfer ve yazılım hataları yayın dışında bırakılmamalıdır.

---

## 8. Public bileşen ekosistemi

Kanonik araştırma deposu, commit-kilitli companion repos ile birlikte kullanılır:

- `turkish-speech-processing-platform`: stereo media inceleme, kanal split, rol/timestamp merge ve fixture değerlendirme.
- `contact-center-ai-evaluation-suite`: transcript sonrası typed, evidence-linked sentetik diyalog değerlendirme.
- `research-publications`: authoritative yayın metadata kaydı.
- `applied-ai-engineering-portfolio`: kanıt seviyesi ve proje dizini.

Kodlar kopyalanmaz; `ecosystem/components.lock.json` ve bootstrap scriptiyle aynı çalışma alanına alınır. Böylece tek giriş noktası ve bağımsız Git geçmişleri birlikte korunur.

---

## 9. Sınırlamalar

- Kontrollü sonuçlar açık veri telefon proxy’leridir; gerçek şirket çağrısı değildir.
- A7 tek seed ve optimizer-reset continuation içerir.
- A7 augmentasyonların bağımsız etkisini ayırmaz.
- CV Spontaneous alt kümesi küçüktür.
- Legacy deneylerin bazı özgün artefaktları erişilebilir değildir.
- Sayı, tutar, tarih ve özel isimler için insan doğrulanmış geniş hedef test seti yoktur.
- Gerçek stereo çağrı üzerinde A4/A7 sıralaması doğrulanmamıştır.

---

## 10. Sonuç

A7 staged domain adaptation, açık veri telefon proxy’sinde en iyi kontrollü Phone WER sonucunu üretmiştir. Bununla birlikte A4 robustness tarafında güçlü aday olarak kalmış ve A7 genel-domain maliyet oluşturmuştur. En doğru sonuç “A7 her yerde daha iyi” değildir.

> Türkçe telefon ASR uyarlamasında başarı; veri dağılımı, staged continuation, LoRA kapsamı, kanal/segmentasyon hattı, decoding ve artefakt doğrulamasının birlikte yönetilmesine bağlıdır. Hedef-domain kazancı, genel-domain negatif transfer ve operasyonel hata profiliyle birlikte raporlanmalıdır.

Açık veri deney hattı:

```text
OPEN_DATA_EXPERIMENT_LINE_COMPLETED
```

---

## Kaynak depo belgeleri

- `docs/full_research_report.md`
- `docs/complete_whisper_experience_archive.md`
- `docs/practical_research_guide.md`
- `docs/negative_results.md`
- `docs/reproducibility.md`
- `docs/repository_ecosystem_audit.md`
- `public/metrics/a7_checkpoint_metrics.csv`
