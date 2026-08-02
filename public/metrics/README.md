# Public Metric Tables

Bu klasör, public repoda yayımlanması güvenli olan, aggregate ve checkpoint-kaynaklı metric tablolarını içerir.

## Dosyalar

- `authoritative_phone_summary.csv`: A0, A2, A4, A5, A6 ve A7 için seçilmiş Phone sonuçları ile A7 robustness sonucu.
- `a7_checkpoint_metrics.csv`: A7’nin dört checkpoint × yedi frozen dataset hedefi ve dört robustness satırı.

## Kaynak ve otorite

A7 satırları frozen evaluation prediction artefaktlarından hesaplanan final tablodan alınmıştır. Prediction SHA-256 değerleri dataset satırlarında korunur. Robustness proxy, MediaSpeech Phone ve G.711 birleştirilmiş aggregate sonuçtur; ayrı prediction hash taşımaz.

## Yorum sınırı

- Phone, G.711 ve robustness sonuçları açık veri telefon proxyleridir.
- Gerçek çağrı merkezi veya şirket performansı değildir.
- A7 step-200, step-150 adapterından `ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET` biçiminde tamamlanmıştır.
- A7 ile A4/A5/A6 arasındaki point delta, staged parent/schedule/augmentasyon farkları nedeniyle tek başına nedensel scope etkisi değildir.
- `cv_spontaneous` örnek sayısı küçüktür; report-only değerlendirilmelidir.

## Yayımlanmayanlar

- ham prediction metinleri,
- audio veya transcript,
- private manifestler,
- model checkpointleri,
- mutlak yerel yollar,
- çağrı kimlikleri veya kişisel veri.

Daha geniş yorum için:

- `docs/full_research_report.md`
- `docs/complete_whisper_experience_archive.md`
- `paper/final_manuscript_tr.md`
