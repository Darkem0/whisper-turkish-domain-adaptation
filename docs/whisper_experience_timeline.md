# Whisper Deneyim Zaman Çizelgesi

Bu zaman çizelgesi, erişilebilen ChatGPT hafızası, yüklenmiş raporlar ve doğrulanmış proje artefaktlarından oluşturulmuştur. Tarihler yaklaşık dönemleri gösterir; özgün run artefaktı olmayan kayıtlar konuşma-hafızası veya arşiv-raporu olarak işaretlenir.

## Kanıt işaretleri

- **A:** Artefakt doğrulamalı
- **B:** Arşiv raporu doğrulamalı
- **C:** ChatGPT konuşma hafızası
- **R:** Araştırıldı, uygulanmadı

---

## 2025 — İlk model uyarlama soruları

### Temmuz–Eylül 2025 — Kişisel Türkçe veriyle Whisper geliştirme `[C]`

- Whisper large-v2/large-v3 modellerini kişisel Türkçe seslerle geliştirme olasılığı incelendi.
- LoRA’nın bağımsız model değil, base Whisper üzerine eklenen alan uyarlama katmanı olduğu netleştirildi.
- Colab T4 ve tüketici GPU’larında tam fine-tune yerine LoRA/PEFT önceliklendirildi.
- Large-v3 üzerinde 1 epoch ve 2 epoch kişisel veri denemeleri yapıldığı konuşma hafızasında kayıtlıdır.
- Özgün metrikler ve checkpointler erişilebilir olmadığı için sonuçlar bilimsel sıralama olarak yayımlanmaz.

### Sonbahar 2025 — ASR çıktısının semantik değerlendirilmesi `[C]`

- Katı regex ve harf-harf eşleşmenin çağrı kalitesini doğru ölçmediği görüldü.
- Kritik sayı, süre ve anlam korunuyorsa küçük ASR yüzey hatalarına tolerans verilmesi benimsendi.
- Boş veya kullanılamaz transcript ayrı kalite durumu olarak ele alındı.
- WER/CER ile downstream semantik kullanılabilirliğin ayrı metrikler olduğu kabul edildi.

---

## Ocak 2026 — Large-v2 LoRA ve gerçek çağrı karşılaştırmaları

### Large-v2 LoRA eğitimi `[C]`

- Base: `openai/whisper-large-v2`
- Yaklaşık 40.082 örnek
- RTX A5000, yaklaşık 24 GB VRAM
- Q/V LoRA, rank 8, alpha 16, dropout 0.1
- Batch 2, gradient accumulation 8
- Learning rate `3e-5`
- 3 epoch

Validation loss düşüşü:

| Epoch | Loss |
|---|---:|
| 1 | 0.1558 |
| 2 | 0.1502 |
| 3 | 0.1488 |

Gerçek hedef çağrı değerlendirmesinde epoch 2 iyi, epoch 3 kötü bulundu. Böylece validation loss’un tek başına hedef-domain kalite göstergesi olmadığı anlaşıldı.

### Aynı çağrıda model karşılaştırması `[C]`

Nitel sıralama:

1. Whisper large-v3
2. Whisper large-v2
3. Fine-tuned large-v2

Öne çıkan hata türleri:

- negatif sayı/para ifadesi kaybı,
- arka plan gürültüsünde anlamsız üretim,
- özel isim hataları,
- fine-tuned modelde kısa veya eksik çıktı.

Özel çağrı metni ve kişisel isimler yayımlanmaz.

### Uzun ses ve generation sınırları `[C]`

- 30 saniyelik bağlam ve chunking sınırları incelendi.
- Overlap, sınır kelimelerini korurken tekrar üretebildi.
- `max_new_tokens=768`, modelin `max_target_positions=448` sınırıyla çatıştı.
- Eğitimdeki `no_timestamps=True` ile inference promptunun uyumu kritik bulundu.
- Attention mask ve `pad_token == eos_token` uyarıları gözlendi.

---

## Ocak 2026 — GB10 ARM64 runtime çalışması `[C]`

- NVIDIA GB10/AArch64, CUDA 13 ve güncel NGC PyTorch containerı doğrulandı.
- Eski container sürümlerinin yeni GPU mimarisini desteklemediği görüldü.
- CTranslate2/faster-whisper CUDA backend’i ARM64 + CUDA 13 kombinasyonunda güvenilir çalışmadı.
- Transformers/openai-whisper yolu tercih edildi.
- Hız/kalite dengesi için large-v3-turbo üretim adayı oldu.

---

## Mart 2026 — I3R ses alma ve dönüştürme hattı `[C]`

Olgunlaşan akış:

