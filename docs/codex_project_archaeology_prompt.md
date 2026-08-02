# Codex Proje Arkeolojisi ve Yayın Hazırlama Promptu

Aşağıdaki prompt, yerel `Whisper ARGE` klasöründeki bütün deney geçmişini, raporları, scriptleri, logları, checkpoint provenance kayıtlarını ve sonuç tablolarını inceleyip paylaşılabilir bir araştırma rehberine dönüştürmek için hazırlanmıştır.

```text
AGENTS.md dosyasını oku.

Proje kökü:

C:\Users\emre\Documents\Whisper ARGE

Amaç:

Bu proje boyunca yapılan bütün Türkçe Whisper araştırmasını eksiksiz biçimde
belgelemek, karşılaştırmak ve paylaşılabilir bir teknik rehber hâline getirmek.

Yalnız en iyi sonucu anlatma. Başarılı, başarısız, sınırlı, reddedilen,
sonradan düzeltilen ve bilimsel olarak inconclusive kalan bütün yöntemleri
kanıtlarıyla kaydet.

Bu görev training veya inference görevi değildir.

YASAKLAR:

- Yeni training başlatma.
- Frozen evaluation veya inference yeniden çalıştırma.
- Audio decode etme; yalnız mevcut metadata/rapor yeterliyse kullan.
- Checkpoint, prediction veya immutable run artefaktını değiştirme.
- Ham audio, transkript, PII, token veya makineye özgü hassas bilgi yayımlama.
- Sonuç veya path uydurma.
- Eski raporları sessizce düzeltme veya silme.
- Git commit/push yapma; yalnız dosyaları hazırla ve finalde değişiklik listesini ver.

## 1. İncelenecek kaynaklar

Aşağıdaki klasör ve dosya türlerini salt okunur incele:

- README.md
- AGENTS.md
- docs/
- reports/
- runs/
- state/
- logs/
- scripts/
- contracts/
- schemas/
- data/manifests/
- data/materialized/
- outputs/evaluation/
- outputs/predictions/
- experiment ledger JSONL/Markdown
- metrics CSV/JSON/Markdown
- checkpoint_lock.json
- evaluation_progress.json
- training_progress.jsonl
- adapter_config.json
- mevcut SHA/hash kayıtları
- danisman_whisper_turkce_genisletilmis_rapor.md

Binary checkpoint ağırlıklarını içerik olarak açma; yalnız path, boyut, hash,
config ve provenance için kullan.

## 2. Önce proje envanteri çıkar

Oluştur:

reports/project_archaeology_inventory.md
reports/project_timeline.md
reports/authoritative_artifact_registry.json

Envanterde her önemli artefakt için:

- deney kimliği
- dosya yolu
- artefakt türü
- oluşturulma/değiştirilme zamanı
- authoritative / stale / superseded / diagnostic sınıfı
- SHA-256 mevcutsa hash
- hangi rapor veya deney tarafından kullanıldığı
- yayınlanabilir mi
- yayınlanmama nedeni

kaydedilsin.

Timestamps tek başına provenance kanıtı sayılmasın. Checkpoint lock, progress,
metric ve raporların birbirleriyle tutarlılığı kontrol edilsin.

## 3. Legacy ve kontrollü seriyi ayır

Legacy seri adları:

- Legacy-H0: baseline
- Legacy-H1: MediaSpeech-only LoRA
- Legacy-H2: General Turkish LoRA
- Legacy-H3: Balanced-phone continuation
- Legacy-H4: Repeat-safe decode

Kontrollü seri:

- A0
- A2
- A3
- A4
- A5
- A6
- A7

Legacy ve kontrollü sonuçları aynı deney protokolüymüş gibi birleştirme.
Her tabloda şu alanları belirt:

- evaluation protokolü
- dataset/split
- inference framework
- decode ayarı
- normalizer
- model/checkpoint
- karşılaştırmanın doğrudan mı tarihsel mi olduğu

## 4. Bütün yöntemleri sınıflandır

Oluştur:

reports/complete_method_inventory.csv
reports/complete_method_inventory.md

Her yöntem için:

- yöntem adı
- kategori: data / training / LoRA scope / augmentation / decoding /
  memory / evaluation / operations
- hipotez
- nerede denendi
- exact config bulunabiliyor mu
- ölçülen sonuç
- faydalı domain
- zarar gören domain
- istatistik desteği
- karar:
  - successful
  - limited
  - failed
  - rejected
  - inconclusive
  - diagnostic_only
- neden işe yaramış olabilir
- neden işe yaramamış olabilir
- yeniden denenecekse hangi koşulda
- makale için ana ders

Aşağıdaki yöntemlerin hiçbirini atlama:

- MediaSpeech-only LoRA
- Common Voice ağırlıklı general Turkish LoRA
- balanced-phone continuation
- encoder+decoder Q/V LoRA
- encoder-only Q/V LoRA
- decoder-only Q/V LoRA
- %10 replay
- zero replay
- TSC source anchor
- staged parent-adapter continuation
- phone-band
- 8 kHz intermediate resampling
- G.711 benzetimi
- speed 0.75
- noise/gain
- universal augmented-output peak guard
- VAD/segmentasyon tarihsel bulguları
- repeat-safe decode
- D3 decode profili
- MEM0, MEM2, MEM3, MEM4
- P7 sonucu
- second decode/retry
- deterministic ITN
- N-best
- raw/normalized WER/CER
- paired bootstrap
- prediction parity ve independent metric recomputation
- data quality audit
- checkpoint/progress/hash sistemi

## 5. Metrik doğrulama

Mevcut prediction artefaktları ve raporlar üzerinden salt okunur doğrulama yap.
Inference yeniden çalıştırma.

Öncelik:

- A0 baseline metrikleri
- A2
- A3 step-50
- A4 en iyi Phone ve robustness checkpointleri
- A5
- A6 corrected results
- A7 step-050/100/150/200

A5–A6 için eski self-comparison sonucunu kullanma.
Eski sıfır-delta raporunu:

SUPERSEDED_DUE_TO_REFERENCE_PATH_BUG

olarak işaretlenmiş tarihsel hata kabul et.

Kaydedilmiş metric ile predictiondan yeniden hesaplanan metric çelişiyorsa:

- prediction artefaktı
- sample ID eşleşmesi
- normalizer implementation
- checkpoint mapping

üzerinden exact nedeni açıkla. Sessizce tek tarafı seçme.

Oluştur:

reports/authoritative_metrics_summary.csv
reports/authoritative_metrics_summary.md
reports/metric_discrepancy_log.md

## 6. “Ne işe yaradı / ne işe yaramadı?” rehberi

Güncelle veya genişlet:

docs/practical_research_guide.md

Rehber şu bölümleri içersin:

1. Ana sonuç
2. Legacy vs kontrollü seri
3. Hızlı karar tablosu
4. Veri yöntemleri
5. LoRA scope sonuçları
6. Replay/anchor sonuçları
7. Augmentasyon sonuçları
8. Decode/inference sonuçları
9. Memory/throughput sonuçları
10. Veri kalite bulguları
11. Başarısızlıkların olası nedenleri
12. Telefon başarısı ile genel Türkçe farkı
13. Operasyonel hatalar
14. Doğru deney sırası
15. Yeni projede uygulanabilir reçete
16. Stop/go karar kuralları
17. Bilimsel olarak açık kalan sorular

Her iddiayı yerel rapor veya artefaktla destekle.
Kanıt bulunmuyorsa “kanıt bulunamadı” yaz.

## 7. Püf noktaları ve doğru uygulama runbooku

Oluştur:

docs/implementation_playbook.md

İçerik:

### Eğitim öncesi

- frozen evaluation hazırlama
- manifest temizleme
- leakage kontrolü
- source/domain metadata kontrolü
- schedule materialization
- deterministic seed
- LoRA scope doğrulama
- base-weight freeze kontrolü

### Augmentasyon

- phone-band işlem sırası
- speed perturbation
- noise SNR
- gain policy
- clipping/overshoot audit
- universal peak guard
- unchanged bucketlara guard uygulamama
- deterministic output/hash

### Training

- smoke test
- first forward/backward sentinel
- gradient kontrolü
- GPU/VRAM kontrolü
- progress flush
- checkpoint cadence
- tek GPU worker

### Checkpoint

- temp directory
- file validation
- atomic rename
- checkpoint lock
- adapter model SHA
- stale checkpoint arşivleme

### Resume

- exact resume ile adapter continuation farkı
- optimizer/scheduler/scaler/RNG durumu
- checkpoint step ile schedule index eşleşmesi
- global LR schedule konumu
- isolated continuation run

### Evaluation

- authoritative checkpoint mapping
- prediction JSONL
- sample ID sırası
- independent metric recomputation
- paired bootstrap
- target-level resume

### Worker izleme

- parent/child PID
- CPU delta
- GPU utilization/VRAM/power
- progress file
- stderr
- stale state tanıma
- görünür terminal kapatma riski

## 8. Hata kataloğu

Oluştur:

docs/failure_catalog.md

Her hata için:

- belirti
- exact neden
- yanlış ilk yorum
- nasıl teşhis edildi
- düzeltme
- tekrarını önleme

Mutlaka dahil et:

- A5–A6 path replacement/self-comparison
- stale RUNNING state
- launcher PID ile gerçek child PID karışması
- debug controlled-stop
- terminal penceresinin kapatılması
- schedule–weight resume mismatch
- pre-existing step-200 overwrite collision
- adapter klasörünü dosya gibi hashleme
- augmentation clipping
- phone-band/resampling overshoot
- unchanged bucketta yanlış peak gate
- stale/superseded checkpoint mapping
- optimizer-reset continuation sınırlaması

## 9. Karar ağacı

Oluştur:

docs/decision_tree.md

Karar ağacı şu sorularla ilerlesin:

- Hedef domain ne?
- Base model yeterli mi?
- Hata akustik mi, decoder/dilsel mi?
- Decoder-only denenmeli mi?
- Encoder-only gerçekten gerekli mi?
- Joint scope ek kazanç üretti mi?
- Replay forgetting’i azalttı mı?
- Staged continuation parentı geçti mi?
- Phone kazancı general-domain kaybına değer mi?
- Prediction parity korundu mu?
- Yeni deney gerçekten yeni bilgi üretecek mi?

Final olası kararlar:

- keep_base
- use_decoder_adapter
- use_staged_phone_adapter
- route_by_domain
- collect_target_evaluation
- stop_open_data_experiments

## 10. Paylaşılabilir yayın belgeleri

Aşağıdaki public dokümanları yerel kanıta göre güncelle:

- README.md
- docs/full_research_report.md
- docs/experiment_catalog.md
- docs/call_oriented_evaluation.md
- docs/negative_results.md
- docs/reproducibility.md
- docs/limitations_and_future_work.md
- docs/artifact_map.md
- docs/practical_research_guide.md
- docs/implementation_playbook.md
- docs/failure_catalog.md
- docs/decision_tree.md

Public belgelerde:

- mutlak Windows path kullanma
- ham audio/transkript kullanma
- özel sample ID yayımlama
- checkpoint dosyası yayımlama
- access token veya gizli metadata yayımlama
- gerçek çağrı merkezi verisi kullanılmış gibi yazma

Public metrikler yalnız doğrulanmış aggregate sonuçlardan gelsin.

## 11. Makale anlatısı

Ana anlatı:

1. Türkçe veri eklemek tek başına başarı değildir.
2. Domain ve veri dengesi kritiktir.
3. Decoder-only güçlü bir Pareto adayıdır.
4. Daha geniş LoRA scope otomatik sinerji sağlamaz.
5. Replay forgetting’i otomatik çözmez.
6. Staged domain adaptation Phone WER’i iyileştirdi.
7. Genel-domain maliyet gerçek ve raporlanmalıdır.
8. Telefon başarısı temiz Türkçe benchmarkıyla aynı değildir.
9. Prediction artefaktı ve independent recomputation zorunludur.
10. Operasyonel provenance hataları bilimsel sonucu geçersiz kılabilir.

Ana sonuçları değiştirme:

- A7 best Phone step-200 normalized WER: 0.154285
- A7 best robustness step-150 normalized WER: 0.147578
- A7 vs A2 Phone: 0.170825 → 0.154285
- A7 vs A4 Phone: 0.158385 → 0.154285
- A7 vs A6 Phone: 0.157203 → 0.154285
- staged_domain_adaptation_supported
- staged_domain_adaptation_with_general_domain_cost
- augmentation_contribution_inconclusive
- OPEN_DATA_EXPERIMENT_LINE_COMPLETED

Bu değerlerde yerel authoritative artefaktla çelişki bulursan değiştirmeden önce
metric discrepancy raporunda kanıtla.

## 12. Son kalite kontrolü

Kontrol et:

- README linkleri çalışıyor mu
- deney isimleri tutarlı mı
- Legacy ve A serisi karışmış mı
- Phone ve robustness checkpointleri doğru mu
- A7 step-200 authoritative isolated continuation mı
- final adapter SHA doğru mu
- path bug eski sonuç olarak mı işaretli
- proxy sonuçlar gerçek çağrı performansı gibi sunuluyor mu
- augmentation bağımsız katkısı yanlışlıkla “kanıtlandı” denmiş mi
- resume exact gibi yanlış sunulmuş mu

## 13. Final cevap formatı

Yalnız şunları ver:

- taranan dosya/artefakt sayısı
- authoritative deney sayısı
- bulunan yeni tutarsızlıklar
- oluşturulan/güncellenen dokümanlar
- en önemli 10 pratik ders
- yayımlanması güvenli dosyalar
- yayımlanmaması gereken dosyalar
- eksik kalan kanıtlar
- önerilen tek sonraki işlem
```
