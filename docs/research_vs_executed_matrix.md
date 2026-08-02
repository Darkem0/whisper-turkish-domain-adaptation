# Araştırılan, Uygulanan ve Reddedilen Whisper Yöntemleri

Bu matris, literatürde incelenen yöntemlerle gerçekten çalıştırılan deneyleri birbirinden ayırır. Amaç, “araştırıldı” ifadesinin yanlışlıkla “uygulandı ve doğrulandı” anlamına gelmesini önlemektir.

## Durum etiketleri

| Etiket | Anlamı |
|---|---|
| `EXECUTED_VERIFIED` | Deney artefaktı, prediction, metric veya checkpoint ile doğrulandı |
| `EXECUTED_ARCHIVAL` | Eski raporda sonuç var; özgün artefaktların bir bölümü artık erişilemiyor |
| `EXECUTED_MEMORY_ONLY` | ChatGPT konuşma hafızasında kayıtlı; public artefakt yok |
| `RESEARCHED_NOT_EXECUTED` | Literatür/mimari araştırması yapıldı, deney çalıştırılmadı |
| `REJECTED_BY_EVIDENCE` | Çalıştırıldı ve eldeki kanıta göre reddedildi |
| `INCONCLUSIVE` | Kanıt karar vermeye yetmedi |
| `DIAGNOSTIC_ONLY` | Üretim adayı değil, mekanizma veya hata teşhisi için kullanıldı |

---

## 1. Ses alma ve ön işleme

| Yöntem | Durum | Kanıt | Sonuç | Yorum |
|---|---|---|---|---|
| I3R’yi üretici decoderıyla açma | `EXECUTED_MEMORY_ONLY` | Çalışan pipeline kayıtları | Başarılı | FFmpeg özel/encrypted biçimi doğrudan okuyamadı |
| `.i3r` dosyasını doğrudan FFmpeg’e verme | `REJECTED_BY_EVIDENCE` | Decode hataları | Başarısız | Önce vendor decode zorunlu |
| Tek kontrollü canonical resampling | `EXECUTED_MEMORY_ONLY` | Pipeline tecrübesi | Başarılı | Gereksiz tekrar dönüşümler azaltıldı |
| Modelden bağımsız sabit sample rate | `REJECTED_BY_EVIDENCE` | Whisper 16 kHz / VibeVoice 24 kHz farkı | Hatalı tasarım | Canonicalization hedef modele bağlı olmalı |
| FFprobe/codec envanteri | `EXECUTED_ARCHIVAL` | Teknik pipeline raporu | Önerilen/uygulanan kontrol | WAV uzantısı gerçek codec’i garanti etmez |
| Ağır bütünsel denoise | `RESEARCHED_NOT_EXECUTED` | Literatür ve pipeline araştırması | Uygulanmadı | Her kayıtta otomatik kazanç beklenemez |
| Hafif denoise A/B | `RESEARCHED_NOT_EXECUTED` | Teknik araştırma | Uygulanmadı | S/Ş/F/H gibi fonemleri silebilir |
| RNNoise | `RESEARCHED_NOT_EXECUTED` | Teknik araştırma | Uygulanmadı | Ek 48 kHz resampling maliyeti var |
| Loudness normalization | `RESEARCHED_NOT_EXECUTED` | Teknik araştırma | Uygulanmadı | Kısa segmentlerde her zaman yararlı değil |

---

## 2. Kanal ayrımı, diarization ve timestamp

