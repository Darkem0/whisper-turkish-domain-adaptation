Mevcut Whisper AR-GE sistemini yeniden kurma. AGENTS.md dosyasını ve mevcut automation, scripts, protocols, configs, reports, state, runs, evaluation, experiments, ledger, src/whisper_arge ve tests içeriklerini oku.

P0 artifact audit ve P1 immutable evaluation lock tamamlandı. Bunları tekrar çalıştırma.

Bu görevde:

1. state/experiment_queue.json ile state/events.jsonl arasındaki P3-P7 çelişkisini düzelt.
   - Prototip implementasyonu ve unit testinin geçmesi, gerçek deneyin PASSED olması değildir.
   - implementation_status, test_status ve execution_status alanlarını ayır.
   - Eski olayları silme; append-only state_reconciled olayı ekle.
   - İlerleme yüzdesini yalnız gerçek execution durumuna göre düzelt.

2. RTX 4070 SUPER bulunduğu için A3_v2-A6_v2 blocker değerini WAITING_FOR_TRAINING_HOST yerine BLOCKED_TRAINING_CONTRACT olarak düzelt.

3. İnternetten model veya veri indirmeden mevcut yerel artefaktları tara:
   - A0/A1/A2 config ve logları
   - evaluation suite ve lock dosyaları
   - prediction JSON/JSONL dosyaları
   - data registry dosyaları
   - experiments ve ledger kayıtları
   - eski PowerShell scriptleri
   - src/whisper_arge dataset loader kodları
   - config ve loglarda açıkça referans verilen yerel veri yolları
   - mevcut Hugging Face model cache

4. A0/A2 değerlendirmelerinde kullanılan gerçek ses dosyaları erişilebiliyorsa 20-50 örnekten sınırlı immutable inference manifest oluştur:
   - protocols/inference_manifest.jsonl
   - protocols/inference_manifest.lock.json
   - configs/local_paths.yaml
   - reports/inference_manifest_report.md

Manifest alanları:
   sample_id, audio_path, audio_sha256, reference_text,
   reference_sha256, duration_seconds, dataset, split,
   condition, group_id, no_gold_reference.

Path veya veri uydurma. Referans metni olmayan sesi dışlama; no_gold_reference=true yaz. Aynı ses hash'ini iki kez ekleme.

5. Gerçek veri yolu eski konumda kalmışsa configs/local_paths.yaml içinde hangi root mapping'in kullanıcı tarafından doldurulması gerektiğini açıkça göster.

6. D0-D7'yi açmadan önce tek gerçek WAV üzerinde saf Hugging Face Transformers openai/whisper-large-v3-turbo smoke testi çalıştır:
   - yeni backend ekleme
   - torch.inference_mode()
   - mevcut uygun FP16/BF16 davranışı
   - çıktı runs/SMOKE_D0 altında
   - GPU ve VRAM ölçümü
   - JSON çıktı doğrulaması

7. Smoke testi geçerse:
   - D0-D7 BLOCKED durumlarını PENDING yap
   - P3-P7 gerçek execution durumlarını PENDING yap
   - supervisor ve watchdog'u başlat
   - PowerShell watcher'ın gerçek ilerleme gösterdiğini doğrula

8. Decoding deneylerini aynı model, aynı WAV, aynı preprocessing ve aynı manifest üzerinde çalıştır:
   - D0 mevcut ayar
   - D1 beam 1
   - D2 beam 3
   - D3 beam 5
   - D4 previous-text conditioning kapalı
   - D5 previous-text conditioning açık
   - D6 destekleniyorsa temperature fallback 0.0, 0.2, 0.4, 0.6; compression threshold 1.35; logprob threshold -1.0
   - D7 mevcut no-speech threshold ve yalnız bir kontrollü alternatif

Cartesian product çalıştırma. Tek ana değişkenli ablation yap.

9. Gerçek inference çıktıları üzerinde:
   - output quality controller
   - hata türüne göre en fazla bir ikinci decoding geçişi
   - deterministik Türkçe sayı, yüzde, para, tarih, saat ve telefon ITN
   - n-best constrained rescoring
   - MEM0-MEM4 RAM/VRAM ve throughput deneyleri
çalıştır.

Haricî LLM, haricî LM, contextual biasing, hotword veya yeni metin üretimi kullanma.

N-best oracle anlamlı kazanç göstermiyorsa rescoring dalını erken durdur.

10. A2 gerçek artefaktlarından strict training contract üretmeye çalış:
   - contracts/A2_reference.resolved.yaml
   - contracts/A3_v2.clean_replay.yaml
   - contracts/A4_v2.layer_selective.yaml
   - contracts/A5_v2.phone_augmentation.yaml
   - contracts/A6_v2.reproducibility.yaml

Eksik alan uydurma. Her contract için VALID veya açık INVALID nedeni yaz.

11. A3_v2 yalnız contract tamamen VALID ise:
   - base modelden temiz başla
   - A2 adapterinden resume etme
   - A2 ile aynı encoder+decoder q_proj/v_proj ve rank 16
   - A2 ile aynı step ve optimizer
   - yüzde 10 clean replay:
     yüzde 7 Common Voice Scripted train
     yüzde 3 FLEURS train
   - validation/test replay'e girmesin

12. A4_v2:
   - A3 ile aynı replay ve eğitim ayarları
   - son 6 encoder katmanı
   - tüm decoder self-attention ve cross-attention
   - q_proj/v_proj
   - rank 16
   - base modelden temiz başlangıç

13. A5_v2 yalnız repository'de önceden doğrulanmış telefon augmentasyonu varsa çalışsın. Yeni augmentasyon icat etme.

14. A6_v2 yalnız promotion gate geçen en iyi parent seçildikten sonra üç seed ile çalışsın.

15. A3_legacy_aborted_step34_invalid hiçbir koşulda resume veya promotion edilmesin.

16. Git politikası:
   - otomatik commit yapma
   - push yapma
   - remote ekleme
   - branch oluşturma
   - GitHub işlemi yapma
   - büyük veri, model, WAV, cache veya checkpoint dosyasını Git'e ekleme

Ana kayıt alanları state, runs, reports, logs, contracts ve protocols klasörleridir.

17. Test et:
   - state reconciliation
   - prototype testinin experiment PASSED sayılmaması
   - progress hesaplama
   - manifest hash
   - duplicate audio
   - missing path
   - training contract schema
   - leakage
   - legacy A3 resume yasağı
   - PowerShell status parsing
   - supervisor fake-task restart

Tüm pytest ve ruff kontrollerini çalıştır.

18. Şu raporları oluştur veya güncelle:
   - reports/state_reconciliation.md
   - reports/inference_manifest_report.md
   - reports/inference_manifest_blockers.md
   - reports/training_contract_report.md
   - reports/next_executable_stage.md
   - reports/codex-continue-local-summary.md

next_executable_stage.md yalnız şu sonuçlardan birini açıkça yazsın:
   READY_FOR_D0_SMOKE
   READY_FOR_D0_D7
   READY_FOR_A3_V2
   BLOCKED_INFERENCE_PATH
   BLOCKED_MODEL_CACHE
   BLOCKED_TRAINING_CONTRACT
   BLOCKED_MULTIPLE

Koşullar gerçekten sağlanmadan supervisor'ı başlatma veya deneyi tamamlanmış gösterme.

Sonuçta gerçek WAV sayısını, gold referans sayısını, manifest hash'ini, smoke sonucunu, D0-D7 durumunu, P3-P7 durumunu, contract sonuçlarını, sıradaki aşamayı, PID'leri, watcher komutunu ve kalan kesin blocker'ları bildir.
