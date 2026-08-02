# Tam Whisper Deneyim Arşivi — ChatGPT Hafızası, Yerel Raporlar ve Kontrollü Deneyler

Bu belge, 2025–2026 boyunca yürütülen Whisper, WhisperX, Türkçe ASR, LoRA/PEFT, uzun ses işleme, stereo kanal ayrımı, VAD, diarization, decoding, inference optimizasyonu, veri hazırlama, değerlendirme ve pseudo-label araştırmalarını tek bir arşivde toplar.

Amaç yalnızca son A7 sonucunu göstermek değildir. Amaç, ilk prototiplerden üretim boru hattına, başarısız fine-tune denemelerinden kontrollü A0–A7 serisine ve gelecekteki pseudo-label mimarisine kadar bütün öğrenme çizgisini yeniden yayımlanabilir hâle getirmektir.

> Bu belge, erişilebilen ChatGPT konuşma hafızası, yüklenmiş raporlar, yerel proje özetleri ve GitHub’daki mevcut araştırma belgelerinin sentezidir. Silinmiş, indekslenmemiş veya erişilemeyen eski sohbetlerin eksiksiz kapsandığı iddia edilmez.

---

## 1. Kanıt sınıfları

Bu arşivde farklı dönemlerin kanıt gücü aynı değildir. Her bulgu aşağıdaki sınıflardan biriyle okunmalıdır.

| Sınıf | Tanım | Örnek |
|---|---|---|
| **A — Artefakt doğrulamalı** | Prediction, metric, checkpoint, progress, hash veya frozen evaluation artefaktı mevcut | Kontrollü A0–A7 serisi, A7 final checkpoint, P7 memory benchmark |
| **B — Arşiv raporu doğrulamalı** | Eski raporda sayısal sonuç mevcut; fakat bazı özgün checkpoint/prediction dosyaları artık yerelde yok | Legacy balanced-phone ve external360 sonuçları |
| **C — Konuşma hafızası** | ChatGPT geçmişinde yapılandırma veya nitel sonuç kayıtlı; özgün dosya bu public depoda yok | 2026 Ocak large-v2 LoRA ve gerçek çağrı karşılaştırması |
| **R — Araştırıldı, uygulanmadı** | Literatür ve mimari araştırması yapıldı; deney çalıştırılmadı | Qwen3-ASR + Qwen3-Omni pseudo-label mimarisi, AdaLoRA, DoRA |

Bu ayrım kritik önemdedir. Bir araştırma önerisi, çalıştırılmış deney gibi; bir konuşma hafızası da artefakt doğrulamalı sonuç gibi sunulmamalıdır.

---

## 2. Kamuya açık yayın için uygulanan redaksiyon

Aşağıdakiler özellikle yayımlanmaz:

- özel IP adresleri ve ağ paylaşımı yolları,
- şirket ve sunucuya özgü kullanıcı/host adları,
- dahili API portları, proje kimlikleri ve veritabanı şemaları,
- müşteri veya temsilci adları,
- banka/finans çağrılarının özgün transkriptleri,
- ham çağrı sesleri,
- erişim tokenları, SSH bilgileri veya parolalar,
- yerel mutlak dosya yollarının tamamı,
- özel model checkpointleri ve lisansı belirsiz veri kopyaları,
- kişisel veri ve üretim loglarında yer alan çağrı kimlikleri.

Yayımlanan içerik teknik dersleri, anonimleştirilmiş ölçümleri ve yeniden üretim ilkelerini korur; özel altyapıyı veya çağrı içeriğini açığa çıkarmaz.

---

## 3. Genel gelişim çizgisi

Çalışma beş dönemde gelişti:

1. **Ses alma ve dönüştürme:** Özel I3R kayıtlarını güvenilir biçimde WAV’a çevirmek ve uçtan uca loglamak.
2. **İlk fine-tuning dönemi:** Whisper large-v2/large-v3 üzerinde LoRA, epoch karşılaştırması ve gerçek çağrı testleri.
3. **Uzun ses ve stereo üretim hattı:** Kanal ayrımı, Agent/Customer etiketleme, timestamp, VAD, diarization ve container çalışması.
4. **Kontrollü araştırma dönemi:** A0–A7, D0–D7, P3–P7, frozen evaluation, paired karşılaştırma ve negatif transfer analizi.
5. **Veri üretim araştırması:** Çoklu ASR öğretmeni, audio-aware hakem ve seçici insan incelemesiyle pseudo-label üretimi.

Bu çizginin ana sonucu şudur:

> Türkçe telefon ASR başarısı tek başına model fine-tuning ile açıklanamaz. Kaynak decode, kanal ayrımı, segmentasyon, eğitim dağılımı, LoRA kapsamı, decode politikası, değerlendirme normalizasyonu ve artefakt bütünlüğü birlikte belirleyicidir.

---

# BÖLÜM I — KRONOLOJİ

## 4. 2025: İlk fine-tuning soruları ve kişisel veri denemeleri

### 4.1. Large-v2/large-v3’ü kişisel veriyle geliştirme

2025 yazı ve sonbaharında temel soru, Whisper large-v2 veya large-v3 modelinin kişisel Türkçe ses verileriyle daha iyi hâle getirilip getirilemeyeceğiydi.

Bu dönemde çıkarılan ilk dersler:

- LoRA bağımsız bir ASR modeli değil, mevcut Whisper ağırlıklarına eklenen bir adaptasyon katmanıdır.
- Belirli bir konuşmacı veya alan üzerinde base modelden daha iyi olabilir.
- Daha iyi sonuç; temel model, veri kalitesi, veri miktarı ve hiperparametrelerin ortak sonucudur.
- Tüketici GPU’larında tam fine-tuning yerine LoRA/PEFT daha uygulanabilirdir.
- Colab T4 sınıfı 16 GB GPU, büyük Whisper modellerinde LoRA için makul; tam fine-tune için sınırlıdır.

### 4.2. Large-v3, 1 epoch ve 2 epoch karşılaştırması

ChatGPT hafızasında 2025 Ağustos civarında, kullanıcının Whisper large-v3’ü kendi ses verileriyle fine-tune ettiği ve 1 epoch ile 2 epoch çıktılarını karşılaştırdığı kayıtlıdır.

Ancak erişilebilen hafızada:

- veri seti boyutu,
- kesin WER/CER,
- tam hiperparametreler,
- örnek çıktıların tamamı

korunmamıştır. Bu nedenle bu deney **C — konuşma hafızası** olarak tutulur ve sayısal bilimsel sonuç şeklinde yayımlanmaz.

Bu dönemden güvenle taşınabilen ders: epoch sayısı tek başına kalite göstergesi değildir; gerçek hedef ses üzerinde ayrı karşılaştırma gerekir.

### 4.3. ASR çıktısını anlamsal değerlendirme