| Yöntem | Durum | Sonuç | Yorum |
|---|---|---|---|
| Fiziksel stereo kanal split | `EXECUTED_MEMORY_ONLY` | Başarılı | Agent/Customer rolü deterministic oldu |
| Stereo kanalları erken mono downmix | `REJECTED_BY_EVIDENCE` | Reddedildi | Rol ve overlap bilgisi kayboluyor |
| Kanal segmentlerini start time ile birleştirme | `EXECUTED_MEMORY_ONLY` | Başarılı | Ayrı ASR çıktıları kronolojik birleşti |
| Fiziksel kanal varken diarization | `DIAGNOSTIC_ONLY` | Genellikle gereksiz | Mono/leakage/ek konuşmacı durumlarına ayrılmalı |
| WhisperX/pyannote diarization | `EXECUTED_MEMORY_ONLY` | Çalıştı | Dependency ve model erişimi ayrı hata alanı oluşturdu |
| NeMo diarization | `EXECUTED_MEMORY_ONLY` | Kısmen çalıştırıldı | Kurulum ve ARM64/CUDA uyumu ağır |
| HF pipeline `chunk_length_s=30` timestamps | `REJECTED_BY_EVIDENCE` | Sorunlu | Malformed segment zamanları üretti |
| Segment timestamp repair | `EXECUTED_MEMORY_ONLY` | Başarılı | 71 segmentte 4 repair, 0 suspicious |
| Word-level timestamps | `INCONCLUSIVE` | Operasyonel olarak ağır | Uzun sürme/takılma gözlendi |
| Türkçe CTC forced alignment | `RESEARCHED_NOT_EXECUTED` | Önerildi | Review UX için yüksek değerli |
| MFA Türkçe alignment | `RESEARCHED_NOT_EXECUTED` | Önerildi | Sözlük/G2P bakım maliyeti var |

---

## 3. VAD ve uzun ses

| Yöntem | Durum | Sonuç | Yorum |
|---|---|---|---|
| VAD’siz uzun Transformers decode | `REJECTED_BY_EVIDENCE` | Legacy nWER `1.1772` | Tekrar/hallucination ve segment sorunu |
| VAD’li uzun decode | `EXECUTED_ARCHIVAL` | Legacy nWER `0.6568` | Runtime farkları da bulunduğu için saf VAD etkisi değildir |
| 20–28 s chunk + overlap | `EXECUTED_MEMORY_ONLY` | Sınırlı | Boundary korur, tekrar üretir |
| Repeat-safe chunk decode | `EXECUTED_ARCHIVAL` | Başarılı | `0.8469 → 0.6466` |
| Agresif silence removal | `RESEARCHED_NOT_EXECUTED` | Önerilmedi | Timeline ve kısa utterance kaybı riski |
| Silero VAD | `EXECUTED_MEMORY_ONLY` | Kullanıldı/araştırıldı | 8/16 kHz ve padding kalibrasyonu gerekli |
| WebRTC VAD | `RESEARCHED_NOT_EXECUTED` | Alternatif | Hafif; frame ve PCM kısıtları var |

---

## 4. Fine-tuning ve PEFT

