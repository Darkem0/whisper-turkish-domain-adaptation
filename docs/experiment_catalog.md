# Deney Kataloğu

## Legacy seri

| Kimlik | Yöntem | Sonuç |
|---|---|---|
| Legacy-H0 | Base Whisper | Başlangıç referansı |
| Legacy-H1 | MediaSpeech-only LoRA | MediaSpeech normalize WER kötüleşti; negatif kontrol |
| Legacy-H2 | Common Voice + MediaSpeech genel Türkçe LoRA | Common Voice iyileşti, MediaSpeech ve dış-domain genellemesi sınırlı kaldı |
| Legacy-H3 | Balanced-phone continuation | Eğitim dağılımına yakın testte iyileşme; temiz dış-domain maliyeti |
| Legacy-H4 | Repeat-safe decode | Uzun telefon örneğinde tekrar döngüsünü azalttı |

## Kontrollü seri

### A0

- Model: base `whisper-large-v3-turbo`
- Eğitim: yok
- Rol: referans

### A2

- Scope: encoder+decoder `q_proj/v_proj`
- Rank: 16
- Replay: yok
- Ana bulgu: hedef telefon ve robustness tarafında iyileşme; FLEURS maliyeti

### A3

- Scope: encoder-only `q_proj/v_proj`
- Replay: %10 clean replay
- Ana bulgu: robustness kazancı; CV Scripted forgetting
- Durum: production adayı değil, araştırma referansı

### A4

- Scope: decoder-only `q_proj/v_proj`
- Replay: yok
- Ana bulgu: güçlü Phone ve robustness adayı
- Not: schedule içinde 52 boş-hedef exposure bulundu; geniş etkileri açıklamak için yetersizdi

### A5

- Scope: encoder-only
- Temiz train manifesti
- Zero replay
- Ana bulgu: Phone iyileşti; A4 robustness seviyesini geçemedi

### A6

- Scope: encoder+decoder
- A5 ile matched veri ve schedule
- Zero replay
- Ana bulgu: A5’ten farklı predictionlar; ilk sıfır-delta raporu geçersizdi

### A7

- Parent: A2
- Yöntem: staged continuation
- Source anchor: TSC, yalnız değiştirilmemiş kaynak ankrajı
- Phone-like sources: MediaSpeech + CV Spontaneous
- Augmentasyon: phone-band, speed 0.75, noise/gain, combined
- Schedule: 3.200 occurrence
- En iyi Phone: step-200, `0.154285`
- En iyi robustness: step-150, `0.147578`
- Bilimsel sınıf: staged adaptation desteklendi; genel-domain maliyet oluştu

## Kontrollü Phone sonuçları

| Deney | En iyi Phone normalize WER |
|---|---:|
| A2 | 0.170825 |
| A4 | 0.158385 |
| A6 | 0.157203 |
| A7 | **0.154285** |

## Yöntem sınıflandırması

| Yöntem | Karar |
|---|---|
| MediaSpeech-only fine-tuning | Başarısız/negatif kontrol |
| Genel Türkçe LoRA | Domain-bağımlı |
| Encoder-only | Sınırlı fayda |
| Decoder-only | Güçlü Pareto adayı |
| Encoder+decoder joint | Ek sinerji kesin değil |
| Staged domain adaptation | Desteklendi |
| Clean replay | Yetersiz koruma |
| Telefon augmentasyonu | Entegrasyon içinde faydalı olabilir; bağımsız katkı ayrıştırılmadı |
| Repeat-safe decode | Uzun görüşmede etkili tarihsel bulgu |