2025 sonundaki downstream çalışmalarda, ASR çıktısının harf-harf veya katı regex eşleşmesiyle değerlendirilmesinin yetersiz olduğu görüldü.

Özellikle:

- kritik sayı veya süre doğru kaldığında küçük yazım hatalarının bütün çağrıyı başarısız saymaması,
- ASR bozulmasına toleranslı semantik değerlendirme,
- boş veya kullanılamaz transkriptin ayrı işaretlenmesi,
- LLM ile yapılandırılmış uygunluk/özet/aksiyon analizi

tercih edildi.

Bu yaklaşım WER’in yerine geçmez. WER/CER model ölçümüdür; semantik değerlendirme ise downstream iş değerini ölçer. İkisi ayrı tutulmalıdır.

---

## 5. 2026 Ocak: Whisper large-v2 LoRA ve ilk ciddi eğitim hattı

### 5.1. Eğitim yapılandırması

ChatGPT hafızasında korunan large-v2 LoRA yapılandırması:

| Alan | Değer |
|---|---|
| Base model | `openai/whisper-large-v2` |
| Veri | Yaklaşık 40.082 eğitim örneği, header’sız TSV |
| GPU | RTX A5000, yaklaşık 24 GB VRAM |
| Trainable parametre | 3.932.160 |
| Toplam parametre | 1.547.237.120 |
| Trainable oran | `%0,2541` |
| LoRA | `q_proj`, `v_proj` |
| Rank / alpha / dropout | `8 / 16 / 0.1` |
| Batch | `2` |
| Gradient accumulation | `8` |
| Learning rate | `3e-5` |
| Epoch | `3` tamamlandı; daha önce 4 planı da konuşuldu |
| Max target length | `384` |
| Dil/görev | Turkish / transcribe |
| Timestamp hedefi | `no_timestamps=True` |

Batch 8 denemesinde OOM görüldü. Eğitim daha küçük batch ve gradient accumulation ile çalıştı. GPU’nun tam yüke çıktığı, yaklaşık 8 GB VRAM kullandığı ve LoRA eğitiminde base modelin büyük bölümünün donmuş kaldığı doğrulandı.

### 5.2. Validation loss ve gerçek kalite ayrışması

Kaydedilen validation loss:

| Epoch | Validation loss |
|---|---:|
| 1 | `0.1558` |
| 2 | `0.1502` |
| 3 | `0.1488` |

Salt validation loss’a göre epoch 3 en iyi görünüyordu. Buna karşılık kullanıcının gerçek çağrı değerlendirmesinde:

- epoch 2 iyi,
- epoch 3 çok kötü

olarak tarif edildi.

Bu çelişki şu önemli dersi verdi:

> Validation loss düşebilirken hedef-domain WER, uzun-form güvenilirlik veya nitel çağrı kalitesi kötüleşebilir.

Olası nedenler:

- validation setinin hedef çağrıyı temsil etmemesi,
- epoch 3’te domain drift veya overfitting,
- inference promptunun eğitimle eşleşmemesi,
- uzun ses segmentasyonu ve decode farkları,
- transcript truncation veya max target ayarı,
- kritik sayı/isim hatalarının ortalama loss içinde görünmemesi.

Daha sonra epoch 2 adapterından `5e-6` learning rate ile bir ek epoch devam fikri önerildi. Bunun nihai artefakt sonucu mevcut hafızada doğrulanmamaktadır.

### 5.3. Aynı çağrıda model karşılaştırması

Aynı Türkçe finans çağrısı üzerinde üç çıktı karşılaştırıldı:

1. fine-tuned model,
2. Whisper large-v3,
3. Whisper large-v2.

Konuşma hafızasındaki genel sıralama:

1. **Whisper large-v3 — en iyi**
2. **Whisper large-v2 — ikinci**
3. **Fine-tuned model — en kötü**

Nitel gözlemler:

- large-v2 bir parasal ifadedeki negatif işareti ilk geçişte kaçırdı,
- arka plan gürültüsü olan bölgelerde anlamsız üretim arttı,
- özel kişi adları hatalı üretilebildi,
- large-v2 timestamp çıktısı kalite kontrolünü kolaylaştırdı,
- fine-tuned modelin daha kısa veya eksik çıktı üretmesi, hedef-domain dışı genelleme ve inference uyuşmazlığı şüphesi doğurdu.

Bu karşılaştırmanın özgün çağrı metni ve özel isimleri public depoda yayımlanmaz.

### 5.4. Uzun ses ve `max_target_positions` hatası

Uzun çağrı inference hattında görülen sorunlar:

- Whisper’ın yaklaşık 30 saniyelik bağlamı nedeniyle sesin tek generate çağrısında kesilmesi,
- 20–28 saniyelik chunk + yaklaşık 5 saniye overlap önerileri,
- overlap nedeniyle tekrar eden kelimeler,
- `max_new_tokens=768` kullanıldığında prompt uzunluğu ile birlikte modelin `max_target_positions=448` sınırının aşılması,
- eğitimde `no_timestamps=True` kullanılıp inference’ta aynı prompt politikasının korunmaması,
- explicit `decoder_input_ids` kullanımının prompt çatışması yaratabilmesi,
- `pad_token == eos_token` nedeniyle attention mask uyarısı.

Ana ders:

> Uzun sesi yalnız daha yüksek `max_new_tokens` ile çözmek doğru değildir. Segmentasyon, modelin maksimum hedef uzunluğu, timestamp promptu ve overlap bir bütün olarak tasarlanmalıdır.

---

## 6. 2026 Ocak: GB10 ARM64 ve runtime seçimi

NVIDIA GB10/AArch64 sisteminde:

- CUDA 13 ve uygun NVIDIA driver doğrulandı,
- Docker GPU passthrough çalıştı,
- güncel NGC PyTorch containerında `torch.cuda` çalıştı,
- eski container sürümlerinin GB10’u desteklemediği görüldü,
- CTranslate2/faster-whisper CUDA backend’i ARM64 + CUDA 13 + yeni GPU mimarisi hattında güvenilir çalışmadı.

Bu nedenle tercih:

- `openai-whisper` turbo veya
- Hugging Face Transformers Whisper

oldu.

Kullanıcı hız/kalite dengesi nedeniyle turbo’dan devam etmeyi seçti.

Bu deneyim daha sonra kontrollü ARGE hattındaki “plain Transformers Whisper, CTranslate2 yok” kısıtının teknik temelini oluşturdu.

---

## 7. 2026 Mart: I3R → WAV → ASR zincirinin olgunlaşması

### 7.1. Özel dosya biçimi

Üretim kayıtları doğrudan FFmpeg’in anlayacağı standart ses değildi. Uçtan uca akış:

```text
özel/encrypted I3R
→ üreticiye ait decoder executable
→ WAV
→ FFmpeg canonicalization
→ Whisper/WhisperX veya VibeVoice
→ transcript + log
```

Önemli hata:

- `.i3r` dosyasını doğrudan FFmpeg’e vermek `Invalid data found when processing input` benzeri hata üretebilir.

Doğru yaklaşım:

- dosyayı önce üretici aracına vermek,
- yerel geçici alanda decode etmek,
- modelin beklediği örnekleme hızı/kanal yapısına dönüştürmek,
- işlem sonunda geçici dosyaları silmek,
- her aşamanın başlangıç/bitiş/hata bilgisini loglamak.

### 7.2. Whisper ile VibeVoice örnekleme farkı

Ortak pipeline uyarlamalarında önemli bir ayrım görüldü:

- Whisper türevleri için 16 kHz mono standarttı.
- VibeVoice hattında modelin 24 kHz beklentisi bulundu.

Tek bir sabit `16 kHz` dönüşümünü bütün modellere uygulamak doğru değildir. Canonicalization hedef modele göre tanımlanmalıdır.

### 7.3. Pipeline hataları

Düzeltilen veya tespit edilen sorunlar:

- file-vs-directory girişinin karıştırılması,
- log yolunun yanlış kurulması,
- gerçek timestamp yerine uydurma sabit süreli segmentler üretilmesi,
- model akışını değiştirirken çalışan I3R ingest mantığının bozulması,
- ara dosyanın silinmemesi veya hata durumunda kalması.

Ana ders:

> Çalışan model kodunu yeniden yazmak yerine yalnız giriş adaptörünü değiştirmek daha güvenlidir.

---

## 8. 2026 Haziran: Stereo çağrı, konuşmacı rolü ve timestamp

### 8.1. Fiziksel kanal ayrımı

Çalışan stereo PoC’nin ana mantığı:

- ses tam olarak iki kanallı olmalı,
- `split_to_mono()` ile kanallar ayrılmalı,
- yapılandırılmış bir `AGENT_CHANNEL` seçimiyle roller eşlenmeli,
- iki kanal ayrı ayrı Whisper’dan geçirilmeli,
- segmentler başlangıç zamanına göre birleştirilmeli,
- JSON ve TXT çıktı üretilmeli.

İlk PoC varsayımları:

| Alan | Değer |
|---|---|
| Model | `openai/whisper-large-v2` |
| Dil | Turkish |
| Timestamp | Açık |
| Chunk | 30 saniye |
| Rol | Kanal konfigürasyonuna göre Agent/Customer |

Desteklenen giriş ailesi WAV, MP3, M4A, FLAC, OGG, AAC ve GSM gibi formatları kapsıyordu.

### 8.2. Neden kanal ayrımı diarization’dan önce gelir?

Kayıt fiziksel olarak taraflara ayrılmışsa:

- konuşmacı kimliği zaten kanal bilgisinde bulunur,
- diarization ek hata kaynağıdır,
- overlap yönetimi daha kolaydır,
- Agent/Customer rol eşlemesi deterministik olur.

Diarization şu durumlarda gerekir:

- mono kayıt,
- kanal sızıntısı,
- konferans/üçüncü kişi,
- kanal bilgisinin güvenilmez olması,
- aynı kanalda birden fazla konuşmacı.

Bu nedenle nihai ilke:

> Fiziksel kanal ayrımı varsa önce onu kullan; diarization’ı zorunlu varsayma.

### 8.3. Stereo-only ve RAM/tmpfs tasarımı

Daha sonra üretim containerı için şu kararlar alındı:

- yalnız stereo çağrılar işlenecek,
- mono kayıtlar ayrı bir iş akışına bırakılacak,
- upload, FFmpeg ve geçici sesler RAM/tmpfs üzerinde tutulacak,
- model GPU/VRAM üzerinde çalışacak,
- iş tamamlanınca geçici dosyalar silinecek,
- disk yalnız image ve model cache için kullanılacak.

Bu tasarım gizlilik, disk I/O ve geçici veri temizliği açısından avantajlıdır.

### 8.4. Timestamp bozulmasının kaynağı

Bir testte birleşmiş segment zamanlarının bozuk olduğu düşünüldü. Kanal birleştirme devre dışı bırakıldığında da sorun devam etti.

Sonuç:

- hata kanal merge’den değil,
- Hugging Face seq2seq pipeline içindeki `chunk_length_s=30` timestamp üretiminden geliyordu.

`chunk_length_s` kaldırılıp timestamp repair uygulandığında:

- 71 segment,
- 4 onarılmış segment,
- 0 şüpheli segment

raporlandı.

`return_timestamps="word"` çok ağır veya takılmaya yatkın bulundu; segment timestamp + repair daha uygulanabilir kaldı.

Ana ders:

> Timestamp hatasını konuşmacı birleştirme koduna yüklemeden önce tek kanal ham ASR çıktısı ayrı doğrulanmalıdır.

### 8.5. Transformers + diarization

GB10 üzerinde Transformers Whisper ve NeMo/pyannote tabanlı diarization hattı çalıştırıldı. Pratik sonuçlar:

- saf Transformers yeni GPU mimarisinde daha güvenilir runtime oldu,
- diarization bağımlılıkları inference’tan ayrı hata alanı oluşturdu,
- batch klasör işleme ihtiyacı doğdu,
- alan terimleri için model vocabulary’sini değiştirmek yerine prompt/context bias veya kontrollü post-normalization daha düşük riskliydi.

---

## 9. 2026 Haziran: Üretim ve performans tecrübeleri

Kamuya açık biçimde taşınabilen genel deneyimler:

- yaklaşık 20 saniyelik bir ses parçası GB10 üzerinde yaklaşık 1 saniye civarında transkribe edilebildi,
- transcriber containerının RAM kullanımı uzun çalışmada büyüyebildi,
- dolmuş swap ve eski worker durumu gecikme/hata üretebildi,
- restart sonrasında RAM düşüşü gözlendi,
- gateway/API zincirinde 500 hataları yalnız modelden değil dosya biçimi, geçici dosya, request alanı ve downstream servislerden kaynaklanabildi,
- GPU hızlı olsa bile CPU, RAM, temp dosyası ve ağ zinciri toplam gecikmeyi belirler.

Yayın ilkesi:

- model inference süresi,
- API toplam süresi,
- dosya dönüşüm süresi,
- queue/bekleme süresi

ayrı ölçülmelidir.

---

# BÖLÜM II — LEGACY AÇIK VERİ DENEYLERİ

## 10. Legacy veri kaynakları

İlk kapsamlı açık veri çalışmasında kullanılan başlıca kaynaklar:

| Veri | Kullanım |
|---|---|
| Common Voice 17 TR Fixed | Genel/crowd read speech |
| MediaSpeech TR | Medya, interview ve daha doğal konuşma proxy’si |
| FLEURS TR | Dış-domain benchmark |
| Khan Academy Turkish | Eğitim/anlatım dış doğrulama |
| Khan Academy Turkish Math | Terimli dış doğrulama |

Karma genel eğitim seti yaklaşık 27,84 saat; balanced-phone seti yaklaşık 24,01 saatti.

Legacy sonuçlarının özgün checkpoint ve prediction arşivinin bir bölümü daha sonra diskte bulunamadı. Bu nedenle bu seri **B — arşiv raporu doğrulamalı** kabul edilir.

---

## 11. Legacy-H0 — Base large-v3-turbo

Base `openai/whisper-large-v3-turbo`, bütün legacy fine-tune denemelerinin referansı oldu.

MediaSpeech testinde:

- raw WER: `0.4255`
- normalized WER: `0.1558`

Bu büyük fark, Türkçe ASR’de noktalama, büyük/küçük harf ve yüzey biçiminin raw WER’i ciddi biçimde şişirebildiğini gösterdi.

---

## 12. Legacy-H1 — MediaSpeech-only LoRA

Yalnız MediaSpeech üzerinde 1 epoch LoRA:

| Model | Normalize WER | Normalize CER |
|---|---:|---:|
| Base | `0.1558` | `0.0916` |
| MediaSpeech LoRA | `0.2162` | `0.1495` |

Göreli WER değişimi yaklaşık `%38,8` kötüleşmeydi.

Karar:

- başarısız,
- aynı biçimde tekrar edilmemeli,
- “daha hedefe yakın Türkçe veri = otomatik iyileşme” varsayımını reddeden negatif kontrol.

Olası nedenler:

- az veri,
- transcript normalizasyonu,
- eğitim/test dağılımı farkı,
- yüksek learning rate veya rank/kapasite dengesi,
- veri çeşitliliğinin yetersizliği.

---

## 13. Legacy-H2 — General Turkish LoRA

Common Voice + MediaSpeech ile 2 epoch hedeflendi; ancak eğitim yaklaşık `global_step=750`, `epoch≈0,42` seviyesinde kesildi.

Bu nedenle “2 epoch tamamlandı” şeklinde raporlanmamalıdır.

Hızlı test:

| Domain | Base WER | General ckpt-750 WER |
|---|---:|---:|
| Common Voice | `0.1837` | `0.1368` |
| MediaSpeech | `0.1601` | `0.1718` |

Sonuç:

- Common Voice iyileşti,
- MediaSpeech kötüleşti,
- toplam veri miktarından çok örnekleme dağılımı belirleyici oldu.

---

## 14. Legacy-H3 — Balanced-phone continuation

General checkpoint üzerinden ikinci aşama:

| Alan | Değer |
|---|---|
| Eğitim örneği | 14.606 |
| Süre | 24,01 saat |
| Learning rate | `5e-6` |
| Global step | 913 |
| Veri dengesi | Common Voice azaltıldı, MediaSpeech artırıldı |
| Augmentasyon | Telefon bandı + noise/gain |

Hızlı test sonucu:

| Domain | Base | General | Balanced-phone |
|---|---:|---:|---:|
| Common Voice | `0.1837` | `0.1368` | `0.1241` |
| MediaSpeech | `0.1601` | `0.1718` | `0.1366` |

Bu aşama, eğitim dağılımına yakın testte hem Common Voice hem MediaSpeech tarafında en iyi sonucu verdi.

Ancak dış doğrulama:

| Model | External360 normalize WER |
|---|---:|
| Base | `0.0857` |
| MediaSpeech LoRA | `0.0853` |
| General LoRA | `0.0957` |
| Balanced-phone | `0.1018` |

Balanced-phone, temiz dış-domain sette base’e göre yaklaşık `%18,7` kötüleşti.

Ana ders:

> Hedef-domain kazancı ile genel-domain kaybı aynı anda gerçekleşebilir.

---

## 15. Legacy-H4 — Repeat-safe decode

9 dakikadan uzun telefon örneğinde ilk balanced-phone decode, “ama ama” benzeri tekrar döngüsü üretti.

Repeat-safe profil:

```text
no_repeat_ngram_size = 4
repetition_penalty = 1.08
chunk_s = 25
```

Yaklaşık 9:06’lık referans bölümünde:

| Çıktı | Normalize WER |
|---|---:|
| Balanced-phone ilk decode | `0.8469` |
| Balanced-phone repeat-safe | `0.6466` |
| Faster-Whisper turbo + VAD | `0.6568` |

Repeat-safe aynı modelde yaklaşık `%23,7` göreli iyileşme sağladı.

Bu deneyin en önemli sonucu:

> Yanlış decode politikası, iyi adapterın kazancını tamamen örtebilir.

Referans transcript gürültülü olduğu için mutlak WER dikkatle yorumlanmalıdır; göreli karşılaştırma daha güvenilirdir.

---

# BÖLÜM III — KONTROLLÜ A0–A7 SERİSİ

## 16. Kontrollü araştırma ilkeleri

Yeni seri şu koşulları sabitledi:

- plain Hugging Face Transformers Whisper,
- base `openai/whisper-large-v3-turbo`,
- PEFT/LoRA,
- RTX 4070 SUPER yaklaşık 12 GB,
- D3 decode profili,
- ortak frozen evaluation,
- raw ve normalized WER/CER,
- prediction JSONL ve SHA-256,
- checkpoint 50/100/150/200,
- checkpoint/dataset bazında resumable evaluation,
- aynı GPU’da tek worker,
- negatif sonuçların korunması,
- CTranslate2/faster-whisper kullanılmaması.

Frozen evaluation paneli:

- MediaSpeech Clean,
- MediaSpeech Phone,
- MediaSpeech G.711,
- CV Scripted,
- FLEURS,
- CV Spontaneous,
- TSC.

Telefon paneli ile genel Türkçe paneli ayrı yorumlandı.

---

## 17. A0 — Kontrollü base

Normalize WER:

| Set | A0 |
|---|---:|
| MediaSpeech Clean | `0.16255` |
| Phone | `0.17568` |
| G.711 | `0.14574` |
| Robustness proxy | `0.16163` |
| CV Scripted | `0.15560` |
| FLEURS | `0.10288` |

A0 yalnız “eğitimsiz model” değil, bütün adaptasyonların guardrail referansıydı.

---

## 18. A2 — Encoder+decoder Q/V LoRA

Yapı:

- encoder+decoder `q_proj/v_proj`,
- rank 16,
- alpha 32,
- dropout 0.05.

Sonuç:

| Set | A2 |
|---|---:|
| Clean | `0.13823` |
| Phone | `0.17082` |
| G.711 | `0.13893` |
| Robustness | `0.14655` |
| CV Scripted | `0.15369` |
| FLEURS | `0.17693` |