```text
I3R
→ üretici decoder executable
→ WAV
→ FFmpeg canonicalization
→ Whisper/WhisperX veya VibeVoice
→ transcript ve log
→ geçici dosya temizliği
```

Öğrenilenler:

- `.i3r` doğrudan FFmpeg’e verilemez.
- Özel/encrypted format önce üretici decoderıyla açılmalıdır.
- Whisper için 16 kHz mono; VibeVoice için 24 kHz gerekebilir.
- Tek bir sample-rate politikası bütün modeller için doğru değildir.
- File-vs-directory, log yolu ve sahte timestamp sorunları düzeltildi.
- Çalışan inference akışını yeniden yazmak yerine yalnız ingest adaptörünü değiştirmek daha güvenlidir.

---

## Haziran 2026 — Stereo çağrı ve konuşmacı rolü `[C]`

### Fiziksel kanal ayrımı

- Tam iki kanallı kayıtlar mono kanallara ayrıldı.
- Kanal konfigürasyonu Agent/Customer rolüne deterministik eşlendi.
- Kanallar ayrı ASR’dan geçirildi.
- Segmentler başlangıç zamanına göre birleştirildi.
- JSON ve TXT çıktı üretildi.

Ana karar:

> Fiziksel kanal bilgisi varsa diarization’dan önce kullanılmalıdır.

### Stereo-only container ve RAM/tmpfs

- Yalnız stereo çağrılar için ayrı çalışma yolu tasarlandı.
- Upload, FFmpeg ve geçici sesler RAM/tmpfs üzerinde tutuldu.
- Model GPU/VRAM üzerinde çalıştı.
- İş sonunda geçici dosya temizliği zorunlu tutuldu.

### Timestamp sorunu

- Bozuk zamanların kanal merge’den değil, seq2seq pipeline `chunk_length_s=30` kullanımından geldiği görüldü.
- Chunk ayarı kaldırılıp segment timestamp repair uygulandı.
- 71 segmentte 4 repair, 0 şüpheli segment raporlandı.
- Word-level timestamp operasyonel olarak ağır bulundu.

---

## Haziran 2026 — Üretim ve servis tecrübeleri `[C]`

- Yaklaşık 20 saniyelik sesin GB10 üzerinde yaklaşık 1 saniye civarında transkripsiyon süreleri görüldü.
- Uzun çalışan containerlarda RAM/swap birikimi servis davranışını bozabildi.
- Restart sonrası bellek kullanımının düştüğü gözlendi.
- API 500 hatalarının yalnız modelden değil, dosya dönüşümü, request alanları, temp dosya ve downstream servislerden kaynaklanabildiği görüldü.
- Model inference süresi ile uçtan uca API süresinin ayrı raporlanması gerektiği kabul edildi.

---

## Temmuz 2026 — Legacy açık veri deneyleri `[B]`

### Legacy-H0 — Base

- MediaSpeech raw WER: `0.4255`
- MediaSpeech normalized WER: `0.1558`

Normalizasyonun ölçüm üzerindeki büyük etkisi görüldü.

### Legacy-H1 — MediaSpeech-only LoRA

- Base nWER: `0.1558`
- LoRA nWER: `0.2162`
- Yaklaşık `%38,8` göreli kötüleşme

Karar: başarısız negatif kontrol.

### Legacy-H2 — General Turkish LoRA

- Hedef 2 epoch tamamlanmadı; checkpoint yaklaşık epoch `0,42` seviyesindeydi.
- Common Voice: `0.1837 → 0.1368`
- MediaSpeech: `0.1601 → 0.1718`

Karar: domain-bağımlı; veri oranı kritik.

### Legacy-H3 — Balanced-phone continuation

- Yaklaşık 24,01 saat balanced schedule
- LR `5e-6`
- Common Voice: `0.1241`
- MediaSpeech: `0.1366`
- External360: base `0.0857`, balanced-phone `0.1018`

Karar: hedefe yakın testte başarılı, temiz dış domainde negatif transfer.

### Legacy-H4 — Repeat-safe decode

- İlk LoRA decode: `0.8469`
- Repeat-safe: `0.6466`
- Yaklaşık `%23,7` göreli iyileşme

Karar: uzun çağrıda decode politikası model kadar etkili.

---

## 30–31 Temmuz 2026 — Kontrollü araştırma hattının kurulması `[A]`

Sabitler:

- plain Hugging Face Transformers
- Whisper large-v3-turbo
- RTX 4070 SUPER, yaklaşık 12 GB
- LoRA/PEFT
- aynı frozen evaluation paneli
- prediction JSONL ve SHA-256
- D3 decode profili
- aynı GPU’da tek worker

### A0 — Base

