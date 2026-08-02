# Whisper Large-v3-Turbo Türkçe Alan Uyarlaması

Bu depo, `openai/whisper-large-v3-turbo` modelini Türkçe telefon ve karşılıklı konuşma koşullarına uyarlamak için yürütülen açık-veri araştırmasının belgelenmiş sonucudur.

Çalışma artık üç ayrı bilgi katmanını kapsar:

1. **Legacy seri:** genel Türkçe LoRA, balanced-phone continuation ve repeat-safe decode denemeleri.
2. **Kontrollü A0–A7 serisi:** LoRA kapsamı, replay, staged domain adaptation, telefon augmentasyonu ve negatif transfer analizleri.
3. **Tam deneyim arşivi:** 2025–2026 arasındaki erişilebilir ChatGPT hafızası, large-v2/large-v3 fine-tuning tecrübeleri, I3R ses hattı, stereo kanal ayrımı, VAD/diarization, GB10 runtime, decoding/memory araştırmaları ve audio-aware pseudo-label tasarımı.

> Ana sonuç: A7 staged domain adaptation, kontrollü seride en iyi Phone WER sonucunu verdi; ancak CV Scripted gibi genel-domain ölçütlerinde maliyet oluştu. Tek bir adapter bütün Türkçe konuşma türlerinde en iyi değildir.

## Temel sonuçlar

| Karşılaştırma | Normalize Phone WER |
|---|---:|
| A2 | 0.170825 |
| A4 | 0.158385 |
| A6 | 0.157203 |
| **A7 step-200** | **0.154285** |

A7’nin en iyi robustness sonucu:

- **A7 step-150:** `0.147578`

Bilimsel sınıflandırma:

- `staged_domain_adaptation_supported`
- `staged_domain_adaptation_with_general_domain_cost`
- `augmentation_contribution_inconclusive`
- `OPEN_DATA_EXPERIMENT_LINE_COMPLETED`

## Deney özeti

| Deney | Yöntem | Kısa sonuç |
|---|---|---|
| A0 | Base model | Kontrollü referans |
| A2 | Encoder+decoder Q/V LoRA | Telefon alanında anlamlı iyileşme, bazı genel-domain kayıpları |
| A3 | Encoder-only + %10 replay | Robustness iyileşti; CV Scripted ciddi kötüleşti |
| A4 | Decoder-only, zero replay | Güçlü Phone ve robustness adayı |
| A5 | Encoder-only, temiz schedule | Phone iyileşti; A4 üstünlüğünü geçemedi |
| A6 | Encoder+decoder, temiz schedule | A5’ten farklı çıktı; ilk analizdeki sıfır-delta sonucu script hatasıydı |
| A7 | A2 parent + TSC source anchor + telefon odaklı staged continuation | En iyi kontrollü Phone sonucu; genel-domain maliyet |

## Neden yalnız WER yetmiyor?

Telefon ve çağrı benzeri konuşmalar:

- kısa cevaplar,
- konuşma kesintileri,
- spontane söyleyiş,
- kanal daralması,
- gürültü,
- tekrar/hallucination,
- sayı, tarih, tutar ve özel isim hataları

nedeniyle temiz okuma benchmarklarından farklı davranır. Bu nedenle sonuçlar iki ayrı panelde yorumlanır:

- **Telefon/karşılıklı konuşma paneli:** MediaSpeech Phone, G.711, robustness proxy, CV Spontaneous.
- **Genel Türkçe izleme paneli:** MediaSpeech Clean, CV Scripted, FLEURS, TSC.

## Önemli metodolojik dersler

- Türkçe veriyle fine-tuning yapmak otomatik olarak iyileşme sağlamaz.
- Veri dağılımı ve domain dengesi model kapsamı kadar önemlidir.
- Telefon augmentasyonu ve staged continuation birlikte fayda sağlayabilir; fakat A7 tasarımı augmentasyonun bağımsız nedensel katkısını ayırmaz.
- Normalize WER/CER, ham WER/CER ile birlikte raporlanmalıdır.
- Negatif transfer saklanmamalıdır.
- Prediction artefaktlarından bağımsız metric recomputation kritik önemdedir.
- Araştırılmış bir yöntem, çalıştırılmış deney gibi sunulmamalıdır.
- ChatGPT konuşma hafızası ile artefakt-doğrulamalı sonuçlar ayrı kanıt sınıflarında tutulmalıdır.

## Tam ChatGPT Whisper deneyim arşivi

Aşağıdaki belgeler yalnız mevcut proje serisini değil, erişilebilen bütün Whisper çalışma geçmişini kapsar:

- [Tam Whisper deneyim arşivi](docs/complete_whisper_experience_archive.md): 2025–2026 boyunca model eğitimi, I3R, stereo, timestamp, VAD, runtime, A0–A7 ve pseudo-label araştırmasının birleşik kaydı.
- [Whisper deneyim zaman çizelgesi](docs/whisper_experience_timeline.md): İlk kişisel fine-tune sorularından A7 terminal kararına kadar kronolojik gelişim.
- [Araştırılan ve uygulanan yöntemler matrisi](docs/research_vs_executed_matrix.md): Gerçekten çalıştırılan, reddedilen, belirsiz ve yalnız araştırılan yöntemlerin ayrımı.
- [ChatGPT hafızası kapsamı ve redaksiyon](docs/chatgpt_memory_provenance.md): Kaynak önceliği, erişim sınırı, gizlilik ve public yayın kuralları.

Arşiv, erişilebilen ChatGPT hafızası ve yüklenmiş kaynaklar içinde mümkün olan en geniş sentezdir. Silinmiş, indekslenmemiş veya erişilemeyen eski sohbetlerin eksiksiz kapsandığı iddia edilmez.

## Pratik başlangıç noktaları

- **Sonuçları ve gerekçeleri öğrenmek için:** [Ne işe yaradı, ne işe yaramadı?](docs/practical_research_guide.md)
- **Yerel proje klasörünü baştan sona analiz ettirmek için:** [Codex proje arkeolojisi promptu](docs/codex_project_archaeology_prompt.md)
- **Bütün deneyleri hızlı karşılaştırmak için:** [Deney kataloğu](docs/experiment_catalog.md)
- **Hataları tekrar etmemek için:** [Negatif sonuçlar ve araştırma hataları](docs/negative_results.md)

## Dokümantasyon

### Bütünleşik deneyim arşivi

- [Tam Whisper deneyim arşivi](docs/complete_whisper_experience_archive.md)
- [Whisper deneyim zaman çizelgesi](docs/whisper_experience_timeline.md)
- [Araştırılan ve uygulanan yöntemler matrisi](docs/research_vs_executed_matrix.md)
- [ChatGPT hafızası kapsam ve redaksiyon notu](docs/chatgpt_memory_provenance.md)

### Kontrollü araştırma belgeleri

- [Pratik araştırma rehberi](docs/practical_research_guide.md)
- [Codex proje arkeolojisi ve yayın promptu](docs/codex_project_archaeology_prompt.md)
- [Tam araştırma raporu](docs/full_research_report.md)
- [Deney kataloğu](docs/experiment_catalog.md)
- [Çağrı/telefon odaklı değerlendirme](docs/call_oriented_evaluation.md)
- [Negatif sonuçlar ve hatalar](docs/negative_results.md)
- [Yeniden üretilebilirlik](docs/reproducibility.md)
- [Sınırlamalar ve gelecek çalışma](docs/limitations_and_future_work.md)
- [Artefakt haritası](docs/artifact_map.md)

### Makine-okunur ve denetlenebilir özetler

- [Authoritative metrik özeti](reports/authoritative_metrics_summary.csv)
- [Authoritative artefakt kaydı](reports/authoritative_artifact_registry.json)
- [A7 checkpoint/dataset metrikleri](reports/a7_v2_checkpoint_dataset_metrics.csv)
- [Metrik ve artefakt tutarsızlık günlüğü](reports/metric_discrepancy_log.md)
- [Yayın uzlaştırması self-audit](reports/publication_self_audit.md)

## Kapsam ve dürüstlük notu

Bu çalışma gerçek şirket veya çağrı merkezi verisi kullanıldığı iddiasında değildir. Kontrollü sonuçlar açık Türkçe veri setleri ve telefon-benzeri proxy değerlendirmelerinden gelir. Gerçek operasyonel performans; insan doğrulanmış hedef-domain test seti olmadan kesinleştirilemez.

Tam deneyim arşivinde eski gerçek çağrı tecrübelerinden teknik dersler yer alır; ham ses, transcript, kişi adı, dahili ağ yolu, servis kimliği veya şirket altyapı ayrıntısı yayımlanmaz.

A7 step-200, `ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET` yöntemiyle step-150’den tamamlanmıştır. Bu durum sonuçların yorumunda açıkça belgelenmiştir.

## Lisans

Kod iskeleti MIT lisanslıdır. Veri setleri ve modeller kendi lisanslarına tabidir. Model checkpointleri, özel sesler veya erişim kısıtlı artefaktlar bu depoda yayımlanmaz.