A2:

- hedef proxy’lerde iyileşti,
- FLEURS’te ciddi regresyon oluşturdu,
- production’a alınmadı,
- A7 için parent adapter oldu.

---

## 19. A3 — Encoder-only + `%10` replay

Yapı:

- encoder-only Q/V,
- rank 16,
- 200 optimizer step,
- 3.200 microbatch,
- `%90` acoustic + `%10` clean replay.

En iyi hedef-domain checkpoint step-50 idi.

- Phone yaklaşık `0.157342`,
- robustness kazancı istatistiksel olarak desteklendi,
- CV Scripted step-50 `0.23532` oldu,
- sonraki checkpointlerde CV Scripted hâlâ `0.219–0.229` bandında kaldı.

A0 CV Scripted `0.15560` olduğundan replay genel-domain korumasına yetmedi.

Terminal karar:

```text
A3_V2_NO_PROMOTABLE_CHECKPOINT
```

Ana ders:

> Replay’in varlığı değil, oranı, kaynak çeşitliliği ve eğitim schedule’ı önemlidir.

---

## 20. A4 — Decoder-only zero replay

Yapı:

- decoder-only Q/V,
- rank 16,
- zero replay,
- temiz veri ayrımı.

En iyi sonuçlar:

- Phone step-50: `0.158385`
- robustness step-200: yaklaşık `0.1441`

A4, Phone’da A7’den sonra güçlü aday; robustness tarafında ise en güçlü Pareto adaylarından biri olarak kaldı.

Schedule auditinde 52 empty-target exposure bulundu. Bu durum raporlandı; ancak geniş performans deseninin tek açıklaması olarak kullanılmadı.

---

## 21. A5 — Encoder-only temiz schedule

A5/A6 için 7 boş transkript çıkarıldı.

Temiz train manifesti:

- 172.231 satır,
- validation 9.081.

En iyi sonuçlar:

- Phone step-100: yaklaşık `0.1580`
- robustness step-50: yaklaşık `0.1475`

A5 hedef alanı iyileştirdi; A4 robustness seviyesini geçemedi.

---

## 22. A6 — Encoder+decoder temiz schedule

A6, A5 ile matched veri ve schedule üzerinde encoder+decoder kapsamını test etti.

En iyi sonuçlar:

- Phone step-200: `0.157203`
- robustness step-200: yaklaşık `0.1448`

İlk analizde A5 ve A6’nın bütün metriklerde aynı olduğu raporlandı. Bunun nedeni analiz scriptindeki path replacement hatasıydı; A6 yanlışlıkla kendisiyle karşılaştırılmıştı.

Düzeltme sonrasında:

- 4.059 prediction farklı,
- 27/28 aggregate metric farklı

bulundu.

Eski sonuç:

```text
SUPERSEDED_DUE_TO_REFERENCE_PATH_BUG
```

olarak işaretlendi.

Ana ders:

> Deney yolu string replacement ile üretilmemeli; kaynak ve aday path’leri açık yapılandırma alanları olmalıdır.

---

## 23. A7 — Staged source-anchored balanced-phone integration

A7, A2 parent adapterından devam etti.

Yapı:

- encoder+decoder Q/V,
- rank 16, alpha 32, dropout 0.05,
- learning rate `5e-6`,
- 200 optimizer step,
- 3.200 occurrence,
- TSC unchanged source anchor,
- MediaSpeech + CV Spontaneous phone-like kaynaklar,
- phone-band,
- `0.75x` speed,
- noise/gain,
- phone-band + noise/gain.

Schedule:

| Bucket | Occurrence |
|---|---:|
| TSC unchanged anchor | 1.067 |
| Phone-like unchanged | 640 |
| Phone-band | 640 |
| Speed 0.75 | 320 |
| Noise/gain | 267 |
| Phone-band + noise/gain | 266 |

### 23.1. Peak guard

Augmentasyon policy üç aşamada olgunlaştı:

- **V1:** clipping oluştu.
- **V2:** noise/gain düzeldi; phone-band resampling overshoot kaldı.
- **V3:** universal peak guard yalnız augmented bucketlara uygulandı.

V3 audit:

- 1.493/1.493 occurrence geçti,
- finite,
- non-silent,
- deterministic,
- maksimum peak yaklaşık `0.9800000191`,
- noise SNR farkı `0.0 dB`.

### 23.2. Eğitim kesintisi ve resume

A7 worker bağlı terminal kapanınca eğitim kesildi. Step-50/100/150 checkpointleri oluşmuştu.

Sorun zinciri:

- step-150 ağırlığıyla schedule step-170’ten yanlış devam denemesi,
- stale step-200 klasörü,
- checkpoint overwrite hatası,
- adapter klasörünü dosya gibi hashlemeye çalışıp `PermissionError` üretme,
- exact optimizer state bulunmaması.

Final çözüm:

- kaynak step-150,
- schedule index 2400,
- global step 151,
- 50 optimizer step,
- izole run dizini,
- `ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET`,
- final 200/200 step ve 3.200/3.200 schedule.

Final adapter SHA:

```text
fa5aa88e3d7fd1c16b7b7cdb0c516bc7d49210f3c5cb63c8405f280bad9e4894
```

### 23.3. A7 sonucu

- En iyi Phone: step-200, `0.154285`
- En iyi A7 robustness: step-150, `0.147578`

Phone karşılaştırması:

| Model | Phone WER |
|---|---:|
| A2 | `0.170825` |
| A4 | `0.158385` |
| A6 | `0.157203` |
| **A7** | **`0.154285`** |

A7:

- kontrollü seride en iyi Phone sonucunu verdi,
- CV Scripted’da A0/A2’ye göre maliyet üretti,
- staged adaptation hipotezini destekledi,
- augmentasyonun bağımsız nedensel katkısını kanıtlamadı.

Bilimsel sınıf:

```text
staged_domain_adaptation_supported
staged_domain_adaptation_with_general_domain_cost
augmentation_contribution_inconclusive
OPEN_DATA_EXPERIMENT_LINE_COMPLETED
```

---

# BÖLÜM IV — DECODING, ITN, N-BEST VE MEMORY

## 24. D0–D7 decoding araştırması

Kontrollü decoding çalışmasında D3 desteklenen profil oldu.

- D3 normalized WER: `0.156021`

Diğer profiller evrensel üstünlük göstermedi. D3 frozen evaluation’ın ortak decode profili olarak sabitlendi.

Bazı erken state kayıtlarında D0–D7 “immutable manifest yok” gerekçesiyle BLOCKED görünürken, daha sonraki execution eventleri D0–D7’nin PASSED tamamlandığını gösterdi. Bu, stale/ön-koşu state kayıtlarının terminal sonuç sanılmaması gerektiğini gösterir.

---