- Clean `0.16255`
- Phone `0.17568`
- G.711 `0.14574`
- Robustness `0.16163`
- CV Scripted `0.15560`
- FLEURS `0.10288`

### A2 — Encoder+decoder Q/V

- Clean `0.13823`
- Phone `0.170825`
- G.711 `0.13893`
- Robustness `0.14655`
- CV Scripted `0.15369`
- FLEURS `0.17693`

Karar: hedef proxy kazanımı, FLEURS maliyeti; A7 parent.

### A3 — Encoder-only + `%10` replay

- En iyi Phone yaklaşık `0.157342`
- Robustness kazancı desteklendi
- CV Scripted step-50 `0.23532`

Karar: `A3_V2_NO_PROMOTABLE_CHECKPOINT`.

### A4 — Decoder-only

- En iyi Phone `0.158385`
- En iyi robustness yaklaşık `0.1441`

Karar: güçlü Pareto adayı.

### A5 — Encoder-only clean schedule

- En iyi Phone yaklaşık `0.1580`
- En iyi robustness yaklaşık `0.1475`

Karar: sınırlı fayda.

### A6 — Encoder+decoder clean schedule

- Phone `0.157203`
- Robustness yaklaşık `0.1448`
- Self-comparison path bugı düzeltildi.
- 4.059 prediction ve 27/28 aggregate metric farklı bulundu.

Karar: daha geniş scope otomatik sinerji sağlamadı.

---

## 31 Temmuz 2026 — Decoding ve memory araştırması `[A]`

### D0–D7

- D3 canonical profil oldu.
- D3 normalized WER: `0.156021`.

### P4–P6

- İkinci decode tetiklenmedi.
- Güvenli deterministic ITN dönüşümü bulunmadı.
- Gerçek n-best çeşitliliği üretilemedi.

### P7 memory

- MEM1: aynı çıktı, yaklaşık `%5,59` hızlanma.
- MEM2: aynı çıktı, yaklaşık `%32,12` microbenchmark hızlanması.
- MEM3/MEM4: daha hızlı, fakat prediction değişti.
- Canonical değerlendirme profili MEM0 olarak kaldı.
- MEM2 `microbenchmark-positive / deployment-inconclusive` sınıfına alındı.

---

## 1–2 Ağustos 2026 — A7 final entegrasyonu `[A]`

### Tasarım

- A2 parent
- TSC source anchor
- MediaSpeech + CV Spontaneous phone-like kaynaklar
- phone-band, speed 0.75, noise/gain ve combined augmentasyon
- 200 optimizer step / 3.200 occurrence

### Augmentasyon güvenliği

- V1 clipping üretti.
- V2 resampling overshoot bıraktı.
- V3 universal peak guard ile 1.493/1.493 occurrence geçti.

### Kesinti ve resume

- Terminal kapanması workerı durdurdu.
- Yanlış schedule-weight resume durduruldu.
- Stale step-200 çakışması çözüldü.
- Adapter klasörünün dosya gibi hashlenmesi düzeltildi.
- Step-150’den optimizer-reset continuation ile tamamlandı.

### Final

- Phone step-200: `0.154285`
- A7 robustness step-150: `0.147578`
- Frozen evaluation: 28/28
- Final adapter SHA: `fa5aa88e3d7fd1c16b7b7cdb0c516bc7d49210f3c5cb63c8405f280bad9e4894`

Terminal karar:

```text
OPEN_DATA_EXPERIMENT_LINE_COMPLETED
```

---

## Temmuz–Ağustos 2026 — Audio-aware pseudo-label araştırması `[R]`

Araştırılan mimari:

- stereo kanal ayrımı,
- VAD/turn segmentation,
- Qwen3-ASR birincil öğretmen,
- Whisper ikinci öğretmen,
- yalnız uyuşmazlık span’lerinde Qwen3-Omni Instruct hakem,
- Türkçe CTC alignment,
- confidence-gated insan incelemesi,
- clean replay veya adapter routing ile student eğitimi.

Bu mimari uygulanmış deney değil, araştırma sonucudur.

---

## Nihai tarihsel çıkarım

Çalışma, “daha fazla fine-tune” yaklaşımından şu bütüncül modele evrildi:

```text
kaynak codec doğrulaması
→ güvenilir kanal ayrımı
→ kontrollü segmentasyon
→ domain dengeli eğitim
→ LoRA scope ablation
→ ortak frozen evaluation
→ decode ve memory eşitliği
→ prediction/checkpoint provenance
→ negatif transfer ve hata analizi
```

En güçlü teknik sonuç A7 Phone WER; en güçlü metodolojik sonuç ise her kazancın ayrı domain, aynı decode ve doğrulanmış artefaktlarla ölçülmesi gereğidir.