| Yöntem | Durum | En önemli kanıt | Karar |
|---|---|---|---|
| Large-v3 kişisel veri 1/2 epoch | `EXECUTED_MEMORY_ONLY` | Deneme hafızası; metrik yok | Raporlanabilir deneyim, bilimsel sonuç değil |
| Large-v2 Q/V LoRA r8 | `EXECUTED_MEMORY_ONLY` | 3 epoch loss ve gerçek çağrı karşılaştırması | Hedef çağrıda başarısız/sınırlı |
| MediaSpeech-only LoRA | `REJECTED_BY_EVIDENCE` | `0.1558 → 0.2162` | Aynı biçimde tekrar edilmemeli |
| General Turkish LoRA | `EXECUTED_ARCHIVAL` | CV iyi, MediaSpeech kötü | Domain-bağımlı |
| Balanced-phone continuation | `EXECUTED_ARCHIVAL` | CV/MediaSpeech iyi; external360 kötü | Hedefte başarılı, negatif transfer |
| A2 encoder+decoder Q/V | `EXECUTED_VERIFIED` | Phone `0.170825`, FLEURS `0.17693` | Hedefte faydalı, general maliyet |
| A3 encoder-only + `%10` replay | `REJECTED_BY_EVIDENCE` | CV Scripted `0.23532` | Replay yetersiz; production adayı değil |
| A4 decoder-only | `EXECUTED_VERIFIED` | Phone `0.158385`, robustness ~`0.1441` | Güçlü Pareto adayı |
| A5 encoder-only clean | `EXECUTED_VERIFIED` | Phone ~`0.1580` | Sınırlı fayda |
| A6 encoder+decoder clean | `EXECUTED_VERIFIED` | Phone `0.157203` | Joint scope sinerjisi sınırlı |
| A7 staged domain adaptation | `EXECUTED_VERIFIED` | Phone `0.154285` | En iyi kontrollü Phone sonucu |
| Full fine-tuning large model | `RESEARCHED_NOT_EXECUTED` | VRAM analizi | 12 GB kartta elendi |
| Layer-selective LoRA | `RESEARCHED_NOT_EXECUTED` | Literatür/PEFT araştırması | Gelecek araştırma adayı |
| AdaLoRA | `RESEARCHED_NOT_EXECUTED` | PEFT araştırması | Özel update schedule nedeniyle ertelendi |
| DoRA | `RESEARCHED_NOT_EXECUTED` | PEFT araştırması | Whisper özel kanıtı yetersiz |
| q/k/v/out geniş LoRA | `RESEARCHED_NOT_EXECUTED` | Kapasite analizi | VRAM/overfit riski |
| Bottleneck adapter | `RESEARCHED_NOT_EXECUTED` | Literatür | Uygulanmadı |
| Prompt/perceiver tuning | `RESEARCHED_NOT_EXECUTED` | Literatür | Uygulanmadı |
| Self-supervised encoder adaptation | `RESEARCHED_NOT_EXECUTED` | Literatür | Hesaplama ve veri maliyeti yüksek |
| Conformer/CNN adapter | `RESEARCHED_NOT_EXECUTED` | Literatür | Ön eğitim ağırlıklarıyla uyum riski |
| CTC/RNNT yardımcı loss | `RESEARCHED_NOT_EXECUTED` | Literatür | Mimari değişiklik gerektirir |

---

## 5. Replay, anchor ve veri karışımı

| Yöntem | Durum | Sonuç | Karar |
|---|---|---|---|
| `%10` clean replay | `EXECUTED_VERIFIED` | CV Scripted forgetting’i önlemedi | Tek başına yetersiz |
| TSC unchanged source anchor | `EXECUTED_VERIFIED` | A7 entegrasyonunun parçası | Bağımsız etkisi ayrıştırılmadı |
| MediaSpeech + CV Spontaneous phone-like mix | `EXECUTED_VERIFIED` | A7’nin parçası | Entegrasyon içinde başarılı |
| Domain-weighted sampling | `EXECUTED_ARCHIVAL` | Legacy balanced-phone iyileşti | Veri oranı kritik |
| Adapter routing | `RESEARCHED_NOT_EXECUTED` | Domain ayrımı nedeniyle önerildi | Gerçek routing deneyine ihtiyaç var |
| Curriculum learning | `RESEARCHED_NOT_EXECUTED` | Literatür | Stabil baseline sonrası aday |
| Multi-domain SpeechStew tipi karışım | `RESEARCHED_NOT_EXECUTED` | Literatür | Uygulanmadı |

---

## 6. Augmentasyon

| Yöntem | Durum | Sonuç | Karar |
|---|---|---|---|
| Phone-band | `EXECUTED_VERIFIED` | A7 entegrasyonunda kullanıldı | Bağımsız causal katkı belirsiz |
| G.711 perturbation | `EXECUTED_VERIFIED` | Frozen evaluation koşulu | Dayanıklılık ölçümü için yararlı |
| Speed `0.75x` | `EXECUTED_VERIFIED` | A7 schedule’da kullanıldı | Bağımsız katkı belirsiz |
| Noise/gain | `EXECUTED_VERIFIED` | A7 schedule’da kullanıldı | Clipping guard zorunlu |
| Phone-band + noise/gain | `EXECUTED_VERIFIED` | A7 combined bucket | Entegrasyon parçası |
| Positive gain içeren V1 | `REJECTED_BY_EVIDENCE` | Clipping | Policy değiştirildi |
| V2 phone-band | `REJECTED_BY_EVIDENCE` | Resampling overshoot | V3 peak guard’a geçildi |
| V3 universal peak guard | `EXECUTED_VERIFIED` | 1.493/1.493 geçti | Başarılı güvenlik katmanı |
| SpecAugment | `RESEARCHED_NOT_EXECUTED` | Literatür | Waveform codec bozulmasının yerine geçmez |
| RIR/reverb | `RESEARCHED_NOT_EXECUTED` | Teknik araştırma | Telefon hedefinde düşük öncelik |
| Packet loss/gap | `RESEARCHED_NOT_EXECUTED` | Teknik araştırma | Gerçek üretim dağılımı olmadan riskli |