## 25. P3–P6 kalite ve ikinci geçiş deneyleri

### P4 — İkinci decode

İkinci pass tetik koşulu değerlendirme örneklerinde devreye girmedi.

Karar:

- ek bilgi kazanımı yok,
- üretim için gerekçelendirilmedi.

### P5 — Deterministic ITN

Güvenli ve deterministik biçimde dönüştürülebilecek sayı/tarih örneği bulunmadı.

Karar:

- koşulsuz ITN uygulanmadı,
- yanlış dönüşüm riskine karşı reddedildi.

### P6 — N-best

Runtime gerçek ve farklı hipotezlerden oluşan n-best üretmedi.

Karar:

- sahte n-best üzerinden rescoring yapılmadı,
- “beam çıktısı var” ile “kullanılabilir n-best çeşitliliği var” ayrımı korundu.

---

## 26. P7 memory benchmark

32 örneklik benchmarkta:

| Profil | Speedup | Prediction equal | Normalized WER | Karar |
|---|---:|---:|---:|---|
| MEM0 | `0%` | Evet | `0.156021` | Canonical |
| MEM1 | `%5,59` | Evet | `0.156021` | Küçük kazanç |
| MEM2 | `%32,12` | Evet | `0.156021` | Microbenchmark pozitif; production’a alınmadı |
| MEM3 | `%57,27` | Hayır | `0.157068` | Reddedildi |
| MEM4 | `%60,07` | Hayır | `0.157068` | Reddedildi |

### 26.1. MEM2 hakkında kayıt uyuşmazlığı

Ham benchmark artefaktı MEM2 için:

- aynı prediction hash,
- `%32,12` hızlanma,
- aynı WER

raporluyor.

Buna karşılık proje handoff notunda “MEM2 anlamlı hız kazancı sağlamadı” ve canonical profilin MEM0 kalacağı yazıldı.

Bu iki kayıt şu şekilde uzlaştırılmalıdır:

- MEM2 küçük, sıcak-cache ve 32 örneklik benchmarkta olumlu görünmektedir.
- Bunun production/frozen evaluation kapsamına taşınmasını doğrulayan geniş artefakt veya karar gerekçesi korunmamıştır.
- Bu nedenle MEM2 “başarısız” değil, **microbenchmark-positive / deployment-inconclusive** olarak sınıflandırılır.
- Bilimsel karşılaştırılabilirlik için MEM0 korunmuştur.

### 26.2. MEM3/MEM4

Batch 3 ve batch 6 profilleri ciddi hızlandı; fakat prediction hash değişti.

Bu nedenle:

> Hız kazancı, çıktı eşitliği bozuluyorsa aynı model koşulu sayılmaz.

MEM3/MEM4 kontrollü değerlendirme için elendi.

---

# BÖLÜM V — VERİ, SES VE DEĞERLENDİRME DERSLERİ

## 27. Ses dönüşümünde öğrenilenler

### İşe yarayanlar

- Özel formatı üretici decoderıyla yalnız bir kez açmak.
- Özgün kaynağı immutable tutmak.
- `ffprobe` ile codec, sample rate, channel ve duration doğrulamak.
- Whisper için tek kontrollü 16 kHz dönüşüm yapmak.
- Gerçek stereo tarafları mono karıştırmadan önce ayırmak.
- Her aşamanın hash ve config bilgisini tutmak.
- Augmentasyon sonrası finite/non-silent/peak audit yapmak.

### İşe yaramayan veya riskli olanlar

- `.wav` uzantısını gerçek PCM kalitesi sanmak.
- 8 kHz kaydı 48 kHz’e çıkarınca bilgi kazanıldığını düşünmek.
- `asetrate` ile gerçek resampling’i karıştırmak.
- art arda gereksiz resampling yapmak.
- iki farklı tarafı erken mono downmix etmek.
- bütün kayıtları aynı agresif denoise zincirinden geçirmek.
- iç sessizlikleri fiziksel olarak silip zaman çizelgesini bozmak.

---

## 28. VAD ve segmentasyon

Legacy uzun çağrı testinde:

- VAD’siz Transformers turbo WER: `1.1772`
- VAD’li turbo WER: `0.6568`

Bu farkın tamamı yalnız VAD’ye atfedilemez; runtime ve decode koşulları da farklıdır. Yine de uzun formda segmentasyonun etkisi model fine-tuning kadar büyük olabilir.

VAD ayarında kritik riskler:

- “evet”, “yok”, “bir”, “tamam” gibi kısa kelimeleri silmek,
- düşük enerjili ilk/son fonemleri kesmek,
- overlap ve turn boundary’lerini bozmak,
- silence removal ile orijinal timeline’ı kaybetmek.

Doğru ölçüm:

- WER/CER,
- boundary deletion,
- speech recall,
- kısa utterance recall,
- hallucination/repetition,
- işlenen ses süresi.

---

## 29. Türkçe normalizasyon

Raw ve normalized WER birlikte raporlanmalıdır.

Üç metin katmanı yararlıdır:

1. **Ham/verbatim transcript:** Denetim ve dilbilim.
2. **Kanonik ASR transcript:** Eğitim ve WER.
3. **Sunum transcript:** ITN, noktalama ve son kullanıcı.

Aynı normalizer referans ve hipoteze uygulanmalıdır.

Sayıları doğrudan rakama çevirmek her zaman doğru değildir. Öğrenci ASR için duyulan surface form ile downstream entity-normalized alan ayrı tutulmalıdır.

---

## 30. Veri dağılımı ve negatif transfer

Bütün deney çizgisinde tekrar eden sonuç:

- Common Voice ağırlığı Common Voice’u iyileştirebilir,
- MediaSpeech ağırlığı doğal konuşmayı iyileştirebilir,
- telefonlaştırma Phone setini iyileştirebilir,
- aynı değişiklik FLEURS/CV Scripted/TSC gibi genel setleri bozabilir.

Bu nedenle tek makro skor kullanılmamalıdır.

Önerilen iki panel:

### Telefon/karşılıklı konuşma paneli

- Phone,
- G.711,
- robustness proxy,
- CV Spontaneous,
- kısa utterance ve deletion,
- tekrar/hallucination.

### Genel Türkçe izleme paneli

- Clean,
- CV Scripted,
- FLEURS,
- TSC.

---

# BÖLÜM VI — DOWNSTREAM VE PSEUDO-LABEL ARAŞTIRMASI

## 31. LLM ile semantik transcript değerlendirmesi

ASR çıktıları daha sonra local LLM ile:

- semantik uygunluk,
- çağrı özeti,
- kritik bilgi,
- eksik aksiyon,
- transcript kullanılabilirliği,
- yapılandırılmış JSON

üretmek için kullanıldı.

Önemli tasarım ilkeleri:

- katı regex yerine ASR toleranslı semantik karşılaştırma,
- kritik sayı/süre korunmuşsa küçük yazım hatasını aşırı cezalandırmama,
- boş veya bozuk transcripti ayrı kalite alanıyla işaretleme,
- ASR hatasını LLM’nin sessizce “uydurmasına” izin vermeme,
- kaynak transcript ile normalize downstream alanını ayırma.

Bu, ASR model başarısını ölçmez; ASR çıktısının iş akışındaki kullanılabilirliğini ölçer.

---

## 32. Audio-aware pseudo-label mimarisi — araştırıldı, uygulanmadı

Bu çalışma hattı **R — araştırıldı, uygulanmadı** sınıfındadır.

Araştırılan öneri:

```text
stereo kanal ayrımı
→ VAD/turn segmentation
→ birincil ASR öğretmeni
→ ikinci Whisper öğretmeni
→ öğretmen uyuşmazlık skoru
→ yalnız riskli span’de audio-aware hakem
→ Türkçe forced alignment
→ confidence-gated insan incelemesi
→ filtrelenmiş student verisi
```

Önerilen roller:

- Qwen3-ASR-1.7B: birincil öğretmen,
- Whisper large-v3-turbo/large-v3: çeşitlilik sağlayan ikinci öğretmen,
- Qwen3-Omni Instruct: yalnız uyuşmazlık span’lerinde audio-aware hakem,
- WhisperX + Türkçe CTC aligner: word alignment,
- insan: yalnız düşük güvenli span’ler.

Ana araştırma sonucu:

- tam otonom insan eşdeğeri label garanti edilemez,
- multi-teacher agreement ve seçici insan düzeltmesi gerçekçi,
- daha çok pseudo-label yerine daha temiz ve filtrelenmiş pseudo-label daha değerlidir,
- surface transcript ile normalized entity ayrı alanlar olmalıdır,
- clean replay veya adapter routing negatif transferi sınırlamak için gereklidir.

Bu mimari henüz mevcut A0–A7 sonuçlarının parçası değildir.

---

## 33. Araştırılan fakat çalıştırılmayan diğer yöntemler

| Yöntem | Durum | Not |
|---|---|---|
| AdaLoRA | R | Düşük VRAM için ilginç; özel update schedule gerekir |
| DoRA | R | Düşük rankta potansiyel; ASR kanıtı LoRA’dan zayıf |
| q/k/v/out geniş LoRA | R | Kapasite artar; VRAM ve overfit riski |
| SpecAugment | R | Waveform codec bozulmasının yerine geçmez |
| External LM / shallow fusion | R | Gerçek n-best ve dev tuning gerekir |
| Text-only adaptation | R | Alan metni varsa değerlidir |
| Target-speaker prompt | R | Overlap/meeting için güçlü literatür sinyali |
| Calm-Whisper tarzı head tuning | R | Non-speech hallucination için araştırma adayı |
| Conformer/CNN adapter | R | Yüksek mimari risk ve yeniden eğitim maliyeti |
| Distillation/speculative decode | R | Üretim throughput için gelecekte değerlendirilebilir |
| Pseudo-label noisy student | R | Kalite filtreleme olmadan riskli |

Bu yöntemler “denendi ve başarısız oldu” şeklinde yazılmamalıdır.

---

# BÖLÜM VII — YÖNTEM KARAR MATRİSİ

## 34. Denenen yöntemlerin toplu sınıflandırması

| Yöntem | Kanıt | Sonuç | Neden / ders |
|---|---|---|---|
| Vendor decoder ile I3R açma | C/A pipeline | Başarılı | FFmpeg özel/encrypted formatı doğrudan okuyamaz |
| Tek canonical resampling | C/B | Başarılı | Gereksiz dönüşüm artefaktını azaltır |
| Stereo kanal split | C | Başarılı | Fiziksel rol bilgisi diarization’dan güvenilir |
| Erken mono downmix | C/R | Reddedildi | Agent/Customer ve overlap bilgisi kaybolur |
| HF `chunk_length_s=30` timestamp | C | Sorunlu | Seq2seq timestamp bozulması üretildi |
| Segment timestamp repair | C | Başarılı | 71 segmentte 4 repair, 0 suspicious |
| Word timestamps | C | Operasyonel olarak ağır | Hang/timing maliyeti |
| VAD’siz uzun form | B | Başarısız | Tekrar/hallucination ve yüksek WER |
| VAD + segmentasyon | B/C | Başarılı | Uzun form güvenilirliği ciddi arttı |
| Overlap chunking | C | Sınırlı | Sınır korur; tekrar üretir |
| Large-v2 LoRA 3 epoch | C | Sınırlı/başarısız hedef test | Loss düştü, gerçek kalite epoch3’te bozuldu |
| MediaSpeech-only LoRA | B | Başarısız | WER `0.1558→0.2162` |
| General Turkish LoRA | B | Domain-bağımlı | CV iyi, MediaSpeech kötü |
| Balanced-phone continuation | B | Hedefte başarılı | Dış clean sette negatif transfer |
| Repeat-safe decode | B | Başarılı | `0.8469→0.6466` |
| A2 encoder+decoder | A | Hedefte başarılı, FLEURS maliyet | A7 parent oldu |
| A3 encoder-only + replay | A | Bilimsel negatif | Replay CV Scripted’ı korumadı |
| A4 decoder-only | A | Güçlü Pareto adayı | Phone ve robustness güçlü |
| A5 encoder-only clean | A | Sınırlı fayda | A4 robustness’ı geçmedi |
| A6 encoder+decoder clean | A | Sınırlı | Daha geniş scope otomatik sinerji vermedi |
| A7 staged adaptation | A | Başarılı | En iyi Phone; genel-domain maliyet |
| Phone-band | A/B | Entegrasyonda faydalı olabilir | Bağımsız katkı ayrıştırılmadı |
| Speed 0.75 | A/C | Faydalı sinyal | A7 içinde; tek başına causal kanıt yok |
| Noise/gain | A/B | Sınırlı/entegre | Clipping kontrolü şart |
| Universal peak guard | A | Başarılı | Augmentasyon güvenliğini sağladı |
| D3 decoding | A | Canonical | nWER `0.156021` |
| P4 second decode | A | Faydasız | Tetiklenmedi |
| P5 deterministic ITN | A | Reddedildi | Güvenli dönüşüm bulunmadı |
| P6 n-best | A | Uygulanamadı | Gerçek hipotez çeşitliliği yok |
| MEM1 | A | Küçük hız kazancı | Prediction eşit |
| MEM2 | A | Inconclusive deployment | Microbenchmarkta `%32,12`, production kararı yok |
| MEM3/MEM4 | A | Reddedildi | Batch predictionı değiştirdi |
| LLM semantic QA | C | Downstream başarılı yaklaşım | WER değil, kullanım değeri ölçer |
| Audio-aware pseudo-label | R | Araştırma önerisi | Henüz çalıştırılmadı |

