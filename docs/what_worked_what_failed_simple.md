# Neler İşe Yaradı, Neler İşe Yaramadı?

Bu sayfa, bütün araştırmanın en kısa ve uygulanabilir özetidir. Ayrıntılı kanıtlar için [tam rapora](full_research_report.md), [deney kataloğuna](experiment_catalog.md) ve [negatif sonuçlara](negative_results.md) bakılmalıdır.

> En önemli sonuç: Türkçe telefon konuşmasında en iyi sonuç, tek bir rastgele fine-tune denemesinden değil; iyi bir parent adapter, hedef-domain ağırlıklı veri karışımı, kontrollü augmentasyon, sabit decode ve doğru değerlendirme düzeninin birlikte kullanılmasından geldi.

---

## 1. En hızlı özet

### İşe yarayanlar

1. **Staged domain adaptation — A7**
   - A2 parent adapterından düşük learning rate ile devam edildi.
   - TSC değiştirilmemiş kaynak ankrajı olarak korundu.
   - MediaSpeech ve CV Spontaneous telefon-benzeri kaynaklar olarak ağırlaştırıldı.
   - Phone WER kontrollü serinin en iyi değeri olan `0.154285` seviyesine indi.

2. **Decoder-only LoRA — A4**
   - Phone ve robustness tarafında güçlü bir Pareto adayı oldu.
   - Daha geniş encoder+decoder kapsamının otomatik olarak daha iyi olmadığını gösterdi.

3. **Repeat-safe decode**
   - Uzun telefon örneğinde tekrar döngülerini belirgin biçimde azalttı.
   - Aynı adapterın kötü decode ile olduğundan çok daha kötü görünebileceğini gösterdi.

4. **VAD ve doğru segmentasyon**
   - Uzun-form konuşmada hallucination, tekrar ve bağlam taşmasını azalttı.
   - Model eğitimi kadar büyük etki oluşturabildi.

5. **Stereo kanal ayrımı**
   - Fiziksel Agent/Customer kanalı varsa diarization’dan daha güvenilir rol bilgisi verdi.
   - Tarafların erken mono karıştırılmasını önledi.

6. **Raw + normalized WER/CER’i birlikte raporlama**
   - Türkçe yüzey biçimi, noktalama ve casing kaynaklı farkları gerçek ASR hatasından ayırdı.

7. **Prediction hash, checkpoint lock ve bağımsız metric recomputation**
   - A5–A6 self-comparison hatasını yakaladı.
   - İkna edici görünen ama yanlış bir `CI=0` sonucunun yayımlanmasını engelledi.

8. **Clipping-safe augmentasyon**
   - Phone-band, speed ve noise/gain işlemlerinden sonra universal peak guard kullanmak sayısal bozulmayı engelledi.

### İşe yaramayanlar veya reddedilenler

1. **Yalnız MediaSpeech ile LoRA**
   - Normalize WER `0.1558 → 0.2162` kötüleşti.
   - Hedefe yakın görünen tek bir veri kaynağına aşırı eğilmek genellemeyi bozdu.

2. **“Daha fazla epoch daha iyidir” yaklaşımı**
   - Large-v2 deneyinde validation loss düşerken gerçek çağrı kalitesi epoch 3’te bozuldu.

3. **%10 replay’in unutmayı otomatik önleyeceği varsayımı**
   - A3 CV Scripted tarafında ciddi regresyon üretti.
   - Replay oranı, çeşitliliği ve schedule tasarımı yetersiz kaldı.

4. **Daha geniş LoRA kapsamının otomatik sinerji sağlayacağı varsayımı**
   - A6 encoder+decoder kapsamı, en iyi tek-scope sonuçları açık biçimde domine etmedi.

5. **İkinci decode/retry**
   - Test koşullarında tetiklenmedi; maliyetine karşı bilgi kazancı üretmedi.

6. **Koşulsuz deterministic ITN**
   - Güvenli dönüşüm örneği bulunmadığı için reddedildi.
   - Sayı/tarih/tutar dönüşümünde yanlış normalizasyon riski daha yüksekti.

7. **Gerçek n-best olmadan rescoring**
   - Runtime birbirinden anlamlı biçimde farklı hipotezler üretmedi.

