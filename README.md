# Whisper Large-v3-Turbo Türkçe Alan Uyarlaması

Bu depo, `openai/whisper-large-v3-turbo` modelini Türkçe telefon ve karşılıklı konuşma koşullarına uyarlamak için yürütülen açık-veri araştırmasının **kanonik araştırma, makale ve yeniden üretim merkezidir**.

Çalışma üç bilgi katmanını kapsar:

1. **Legacy seri:** genel Türkçe LoRA, balanced-phone continuation ve repeat-safe decode denemeleri.
2. **Kontrollü A0–A7 serisi:** LoRA kapsamı, replay, staged domain adaptation, telefon augmentasyonu ve negatif transfer analizleri.
3. **Tam deneyim arşivi:** 2025–2026 arasındaki erişilebilir ChatGPT hafızası, large-v2/large-v3 fine-tuning tecrübeleri, I3R ses hattı, stereo kanal ayrımı, VAD/diarization, GB10 runtime, decoding/memory araştırmaları ve audio-aware pseudo-label tasarımı.

> Ana sonuç: A7 staged domain adaptation, kontrollü seride en iyi Phone WER sonucunu verdi; ancak CV Scripted gibi genel-domain ölçütlerinde maliyet oluştu. Tek bir adapter bütün Türkçe konuşma türlerinde en iyi değildir.

## Nihai makale

- **[Türkçe Telefon-Benzeri Konuşmalar için Whisper Large-v3-Turbo Uyarlaması](paper/final_manuscript_tr.md)**
- [Tam araştırma raporu](docs/full_research_report.md)
- [Tam Whisper deneyim arşivi](docs/complete_whisper_experience_archive.md)
- [GitHub depo ekosistemi denetimi](docs/repository_ecosystem_audit.md)

Atıf bilgisi: [`CITATION.cff`](CITATION.cff)

## Temel sonuçlar

| Karşılaştırma | Normalize Phone WER |
|---|---:|
| A0 | 0.175690 |
| A2 | 0.170825 |
| A4 | 0.158385 |
| A5 | 0.157968 |
| A6 | 0.157203 |
| **A7 step-200** | **0.154285** |

A7’nin en iyi robustness sonucu:

- **A7 step-150:** `0.147578`

Bilimsel sınıflandırma:

- `staged_domain_adaptation_supported`
- `staged_domain_adaptation_with_general_domain_cost`
- `augmentation_contribution_inconclusive`
- `OPEN_DATA_EXPERIMENT_LINE_COMPLETED`

Aggregate public tablolar:

- [`public/metrics/authoritative_phone_summary.csv`](public/metrics/authoritative_phone_summary.csv)
- [`public/metrics/a7_checkpoint_metrics.csv`](public/metrics/a7_checkpoint_metrics.csv)

## Deney özeti

| Deney | Yöntem | Kısa sonuç |
|---|---|---|
| A0 | Base model | Kontrollü referans |
| A2 | Encoder+decoder Q/V LoRA | Telefon alanında iyileşme, FLEURS maliyeti |
| A3 | Encoder-only + %10 replay | Robustness iyileşti; CV Scripted ciddi kötüleşti |
| A4 | Decoder-only, zero replay | Güçlü Phone ve robustness Pareto adayı |
| A5 | Encoder-only, temiz schedule | Phone iyileşti; A4 robustness seviyesini geçemedi |
| A6 | Encoder+decoder, temiz schedule | A5’ten farklı çıktı; eski zero-delta analizi script hatasıydı |
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
- Hız optimizasyonu prediction çıktısını değiştiriyorsa aynı bilimsel koşul sayılmaz.
- Checkpoint ağırlığı, scheduler ve sample schedule aynı global step’ten devam etmelidir.

## Tek giriş noktası, korunmuş bağımsız repolar

Bu repo bütün araştırmanın kanonik merkezidir. Çalışır public bileşenler bağımsız Git geçmişleriyle korunur:

- **[Turkish Speech Processing Platform](https://github.com/Darkem0/turkish-speech-processing-platform)** — stereo WAV inceleme, kanal split, rol/timestamp merge, duplicate suppression, fixture WER/CER ve local API.
- **[Contact Center AI Evaluation Suite](https://github.com/Darkem0/contact-center-ai-evaluation-suite)** — sentetik diyalog üzerinde typed, evidence-linked downstream değerlendirme.
- **[Research Publications](https://github.com/Darkem0/research-publications)** — kaynak-doğrulamalı yayın metadata kaydı.
- **[Applied AI Engineering Portfolio](https://github.com/Darkem0/applied-ai-engineering-portfolio)** — proje ve kanıt seviyesi dizini.

Commit-kilitli registry:

- [`ecosystem/components.lock.json`](ecosystem/components.lock.json)
- [`ecosystem/README.md`](ecosystem/README.md)

Bütün public bileşenleri aynı yerel çalışma alanına almak için:

```bash
python scripts/bootstrap_public_ecosystem.py --destination components
```

Sadece çalışır speech ve downstream evaluator bileşenleri:

```bash
python scripts/bootstrap_public_ecosystem.py \
  --destination components \
  --include speech_processing contact_center_evaluation
```

Diğer depolar silinmez veya zorla merge edilmez. Bu yapı tek bir kanonik giriş noktası sağlar ve companion repo geçmişlerini korur.

## Hızlı başlangıç

Araştırma deposunun sentetik ve dependency-free varsayılan yolu:

```bash
python -m whisper_adaptation demo
python -m whisper_adaptation evaluate --manifest experiments/adapter-routing.json
python -m unittest discover -s tests -v
```

Bu komutlar model indirmez ve tarihsel A0–A7 metriklerini yeniden üretme iddiası taşımaz. Varsayılan fixture, araştırma sözleşmesini ve metric kodunu gösterir.

## Tam ChatGPT Whisper deneyim arşivi

Aşağıdaki belgeler yalnız mevcut proje serisini değil, erişilebilen bütün Whisper çalışma geçmişini kapsar:

- [Tam Whisper deneyim arşivi](docs/complete_whisper_experience_archive.md)
- [Whisper deneyim zaman çizelgesi](docs/whisper_experience_timeline.md)
- [Araştırılan ve uygulanan yöntemler matrisi](docs/research_vs_executed_matrix.md)
- [ChatGPT hafızası kapsamı ve redaksiyon](docs/chatgpt_memory_provenance.md)

Arşiv, erişilebilen ChatGPT hafızası ve yüklenmiş kaynaklar içinde mümkün olan en geniş sentezdir. Silinmiş, indekslenmemiş veya erişilemeyen eski sohbetlerin eksiksiz kapsandığı iddia edilmez.

## Pratik başlangıç noktaları

- **Sonuçları ve gerekçeleri öğrenmek için:** [Ne işe yaradı, ne işe yaramadı?](docs/practical_research_guide.md)
- **Yerel proje klasörünü baştan sona analiz ettirmek için:** [Codex proje arkeolojisi promptu](docs/codex_project_archaeology_prompt.md)
- **Bütün deneyleri hızlı karşılaştırmak için:** [Deney kataloğu](docs/experiment_catalog.md)
- **Hataları tekrar etmemek için:** [Negatif sonuçlar ve araştırma hataları](docs/negative_results.md)
- **Repo/branch birleştirme kararını görmek için:** [Ekosistem denetimi](docs/repository_ecosystem_audit.md)

## Dokümantasyon

### Nihai yayın

- [Final makale](paper/final_manuscript_tr.md)
- [GitHub depo ekosistemi denetimi](docs/repository_ecosystem_audit.md)
- [Public metric tabloları](public/metrics/README.md)

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

## Kapsam ve dürüstlük notu

Bu çalışma gerçek şirket veya çağrı merkezi verisi kullanıldığı iddiasında değildir. Kontrollü sonuçlar açık Türkçe veri setleri ve telefon-benzeri proxy değerlendirmelerinden gelir. Gerçek operasyonel performans; insan doğrulanmış hedef-domain test seti olmadan kesinleştirilemez.

Tam deneyim arşivinde eski gerçek çağrı tecrübelerinden teknik dersler yer alır; ham ses, transcript, kişi adı, dahili ağ yolu, servis kimliği veya şirket altyapı ayrıntısı yayımlanmaz.

A7 step-200, `ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET` yöntemiyle step-150’den tamamlanmıştır. Bu durum sonuçların yorumunda açıkça belgelenmiştir.

## Gizlilik ve yayımlanmayan artefaktlar

Bu depoda şunlar yer almaz:

- ham ses ve özel transkript,
- model checkpointi veya adapter ağırlığı,
- token, secret ve `.env`,
- private manifest ve materialized veri,
- mutlak yerel/sunucu yolları,
- müşteri veya çalışan kimliği,
- dahili servis topolojisi.

## Lisans

Kod iskeleti MIT lisanslıdır. Veri setleri ve modeller kendi lisanslarına tabidir. Model checkpointleri, özel sesler veya erişim kısıtlı artefaktlar bu depoda yayımlanmaz.