---

# BÖLÜM VIII — OPERASYONEL DERSLER

## 35. Worker ve deney yönetimi

İşe yarayan düzen:

```text
manifest/config preflight
→ 2-step smoke
→ bağımsız worker
→ PID + stdout/stderr + progress
→ checkpoint audit
→ ayrı frozen evaluation worker
→ prediction hash ve metric recomputation
```

İşe yaramayan düzen:

- aynı GPU’da birden fazla eğitim workerı,
- tek Codex görevinde bütün frameworkü sıfırdan yazdırmak,
- state dosyasını gerçek process durumu sanmak,
- progress artmıyor diye workerı kör biçimde yeniden başlatmak,
- stale checkpoint klasörüne yazmak,
- optimizer ağırlığı ve schedule konumunu farklı adımlardan resume etmek,
- Codex’e sık polling yaptırmak,
- terminal penceresinin görünürde boş olduğu için kapatılması.

---

## 36. Checkpoint ve resume

Doğru ilkeler:

- checkpoint model dosyasını hashlemek, klasörü değil,
- adapter config ve model SHA’yı ayrı tutmak,
- schedule index, global step ve kaynak checkpointi birlikte kaydetmek,
- exact optimizer state yoksa resume türünü açıkça yazmak,
- stale output dizininden kaçınmak için izole run kullanmak,
- checkpoint lock ve final progressi doğrulamak,
- atomic save kullanmak.

A7’nin optimizer-reset continuation olması saklanmamalıdır.

---

## 37. Analiz ve yazılım hataları

Kaydedilen önemli hatalar:

- A5–A6 self-comparison path bugı,
- eski sahte zero-delta sonucu,
- stale PID/state,
- directory hashing `PermissionError`,
- yanlış schedule-weight resume,
- stale step-200 overwrite çakışması,
- eksik attention mask,
- prompt/timestamp uyuşmazlığı,
- 448 token sınırını aşan `max_new_tokens`,
- timestamp merge yerine ASR timestamp üretiminin suçlu çıkması.

Ana ders:

> Sonuç tablosu tek başına kanıt değildir. Kaynak prediction, config, checkpoint ve script path’i doğrulanmalıdır.

---

# BÖLÜM IX — BUGÜNKÜ NİHAİ DURUM

## 38. Ne gerçekten işe yaradı?

En güçlü doğrulanmış sonuçlar:

1. **A7 staged domain adaptation:** En iyi kontrollü Phone WER `0.154285`.
2. **A4 decoder-only:** Robustness tarafında güçlü Pareto adayı.
3. **Repeat-safe decode:** Uzun legacy çağrıda çok büyük göreli kazanç.
4. **VAD/segmentasyon:** Uzun form güvenilirliğini model kadar etkiledi.
5. **Stereo kanal ayrımı:** Rol etiketini deterministic hâle getirdi.
6. **D3 + deterministic evaluation:** Karşılaştırılabilir decode temeli sağladı.
7. **Raw + normalized WER/CER:** Yüzey biçimi ile gerçek ASR hatasını ayırdı.
8. **Prediction-level hash ve recomputation:** A5–A6 hatasını yakaladı.
9. **Source anchor + staged continuation:** A2’yi Phone’da belirgin geçti.
10. **Augmentasyon peak guard:** Clipping ve overshoot’u kontrol altına aldı.

---

## 39. Ne işe yaramadı veya reddedildi?

1. MediaSpeech-only LoRA.
2. “Daha fazla epoch her zaman daha iyi” varsayımı.
3. `%10` replay’in genel-domain forgetting’i otomatik önleyeceği varsayımı.
4. Daha geniş encoder+decoder scope’un otomatik sinerji vereceği varsayımı.
5. VAD’siz uzun form.
6. Decode koşullarını eşitlemeden model karşılaştırmak.
7. Gerçek n-best olmadan rescoring.
8. Güvenli örnek olmadan deterministic ITN.
9. Prediction değiştirerek hızlanan MEM3/MEM4 batching.
10. State dosyasına tek başına güvenmek.

---

## 40. Ne hâlâ belirsiz?

- A7’de phone-band, speed, noise/gain ve source anchor’ın bağımsız katkısı.
- MEM2’nin geniş üretim yükünde gerçek değeri.
- Gerçek insan doğrulanmış iki kanallı telefon setinde A4 ve A7 sıralaması.
- Bankacılık sayı/tutar/tarih/isim hata profili.
- Pseudo-label öğretmen komitesinin Türkçede insan emeğini ne kadar azaltacağı.
- LoRA adapter routing’in gerçek production avantajı.
- Gerçek multi-seed belirsizliği.

---

## 41. Kamuya açık nihai yorum

Bu deney geçmişi şu iddiayı destekler:

> Türkçe telefon-benzeri açık veri proxy’sinde staged domain adaptation, Whisper large-v3-turbo Phone WER’ini iyileştirmiştir. Bununla birlikte genel Türkçe domainlerde negatif transfer oluşmuştur. Model eğitimi kadar kaynak decode, stereo kanal ayrımı, VAD, decoding, normalizasyon ve artefakt doğrulaması da belirleyicidir.

Desteklenmeyen iddialar:

- A7 gerçek şirket çağrılarında kanıtlanmış en iyi modeldir.
- Telefon augmentasyonunun tek başına etkisi kanıtlanmıştır.
- Tek adapter bütün Türkçe konuşmada üstündür.
- Pseudo-label mimarisi üretimde denenmiştir.
- Eski conversation-memory deneyleri bit-for-bit yeniden üretilebilirdir.

---

## 42. İlgili belgeler

- [Pratik araştırma rehberi](practical_research_guide.md)
- [Tam araştırma raporu](full_research_report.md)
- [Deney kataloğu](experiment_catalog.md)
- [Negatif sonuçlar](negative_results.md)
- [Yeniden üretilebilirlik](reproducibility.md)
- [Çağrı odaklı değerlendirme](call_oriented_evaluation.md)
- [Araştırılan ve çalıştırılan yöntem matrisi](research_vs_executed_matrix.md)
- [Whisper deneyim zaman çizelgesi](whisper_experience_timeline.md)
- [ChatGPT hafızası kapsam ve redaksiyon notu](chatgpt_memory_provenance.md)

---

## 43. Terminal araştırma kararı

```text
OPEN_DATA_EXPERIMENT_LINE_COMPLETED
```

Bu karar, Whisper üzerine artık hiçbir çalışma yapılamayacağı anlamına gelmez. Yalnız mevcut açık-veri A0–A7 deney hattının tamamlandığını; bundan sonraki iddiaların yeni veri, yeni hipotez veya gerçek hedef-domain doğrulaması gerektirdiğini belirtir.