8. **MEM3/MEM4 batching**
   - Hızlandı fakat prediction değişti.
   - Aynı bilimsel koşul olarak kabul edilemedi.

9. **State dosyasına tek başına güvenmek**
   - Süreç kapanmasına rağmen `RUNNING` kalan state kayıtları oldu.
   - PID, CPU/GPU, progress ve checkpoint birlikte kontrol edilmelidir.

---

## 2. Yöntem bazında karar tablosu

| Yöntem | Karar | Neden |
|---|---|---|
| MediaSpeech-only fine-tuning | **Başarısız** | Dar domain ve yetersiz çeşitlilik |
| General Turkish LoRA | **Domain-bağımlı** | Bir set iyileşirken diğeri bozuldu |
| Balanced-phone continuation | **Hedefte başarılı** | Telefon-benzeri veri dengesi iyileşti; dış clean domain maliyeti oluştu |
| Encoder-only LoRA | **Sınırlı** | Phone kazancı var, robustness lideri değil |
| Decoder-only LoRA | **Güçlü aday** | A4 Phone/robustness Pareto sonucu |
| Encoder+decoder joint LoRA | **Sınırlı** | Daha geniş scope otomatik sinerji vermedi |
| A2 parent + staged continuation | **Başarılı** | A7 en iyi kontrollü Phone sonucunu verdi |
| %10 clean replay | **Yetersiz** | CV Scripted forgetting’i önlemedi |
| Source anchor | **Faydalı tasarım parçası** | Hedef adaptasyon sırasında değişmemiş kaynak dağılımı korundu |
| Phone-band / speed / noise | **Entegrasyon içinde faydalı olabilir** | A7’de birlikte kullanıldı; bağımsız katkı ayrıştırılmadı |
| Repeat-safe decode | **Başarılı** | Uzun form tekrar döngüsünü düşürdü |
| D3 decode | **Canonical** | Kontrollü karşılaştırma profili |
| MEM0 | **Canonical** | Prediction-safe varsayılan |
| MEM2 | **Microbenchmark olumlu, deployment belirsiz** | Küçük testte aynı çıktı ve hız kazancı; geniş üretim kanıtı yok |
| MEM3/MEM4 | **Reddedildi** | Prediction drift |
| VAD/segmentasyon | **Başarılı** | Uzun-form güvenilirliği yükseldi |
| Stereo kanal split | **Başarılı** | Rol bilgisi deterministic kaldı |

---

## 3. Neden bazı yöntemler çalışmadı?

### Veri miktarı ile veri dağılımı aynı şey değildir

Daha fazla saat veri, modelin doğru konuşma türünü öğrendiği anlamına gelmez. Read speech, spontane konuşma, telefon bandı, kısa cevaplar ve temiz stüdyo sesi farklı hata profilleri üretir.

### Validation loss hedef iş yükünü temsil etmeyebilir

Ortalama loss düşerken:

- sayı ve tutar hatası,
- kısa cevap silinmesi,
- özel isim bozulması,
- uzun-form tekrar döngüsü

artabilir. Bu nedenle gerçek hedef-domain dev set zorunludur.

### Replay oranı değil, replay içeriği belirleyicidir

Replay:

- yeterli çeşitlilik taşımıyorsa,
- target schedule tarafından bastırılıyorsa,
- yalnız az sayıda temiz örneği tekrarlıyorsa

genel-domain forgetting’i engelleyemez.

### Daha çok trainable parametre daha iyi model demek değildir

Encoder ve decoder birlikte açıldığında:

- gradyanlar birbirini bastırabilir,
- küçük veri üzerinde gereksiz kapasite oluşabilir,
- domain eğilimi artabilir.

A4’ün güçlü sonucu bu nedenle önemlidir.

### Decode hatası model hatası gibi görünebilir

VAD, chunk sınırı, tekrar baskılama, timestamp promptu ve attention mask ayarları yanlışsa iyi bir adapter kötü görünebilir.

---

## 4. Gerçek veriye geçerken hangi modeli denemeliyim?

En az şu üç adayı aynı insan-doğrulanmış gerçek test setinde karşılaştır:

1. **A0 base** — tarafsız referans.
2. **A4** — decoder-only, güçlü robustness adayı.
3. **A7** — en iyi açık-veri Phone adayı.