---

## 7. Decoding, dil modeli ve son işlem

| Yöntem | Durum | Sonuç | Karar |
|---|---|---|---|
| D3 decode profili | `EXECUTED_VERIFIED` | nWER `0.156021` | Canonical |
| Repeat-safe decode | `EXECUTED_ARCHIVAL` | Büyük uzun-form kazancı | Korunmalı, fakat meşru tekrar riski izlenmeli |
| P4 ikinci decode | `REJECTED_BY_EVIDENCE` | Tetiklenmedi | Ek maliyet gerekçesiz |
| P5 deterministic ITN | `REJECTED_BY_EVIDENCE` | Güvenli dönüşüm yok | Koşulsuz uygulanmadı |
| P6 n-best rescoring | `INCONCLUSIVE` | Gerçek n-best yok | Uygulanabilir deney oluşmadı |
| External 5-gram/neural LM | `RESEARCHED_NOT_EXECUTED` | Literatür | Dev set ve gerçek hipotez çeşitliliği gerekir |
| Contextual bias/hotword | `RESEARCHED_NOT_EXECUTED` | Literatür ve kullanım ihtiyacı | Özel ad/entity için aday |
| LLM transcript correction | `EXECUTED_MEMORY_ONLY` | Downstream semantik analizde kullanıldı | ASR gold üretimi için confidence gate gerekir |
| Calm-Whisper head tuning | `RESEARCHED_NOT_EXECUTED` | Literatür | Non-speech hallucination adayı |

---

## 8. Inference runtime ve memory

| Yöntem | Durum | Sonuç | Karar |
|---|---|---|---|
| Plain Transformers | `EXECUTED_VERIFIED` | Kontrollü araştırmanın runtime’ı | Canonical |
| OpenAI Whisper turbo | `EXECUTED_MEMORY_ONLY` | GB10’da kullanıldı | Uygulanabilir |
| Faster-Whisper/CTranslate2 x86 | `EXECUTED_ARCHIVAL` | Legacy VAD baseline | Eski karşılaştırma |
| Faster-Whisper/CTranslate2 ARM64 CUDA13 | `REJECTED_BY_EVIDENCE` | Backend/arch uyumsuzluğu | GB10 hattında terk edildi |
| MEM0 | `EXECUTED_VERIFIED` | Deterministik canonical | Korundu |
| MEM1 | `EXECUTED_VERIFIED` | `%5,59` hız, aynı çıktı | Küçük kazanç |
| MEM2 | `INCONCLUSIVE` | `%32,12` hız, aynı çıktı | Microbenchmark olumlu; deployment kanıtı eksik |
| MEM3 | `REJECTED_BY_EVIDENCE` | `%57,27` hız, çıktı farklı | Karşılaştırma için kullanılamaz |
| MEM4 | `REJECTED_BY_EVIDENCE` | `%60,07` hız, çıktı farklı | Karşılaştırma için kullanılamaz |
| INT8/INT4 quantization | `RESEARCHED_NOT_EXECUTED` | Literatür | Kalite/hız A/B gerekli |
| Distillation | `RESEARCHED_NOT_EXECUTED` | Literatür | Büyük üretim hacmi için aday |
| Speculative decoding | `RESEARCHED_NOT_EXECUTED` | Literatür | Doğru kabul algoritması gerekir |

---

## 9. Değerlendirme ve güvenilirlik

