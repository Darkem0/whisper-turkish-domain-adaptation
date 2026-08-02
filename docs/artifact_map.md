# Artefakt Haritası

Bu dosya, yayımlanabilir dokümantasyon ile yerel/özel artefaktlar arasındaki sınırı açıklar.

## Public dokümantasyon

- `README.md`: ana sonuçlar ve proje özeti
- `docs/full_research_report.md`: tam araştırma anlatısı
- `docs/experiment_catalog.md`: Legacy ve A0–A7 deney envanteri
- `docs/call_oriented_evaluation.md`: telefon/çağrı odaklı değerlendirme çerçevesi
- `docs/negative_results.md`: başarısız yöntemler ve operasyonel hatalar
- `docs/reproducibility.md`: sabitlenen ayarlar, hash ve resume notları
- `docs/limitations_and_future_work.md`: sınırlamalar ve sonraki araştırma seçenekleri

## Yerel authoritative raporlar

Yerel çalışma dizininde aşağıdaki rapor aileleri nihai tabloların kaynağıdır:

- A7 frozen evaluation integrity
- A7 checkpoint/dataset metrics
- A7 checkpoint trajectory
- A7 comparative analysis
- A7 statistical analysis
- A0–A7 metrics comparison
- final method inventory
- final positive results
- final negative results
- final reproducibility and failures
- research experiment ledger

Bu raporlar makineye özgü yollar veya yayımlanmaması gereken artefakt referansları içerebileceğinden doğrudan public depoya kopyalanmadan önce redaksiyon gerektirir.

## Yayımlanmayan model artefaktları

- A2/A3/A4/A5/A6/A7 LoRA checkpointleri
- optimizer/scaler state
- local checkpoint lock dosyalarının mutlak yol içeren sürümleri
- prediction JSONL dosyalarının veri lisansına bağlı kopyaları
- ses dosyaları ve transkriptler

## A7 authoritative mapping

| Checkpoint | Kaynak |
|---|---|
| step-050 | original A7 run |
| step-100 | original A7 run |
| step-150 | original A7 run |
| step-200 | isolated resume150 final continuation |

Final A7 adapter SHA:

`fa5aa88e3d7fd1c16b7b7cdb0c516bc7d49210f3c5cb63c8405f280bad9e4894`

## Yayın güvenliği

Public commitlerden önce aşağıdakiler taranmalıdır:

- `C:\Users\...` gibi mutlak yollar,
- token ve erişim anahtarları,
- ham transkriptler,
- ses dosyaları,
- kişisel veri,
- özel kurum/proje adları,
- lisansı belirsiz dataset kopyaları,
- büyük checkpoint dosyaları.

## Sonuçların izlenebilirliği

README’deki ana sayılar:

- A7 Phone step-200: `0.154285`
- A7 robustness step-150: `0.147578`
- A2 Phone: `0.170825`
- A4 Phone: `0.158385`
- A6 Phone: `0.157203`

nihai A7 karşılaştırma raporlarından türetilmiştir. Public depo, bu sayıları gerçek şirket veya özel çağrı verisi sonucu olarak sunmaz.