A7’nin açık veri Phone sonucu en iyi olsa da gerçek çağrıda otomatik kazanan olduğu kanıtlanmamıştır.

---

## 5. Gerçek veri için hızlı A7 başlangıç tarifi

Bu tarif A7’den türetilmiş pratik bir başlangıçtır; evrensel optimum olduğu iddia edilmez.

### Model

- Base: `openai/whisper-large-v3-turbo`
- Başlangıç: mevcut A7 veya doğrulanmış genel/telefon parent adapter
- Scope: encoder+decoder `q_proj/v_proj`
- LoRA rank: `16`
- Alpha: `32`
- Dropout: `0.05`
- Base weights: frozen

### Eğitim

- Learning rate: `5e-6`
- Batch size: `1`
- Gradient accumulation: `16`
- FP16
- AdamW
- Linear scheduler
- Warmup: `20` optimizer step
- İlk eleme: `200` optimizer step
- Checkpoint: `50 / 100 / 150 / 200`

### Veri karışımı

Başlangıç şablonu:

- yaklaşık `%25–35` değişmemiş anchor,
- yaklaşık `%65–75` gerçek hedef telefon konuşması veya telefon-benzeri veri.

Anchor mutlaka TSC olmak zorunda değildir. Gerçek projede:

- temiz ve doğru Türkçe,
- önemli genel kelime dağarcığı,
- hedef dışı ama korunması gereken konuşma türü

kullanılmalıdır.

### Augmentasyon

Yalnız gerçek üretim dağılımıyla uyumlu bozulmaları kullan:

- phone-band,
- gerçek codec/G.711 benzetimi,
- sınırlı speed perturbation,
- ölçülmüş SNR aralığında noise,
- kontrollü gain.

Her augmented waveform için:

- finite,
- non-silent,
- final peak kontrolü,
- duration kontrolü,
- transcript değişmezliği

zorunlu olmalıdır.

### Değerlendirme

Tek bir WER yeterli değildir. Ayrı raporla:

- customer WER/CER,
- agent WER/CER,
- call-level macro WER,
- deletion / insertion / substitution,
- kısa cevap doğruluğu,
- sayı, tarih ve tutar doğruluğu,
- kişi/kurum/ürün adı doğruluğu,
- hallucination ve repetition,
- genel Türkçe holdout sonucu.

### Karar

En düşük tek WER’e değil, Pareto dengesine bak:

- hedef çağrı kazancı,
- kritik entity doğruluğu,
- genel-domain maliyeti,
- latency ve kaynak kullanımı.

---

## 6. En hızlı güvenli deney sırası

```text
1. Gerçek insan-doğrulanmış dev ve final holdout hazırla
2. A0 / A4 / A7 baseline evaluation yap
3. A7 tarzı 200-step staged continuation çalıştır
4. 50/100/150/200 checkpointlerini gerçek dev sette ölç
5. En iyi 1–2 adayı hata türlerine göre seç
6. Final holdout’u yalnız bir kez çalıştır
7. Sonra gerekirse daha uzun eğitim veya tek bir hedefli ablation yap
```

Yeni gerçek veride önce onlarca yöntem denemek yerine bu sıra, mevcut araştırmadan gelen en yüksek bilgi değerli başlangıçtır.

---

## 7. Kırmızı çizgiler

- Gerçek test setini training veya checkpoint seçimi için kullanma.
- Aynı çağrının segmentlerini train/dev/test arasında bölme.
- Timestamp, codec ve kanal rolü metadata’sını kaybetme.
- Prediction değiştirerek hızlanan batching’i eşdeğer sayma.
- Yalnız validation loss ile checkpoint seçme.
- Ham ve normalized metrikleri karıştırma.
- Resume sırasında checkpoint ağırlığı ile schedule konumunu farklı step’lerden alma.
- A7’yi gerçek çağrıda ölçmeden production kazananı ilan etme.

---

## 8. Tek cümlelik sonuç

> En hızlı makul yol, A7’nin staged domain-adaptation düzenini gerçek ve insan-doğrulanmış hedef veriyle yeniden kurmak; A0 ve A4’ü koruyarak aynı holdout üzerinde karşılaştırmak ve kritik çağrı hatalarını genel Türkçe WER’den ayrı ölçmektir.
