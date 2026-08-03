# Yayın ve Paylaşım Paketi

Bu sayfa, araştırmayı GitHub dışındaki akademik veya teknik platformlarda paylaşmak için hazır metinler sunar.

## Başlık

**Türkçe Telefon-Benzeri Konuşmalar için Whisper Large-v3-Turbo Uyarlaması: LoRA Kapsamı, Staged Domain Adaptation, Telefon Augmentasyonu ve Negatif Transfer**

## English title

**Adapting Whisper Large-v3-Turbo for Turkish Telephone-Like Speech: LoRA Scope, Staged Domain Adaptation, Telephone Augmentation, and Negative Transfer**

---

## Türkçe öz

Bu çalışma, `openai/whisper-large-v3-turbo` modelinin Türkçe telefon-benzeri ve karşılıklı konuşma koşullarına uyarlanmasını inceler. Araştırma, tarihsel Legacy deneyler ile ortak frozen evaluation altında yürütülen kontrollü A0–A7 serisini birleştirir. Encoder-only, decoder-only ve encoder+decoder LoRA kapsamları; replay, temiz schedule, parent-adapter continuation, kaynak ankrajı, telefon bandı, hız ve noise/gain augmentasyonları karşılaştırılmıştır. En iyi kontrollü MediaSpeech Phone sonucu, A2 adapterından staged continuation ile geliştirilen A7 step-200 tarafından `0.1542845` normalized WER olarak elde edilmiştir. A7, A2 (`0.170825`), A4 (`0.158385`) ve A6 (`0.157203`) Phone sonuçlarını geçmiştir. Bununla birlikte CV Scripted performansında genel-domain maliyet oluşmuş, A4 robustness tarafında güçlü bir Pareto adayı olarak kalmıştır. Sonuçlar staged domain adaptation hipotezini destekler; ancak A7 aynı anda parent continuation, veri dengesi ve augmentasyonu değiştirdiği için augmentasyonların bağımsız nedensel katkısı ayrıştırılamaz. Çalışma ayrıca decode, segmentasyon, stereo kanal ayrımı, prediction provenance, checkpoint bütünlüğü ve negatif sonuçların korunmasının model eğitimi kadar önemli olduğunu göstermektedir.

## English abstract

This study investigates adapting `openai/whisper-large-v3-turbo` to Turkish telephone-like and conversational speech. It combines a historical Legacy series with a controlled A0–A7 series evaluated under a shared frozen protocol. Encoder-only, decoder-only, and encoder–decoder LoRA scopes were compared alongside replay, clean schedules, parent-adapter continuation, source anchoring, telephone-band, speed, and noise/gain augmentation. The best controlled MediaSpeech Phone result was achieved by A7 step-200, which continued from the A2 adapter and reached a normalized WER of `0.1542845`. A7 outperformed A2 (`0.170825`), A4 (`0.158385`), and A6 (`0.157203`) on the Phone proxy. However, A7 incurred a general-domain cost on CV Scripted, while A4 remained a strong robustness Pareto candidate. The findings support staged domain adaptation for the open-data telephone proxy, but the independent causal contribution of augmentation remains inconclusive because A7 jointly changed parent continuation, source balance, and augmentation. The study also shows that decoding, segmentation, stereo channel handling, prediction provenance, checkpoint integrity, and preservation of negative results are as important as model training.

---

## Anahtar kelimeler

### Türkçe

Whisper, Türkçe ASR, otomatik konuşma tanıma, telefon konuşması, çağrı merkezi, LoRA, PEFT, domain adaptation, staged adaptation, negatif transfer, WER, CER, stereo kanal ayrımı, VAD, uzun-form decoding.

### English

Whisper, Turkish ASR, automatic speech recognition, telephone speech, contact-center speech, LoRA, PEFT, domain adaptation, staged adaptation, negative transfer, WER, CER, stereo channel separation, VAD, long-form decoding.

---

## Bir paragraflık teknik özet