| Yöntem | Durum | Sonuç | Karar |
|---|---|---|---|
| Raw WER/CER | `EXECUTED_VERIFIED` | Yüzey biçimine duyarlı | Normalize metrikle birlikte raporlanmalı |
| Normalized WER/CER | `EXECUTED_VERIFIED` | Ana karar metriği | Referans ve hipoteze aynı normalizer |
| Frozen 4×7 evaluation | `EXECUTED_VERIFIED` | A3–A7’de kullanıldı | Güçlü karşılaştırma temeli |
| Paired bootstrap | `EXECUTED_VERIFIED` | Seçilmiş karşılaştırmalarda kullanıldı | Sample eşleşmesi doğrulanmalı |
| Prediction SHA-256 | `EXECUTED_VERIFIED` | A5–A6 bugını görünür kıldı | Zorunlu |
| Checkpoint SHA/lock | `EXECUTED_VERIFIED` | A7 provenance | Zorunlu |
| Tek birleşik skor | `REJECTED_BY_EVIDENCE` | Domain farkını gizler | Telefon ve general paneli ayrı tutulmalı |
| Validation loss ile checkpoint seçimi | `REJECTED_BY_EVIDENCE` | Large-v2 epoch3 örneği | Hedef-domain eval gerekli |
| LLM semantik kalite skoru | `EXECUTED_MEMORY_ONLY` | Downstream için yararlı | WER’in yerine geçmez |
| Entity/sayı/tarih özel metrikleri | `RESEARCHED_NOT_EXECUTED` | Önerildi | Gerçek çağrı gold seti gerekir |

---

## 10. Pseudo-label ve audio-aware sistemler

| Yöntem | Durum | Rol | Hüküm |
|---|---|---|---|
| Tek Whisper pseudo-label | `RESEARCHED_NOT_EXECUTED` | Basit teacher | Confirmation-bias riski yüksek |
| Multi-ASR fusion | `RESEARCHED_NOT_EXECUTED` | Öğretmen çeşitliliği | Güçlü araştırma adayı |
| Qwen3-ASR-1.7B teacher | `RESEARCHED_NOT_EXECUTED` | Birincil teacher | Türkçe/context bias açısından önerildi |
| Whisper ikinci teacher | `RESEARCHED_NOT_EXECUTED` | Hata çeşitliliği | Önerildi |
| Qwen3-Omni Instruct hakem | `RESEARCHED_NOT_EXECUTED` | Yalnız anlaşmazlık span’leri | Maliyet kontrollü yaklaşım |
| Türkçe CTC alignment | `RESEARCHED_NOT_EXECUTED` | Review/timestamp | Önerildi |
| Confidence-gated insan inceleme | `RESEARCHED_NOT_EXECUTED` | Düşük güvenli span düzeltme | Tam otomasyondan daha gerçekçi |
| Surface transcript + normalized entity ayrımı | `RESEARCHED_NOT_EXECUTED` | Eğitim/downstream ayrımı | Güçlü tasarım ilkesi |

---

## 11. Nihai sınıflandırma

### Güçlü biçimde desteklenen

- Staged domain adaptation hedef Phone proxy’sini iyileştirdi.
- Telefon başarısı ile genel Türkçe başarısı aynı değildir.
- Decode ve segmentasyon model eğitimi kadar etkili olabilir.
- Prediction/checkpoint provenance zorunludur.
- Daha geniş LoRA scope otomatik olarak daha iyi değildir.

### Reddedilen

- Türkçe veri eklemek otomatik iyileştirir.
- Daha fazla epoch otomatik iyileştirir.
- `%10` replay genel-domain forgetting’i otomatik önler.
- Batch hızlanması prediction eşitliği bozulsa da aynı koşuldur.
- Tek validation loss en iyi checkpointi belirler.

### Belirsiz

- A7’de her augmentasyonun bağımsız katkısı.
- MEM2’nin gerçek üretim yararı.
- Gerçek çağrı verisinde A4/A7 sıralaması.
- Audio-aware pseudo-label mimarisinin insan emeği azaltma oranı.

### Araştırma terminal kararı

```text
OPEN_DATA_EXPERIMENT_LINE_COMPLETED
```