Kontrollü A0–A7 serisinde en iyi Phone sonucu, A2 parent adapterından düşük learning rate ile devam eden, değişmemiş bir source anchor ve telefon-benzeri veri/augmentasyon karışımı kullanan A7 step-200 tarafından üretildi. Buna rağmen A7 bütün domainlerde en iyi değildi: CV Scripted tarafında maliyet oluştu ve A4 robustness için güçlü bir Pareto adayı olarak kaldı. Dolayısıyla doğru sonuç “tek model her yerde en iyidir” değil; hedef-domain staged adaptation’ın işe yaradığı, fakat model seçiminin telefon ve genel Türkçe panellerinde ayrı yapılması gerektiğidir.

## 100 kelimelik paylaşım metni

Türkçe telefon konuşması için Whisper large-v3-turbo üzerinde Legacy ve kontrollü A0–A7 deneylerini tamamladım. Encoder/decoder LoRA kapsamı, replay, veri dengesi, phone-band, speed, noise/gain, decoding ve memory profilleri karşılaştırıldı. A7 staged domain adaptation, MediaSpeech Phone normalized WER’i `0.154285` seviyesine indirerek kontrollü serinin en iyi Phone sonucunu verdi. Ancak CV Scripted tarafında negatif transfer oluştu; A4 robustness için güçlü bir Pareto adayı olarak kaldı. Repo; Türkçe/İngilizce makale, public metric tabloları, negatif sonuçlar, tam deney arşivi ve yeniden üretim rehberleri içeriyor.

## Kısa sosyal paylaşım

Türkçe telefon-benzeri konuşma için Whisper large-v3-turbo A0–A7 araştırması tamamlandı. En iyi Phone nWER: **0.154285 (A7 step-200)**. Staged adaptation işe yaradı; fakat genel-domain maliyet oluştu. Makale, metrikler, negatif sonuçlar ve yeniden üretim rehberi: https://github.com/Darkem0/whisper-turkish-domain-adaptation

---

## Doğru iddia biçimi

Kullanılabilir:

> A7, çalışmadaki açık-veri telefon proxy’sinde en iyi kontrollü Phone WER sonucunu verdi.

Kullanılmamalı:

> A7 gerçek Türkçe çağrı merkezlerinde kanıtlanmış en iyi modeldir.

Kullanılabilir:

> Staged domain adaptation hipotezi hedef Phone proxy’sinde desteklendi.

Kullanılmamalı:

> Telefon augmentasyonunun bağımsız etkisi kesin olarak kanıtlandı.

---

## Önerilen yayın kanalları

- GitHub canonical repository
- Zenodo: GitHub release arşivi ve DOI
- OSF: proje kaydı ve ek materyal
- arXiv veya alan-uygun bir preprint sunucusu
- Hugging Face Paper page veya model card, yalnız model paylaşım lisansı uygunsa
- Medium, Substack veya kişisel teknik blog: sadeleştirilmiş rehber sürümü
- LinkedIn: kısa sonuç ve GitHub bağlantısı

Bu platformların kuralları ve veri/model lisansları ayrıca kontrol edilmelidir.

---

## Atıf

Depodaki [`CITATION.cff`](../CITATION.cff) kullanılmalıdır.

Önerilen düz metin:

> Aslan, E. (2026). Whisper Large-v3-Turbo Turkish Domain Adaptation: LoRA Scope, Staged Domain Adaptation, Telephone Augmentation, and Negative Transfer. GitHub repository. https://github.com/Darkem0/whisper-turkish-domain-adaptation

---

## Yayın öncesi kontrol listesi

- [ ] A7 sonucu `0.1542845` olarak authoritative tabloyla eşleşiyor.
- [ ] A7 resume sınırlaması belirtiliyor.
- [ ] A4 robustness Pareto sonucu korunuyor.
- [ ] CV Scripted/FLEURS negatif transferi saklanmıyor.
- [ ] Open-data proxy ile gerçek çağrı performansı karıştırılmıyor.
- [ ] Ham ses, özel transkript ve checkpoint yayımlanmıyor.
- [ ] Veri seti ve model lisansları ayrı kontrol ediliyor.
- [ ] Araştırılmış fakat çalıştırılmamış yöntemler açıkça ayrılıyor.
