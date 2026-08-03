# Whisper Türkçe ASR Legacy Project Handoff

**Denetim tarihi:** 30 Temmuz 2026  
**Denetim kapsamı:** Önceki Whisper large-v3-turbo Türkçe ASR çalışmaları, yerel dosya kalıntıları, geçmiş çalışma notları ve yeniden kullanılabilir kodlar.  
**Denetim kısıtı:** Bu denetimde yeni deney çalıştırılmadı, model veya veri indirilmedi, eğitim başlatılmadı, mevcut dosyalar silinmedi ve mevcut deney dosyaları değiştirilmedi.

## 1. Kritik durum özeti

Çalışmanın şu anda önerilen ana klasörü:

`%USERPROFILE%\Documents\Whisper ARGE`

Bu klasör mevcut ve `.git` dizini içeriyor; ancak denetim anında çalışma kodu, veri, manifest, model veya rapor dosyası içermiyordu. `docs` klasörü ve bu handoff belgesi bu denetim kapsamında oluşturuldu.

Önceki deneylerin çalışma klasörü olarak geçmiş kayıtlarda geçen yol:

`%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr`

Bu yol denetim sırasında diskte bulunamadı. Dolayısıyla aşağıdaki deney sonuçları ve dosya yolları iki ayrı sınıfa ayrılmıştır:

- **Diskte doğrulanan:** Denetim sırasında gerçek dosya sistemi üzerinde bulunan dosyalar.
- **Geçmiş deney kaydından bilinen fakat disk üzerinde doğrulanamayan:** Önceki çalışma oturumunun kayıtlarında bulunan, fakat ilgili klasör artık mevcut olmadığı için yeniden açılıp hash/path doğrulaması yapılamayan öğeler.

Bu ayrım makalede önemlidir: diskte bulunmayan çıktılar yeniden üretilebilirlik arşivi olarak kabul edilmemeli, yalnızca geçmiş deney kaydı olarak belirtilmelidir.

## 2. Ana proje ve ilgili klasörler

| Rol | Windows yolu | Durum |
|---|---|---|
| Yeni ana ARGE klasörü | `%USERPROFILE%\Documents\Whisper ARGE` | Diskte mevcut; boş Git deposu |
| Eski deney çalışma kökü | `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr` | Diskte bulunamadı |
| Eski deney çıktı kökü | `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter` | Diskte bulunamadı |
| Minimal Whisper prototipi | `<legacy-prototype-root>` | Diskte mevcut |
| Temizlenmiş araştırma iskeleti | `%USERPROFILE%\Documents\Codex\2026-07-22\read-the-attached-emre-aslan-codex\work\overhaul-repos\whisper-turkish-domain-adaptation` | Diskte mevcut; gerçek ses/eğitim çıktısı içermiyor |
| Kullanıcı test sesi | `%USERPROFILE%\Desktop\test.mp3` | Diskte mevcut; yaklaşık 3.55 MB |

`%USERPROFILE%\Documents\Whisper ARGE` ile `<legacy-prototype-root>` aynı çalışma ağacının devamı olarak doğrulanamadı. Bunlar ayrı konumlardır.

## 3. Python ortamları ve requirements dosyaları

### Geçmiş deney ortamı

Önceki deney kaydında kullanılan sanal ortam yolu:

`%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\.venv`

İlgili deney klasörü bulunamadığı için bu sanal ortam denetim sırasında doğrulanamadı.

### Diskte bulunan Python/proje tanımları

- `<legacy-prototype-root>\.venv` denetimde bulunamadı.
- `<legacy-prototype-root>\requirements.txt` denetimde bulunamadı. README içinde bu dosyaya referans var, fakat dosyanın kendisi yok.
- Temizlenmiş iskeletin proje tanımı: `%USERPROFILE%\Documents\Codex\2026-07-22\read-the-attached-emre-aslan-codex\work\overhaul-repos\whisper-turkish-domain-adaptation\pyproject.toml`
- Bu `pyproject.toml` yalnızca temel paket metadata'sı içeriyor; Whisper eğitim/inference bağımlılıklarının tam kilitli listesini içermiyor.
- Denetimde proje köküne ait `requirements.txt` veya `environment.yml` bulunamadı.

Geçmiş deneylerde kullanılan paket ailesi kayıtlarına göre: PyTorch CUDA, Transformers, Datasets, PEFT, Evaluate, librosa, soundfile, faster-whisper ve jiwer kullanılmıştır. Sürüm kilitleri ve `pip freeze` çıktısı diskte bulunmadığı için sürüm bazlı yeniden üretilebilirlik sağlanamıyor.

## 4. Eğitim scriptleri

### Geçmiş deney scriptleri: disk üzerinde bulunamadı

Aşağıdaki yollar önceki deney kaydında kullanılmış, ancak eski çalışma köküyle birlikte artık doğrulanamamıştır:

- `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\src\train_lora_whisper.py`
- `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\src\build_commonvoice_manifest.py`
- `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\src\build_mediaspeech_manifest.py`
- `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\src\make_balanced_manifest.py`
- `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\src\merge_manifests.py`
- `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\src\build_hf_asr_manifest.py`

### Diskte bulunan eski/minimal eğitim dosyası

- `<legacy-prototype-root>\train_whisper.py`

Bu dosya denetimde boş veya tamamlanmamış görünüyor; tek başına geçmiş LoRA eğitimlerini yeniden çalıştıracak durumda olduğu doğrulanamadı.

## 5. Evaluation ve normalizasyon scriptleri

### Geçmiş deney scriptleri: disk üzerinde bulunamadı

- `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\src\evaluate_whisper.py`
- `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\src\evaluate_lora_whisper.py`
- `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\src\evaluate_user_reference.py`
- `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\src\evaluate_text_metrics.py`
- `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\src\compare_prediction_metrics.py`
- `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\src\normalize_tr.py`
- `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\src\transcribe_faster_whisper.py`
- `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\src\transcribe_lora_whisper.py`

### Diskte bulunan prototip evaluation/inference dosyaları

- `<legacy-prototype-root>\eval.py`
- `<legacy-prototype-root>\inference.py`

Bu iki dosya `jiwer`, `datasets`, `transformers`, `torch` ve `soundfile` kullanıyor; ancak Türkçe normalizasyon, VAD, uzun çağrı bölütleme, LoRA adapter yükleme ve tekrar güvenli çözümleme özellikleri içermiyor.

### Yeniden kullanılabilir temiz araştırma kodu

`%USERPROFILE%\Documents\Codex\2026-07-22\read-the-attached-emre-aslan-codex\work\overhaul-repos\whisper-turkish-domain-adaptation\whisper_adaptation` altında şu modüller mevcut:

- `metrics.py`: raw/normalized WER-CER hesabı için küçük yardımcılar.
- `repeat_safe.py`: tekrar döngülerini sınırlayan çözümleme mantığı.
- `segmentation.py`: bölütleme koşullarını kaydetmeye yönelik yardımcı.
- `routing.py`: base model / adapter routing hipotezi.
- `experiments.py`: deney tanımı ve kayıt iskeleti.
- `cli.py`: iskelet komut satırı arayüzü.

Bu repo gerçek Whisper eğitimi veya gerçek ses inference'ı çalıştırmıyor; temiz oda araştırma iskeletidir.

## 6. İndirilen veri setleri ve yerel yollar

### Geçmiş deneyde kullanıldığı kaydedilen veri setleri

Aşağıdaki yollar artık disk üzerinde doğrulanamadı:

- MediaSpeech TR arşivi: `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\work\datasets\mediaspeech\TR.tgz`
- MediaSpeech TR çıkarılmış klasörü: `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\work\datasets\mediaspeech\TR`
- Common Voice dışa aktarılmış sesleri: `%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\work\datasets\commonvoice17_fixed_audio`

Kaynak kayıtları:

- MediaSpeech TR: [OpenSLR SLR108](https://www.openslr.org/108/)
- Common Voice TR sabitlenmiş veri: [ysdede/commonvoice_17_tr_fixed](https://huggingface.co/datasets/ysdede/commonvoice_17_tr_fixed)
- FLEURS TR: [google/fleurs](https://huggingface.co/datasets/google/fleurs)
- Khan Academy Türkçe: [ysdede/khanacademy-turkish](https://huggingface.co/datasets/ysdede/khanacademy-turkish)
- Khan Academy Türkçe matematik: [ysdede/khanacademy-turkish-math](https://huggingface.co/datasets/ysdede/khanacademy-turkish-math)

### Denetimde doğrulanan model cache'i

`%USERPROFILE%\.cache\huggingface\hub` altında şu model cache klasörleri mevcut:

- `models--openai--whisper-large-v3-turbo`
- `models--openai--whisper-large-v3`
- `models--mobiuslabsgmbh--faster-whisper-large-v3-turbo`
- `models--Systran--faster-whisper-large-v3`
- `models--Sercan--distil-whisper-large-v3-tr`

Bu cache klasörleri model indirmelerinin izidir; geçmiş veri setlerinin ve LoRA adapterlerinin mevcut olduğunu göstermez.

## 7. Manifestler

Geçmiş deney kaydında üretilen manifestler ve kaydedilen satır sayıları:

| Manifest | Satır | Süre | Disk durumu |
|---|---:|---:|---|
| `data/manifests/mediaspeech/train.jsonl` | 2.010 | 8,01 saat | Bulunamadı |
| `data/manifests/mediaspeech/validation.jsonl` | 251 | 1,01 saat | Bulunamadı |
| `data/manifests/mediaspeech/test.jsonl` | 252 | 0,99 saat | Bulunamadı |
| `data/manifests/commonvoice17_fixed/train.jsonl` | 26.501 | 19,84 saat | Bulunamadı |
| `data/manifests/commonvoice17_fixed/validation.jsonl` | 8.639 | 6,27 saat | Bulunamadı |
| `data/manifests/commonvoice17_fixed/test.jsonl` | 9.650 | 7,33 saat | Bulunamadı |
| `data/manifests/general_tr/train.jsonl` | 28.511 | 27,84 saat | Bulunamadı |
| `data/manifests/general_tr/validation.jsonl` | 8.890 | 7,27 saat | Bulunamadı |
| `data/manifests/general_tr/test.jsonl` | 9.902 | 8,32 saat | Bulunamadı |
| `data/manifests/general_tr_fast/test.jsonl` | 1.000 | 0,83 saat | Bulunamadı |
| `data/manifests/balanced_phone/train.jsonl` | 14.606 | 24,01 saat | Bulunamadı |
| `data/manifests/user_test.jsonl` | 1 | yaklaşık 9,38 dk | Bulunamadı |
| `data/manifests/external_eval/external_tr_360.jsonl` | 360 | 1,08 saat | Bulunamadı |

Manifestlerin içerik hash'leri, ses referansları ve veri seti revision bilgileri mevcut diskte bulunmadığından doğrulanamamıştır.

## 8. Prediction JSONL dosyaları

Geçmiş deney kaydında adı geçen, fakat mevcut dosya sisteminde bulunamayan prediction çıktıları:

- `outputs/predictions/user_test_large_v3_turbo.jsonl`
- `outputs/predictions/user_test_large_v3.jsonl`
- `outputs/predictions/user_test_distil_large_v3_tr.jsonl`
- `outputs/predictions/user_test_faster_large_v3_turbo_vad.json`
- `outputs/predictions/user_test_faster_large_v3_vad.json`
- `outputs/predictions/user_test_lora_balanced_phone_from750_chunked.json`
- `outputs/predictions/user_test_lora_balanced_phone_from750_chunked_repeat_safe.json`
- `outputs/predictions/external360_baseline_large_v3_turbo.jsonl`
- `outputs/predictions/external360_lora_mediaspeech_1epoch.jsonl`
- `outputs/predictions/external360_lora_general_checkpoint750.jsonl`
- `outputs/predictions/external360_lora_balanced_phone_final.jsonl`

## 9. Checkpoint ve LoRA adapter yolları

Geçmiş kayıtlarda geçen adapter ve checkpoint yolları:

- `outputs/models/whisper-large-v3-turbo-tr-mediaspeech-1epoch-lora`
- `outputs/models/whisper-large-v3-turbo-general-tr-2epoch-lora/checkpoint-750`
- `outputs/models/whisper-large-v3-turbo-balanced-phone-from750-lora`
- `outputs/models/whisper-large-v3-turbo-balanced-phone-from750-lora/checkpoint-500`
- `outputs/models/whisper-large-v3-turbo-balanced-phone-from750-lora/checkpoint-913`

Tam Windows karşılıkları geçmiş çalışma köküne göre şöyleydi:

`%USERPROFILE%\Documents\Codex\2026-07-07\se-ti-im-bir-bug-pr\outputs\whisper_tr_callcenter\outputs\models\...`

Bu klasörler ve `trainer_state.json` dosyaları denetim sırasında bulunamadı. Yalnızca model cache'inde base Whisper modelleri doğrulanmıştır; LoRA adapteri doğrulanmamıştır.

## 10. Tamamlanan deneyler

Aşağıdaki sınıflandırma geçmiş çalışma kaydına dayanır; çıktı dosyaları mevcut olmadığından bu bölümün sonuçları arşivlenmiş deney notu statüsündedir.

### A0: Base model baseline

Model: `openai/whisper-large-v3-turbo`.

Tamamlandı olarak kaydedilen koşular:

- MediaSpeech TR test.
- General hızlı test.
- External TR 360 test: FLEURS TR, Khan Academy TR ve Khan Academy matematik alt kümeleri.
- Kullanıcının `%USERPROFILE%\Desktop\test.mp3` ses kaydı üzerinde inference.

### A1: MediaSpeech-only LoRA, 1 epoch

Adapter eğitimi tamamlandı olarak kaydedildi. MediaSpeech testinde normalized WER:

- Baseline: `0,1558`
- MediaSpeech LoRA: `0,2162`
- Değişim: yaklaşık `%38,8` kötüleşme

Bu deney tekrar kullanılmaması gereken adaylardan biridir; aynı veri/ayarlarla tekrar çalıştırılması araştırma açısından düşük önceliklidir.

### A2: General Turkish LoRA, 2 epoch hedefi

Deney tamamen bitmedi. Eğitim yaklaşık `global_step=750`, `epoch=0,4209` seviyesinde kesildi. Bu nedenle “2 epoch tamamlandı” şeklinde raporlanmamalıdır.

Kayıtlı general hızlı test sonucu, Common Voice normalized WER'de iyileşme; MediaSpeech alt kümesinde ise gerileme göstermiştir.

### A3: Balanced phone LoRA, checkpoint-750'dan devam

`checkpoint-913` seviyesine kadar tamamlandı olarak kaydedildi; 14.606 örnek ve yaklaşık 24,01 saatlik balanced phone manifest kullanıldı.

General hızlı test normalized WER:

| Alt küme | Base | General ckpt-750 | Balanced phone final |
|---|---:|---:|---:|
| Common Voice | 0,1837 | 0,1368 | 0,1241 |
| MediaSpeech | 0,1601 | 0,1718 | 0,1366 |

Bu testte balanced phone adapter en iyi sonucu verdi. Ancak bu başarı tüm alanlara genellenemedi.

### A4: Uzun telefon çağrısı ve repeat-safe çözümleme

Kullanıcı sesinde ilk balanced phone chunked çıktı “ama ama” tekrar döngüsü üretti; kayıtta 107 tekrar bulunduğu not edildi. `no_repeat_ngram_size=4` ve `repetition_penalty=1,08` içeren repeat-safe koşulda bu tekrar sayısı sıfıra indirildi.

Referansın yaklaşık 9:06'ya kadar olan bölümü için normalized WER:

- LoRA ilk çözümleme: `0,8469`
- LoRA repeat-safe: `0,6466`
- İyileşme: yaklaşık `%23,7` göreli
- Faster Whisper turbo VAD: `0,6568`

Bu, uzun telefon çağrısında decoding/VAD koşullarının yalnızca model adapteri kadar önemli olduğunu gösteren tamamlanmış bir deneydir. Kullanıcı referansının gürültülü/ham niteliği nedeniyle mutlak WER değeri dikkatle yorumlanmalıdır.

### A5: External TR 360 doğrulaması

Bu koşul negatif transferi gösterdi:

| Model | Normalized WER | Normalized CER |
|---|---:|---:|
| Base large-v3-turbo | 0,0857 | 0,0283 |
| MediaSpeech LoRA 1 epoch | 0,0853 | 0,0287 |
| General LoRA checkpoint-750 | 0,0957 | 0,0316 |
| Balanced phone LoRA final | 0,1018 | 0,0344 |

External clean/read/lecture ağırlıklı bu sette base model en iyi normalized WER değerini vermiştir. MediaSpeech LoRA pratik olarak aynı seviyede kalmış, general ve balanced phone adapterleri gerilemiştir.

## 11. Başarısız, yarım kalan veya olumsuz sonuçlanan deneyler

- MediaSpeech-only LoRA, MediaSpeech normalized WER'i baseline'a göre kötüleştirdi.
- General Turkish LoRA için hedeflenen 2 epoch tamamlanmadı; yalnızca checkpoint-750 değerlendirildi.
- İlk balanced phone chunked çözümleme tekrarlı çıktı üretti; repeat-safe ayar olmadan üretim için uygun değildir.
- Balanced phone LoRA external360 üzerinde normalized WER'i baseline'a göre yaklaşık `%18,8` artırdı; bu negatif transferdir.
- Temiz dış doğrulama verisinde “fine-tune edilmiş her model base modelden iyidir” varsayımı doğrulanmadı.
- Gerçek bankacılık çağrısı verisiyle deney yapılmadı; bankacılık alanı için sonuç iddiası kurulamaz.
- Tam veri ve checkpoint arşivi kaybolduğu/taşındığı için deneyler şu anda bağımsız olarak yeniden üretilemiyor.

## 12. Raporda geçen fakat diskte bulunamayan dosyalar

Toplu olarak aşağıdaki geçmiş raporlar da bulunamadı:

- `outputs/danisman_whisper_turkce_ara_rapor.md`
- `outputs/danisman_whisper_turkce_genisletilmis_rapor.md`
- `outputs/danisman_mail_metni.md`
- `outputs/danisman_mail_metni_genisletilmis.md`
- `outputs/evaluation/test_mp3_reference_evaluation_tr.md`
- `outputs/evaluation/user_test_reference_metrics.md`
- `outputs/evaluation/user_test_reference_metrics_to_9m06.md`
- `outputs/evaluation/external360_model_evolution_metrics.md`
- `outputs/evaluation/external360_model_evolution_metrics.json`
- `outputs/general_tr_training_report.md`
- `outputs/mediaspeech_experiment_report.md`

Bu dosyaların geçmiş içerikleri önceki çalışma kaydında özetlenmiş olsa da dosya bütünlüğü, son düzenleme tarihi ve hash doğrulanamıyor.

## 13. Yeniden kullanılabilecek kodlar

Öncelikli olarak korunması gereken mevcut kod:

- `%USERPROFILE%\Documents\Codex\2026-07-22\read-the-attached-emre-aslan-codex\work\overhaul-repos\whisper-turkish-domain-adaptation\whisper_adaptation\metrics.py`
- `%USERPROFILE%\Documents\Codex\2026-07-22\read-the-attached-emre-aslan-codex\work\overhaul-repos\whisper-turkish-domain-adaptation\whisper_adaptation\repeat_safe.py`
- `%USERPROFILE%\Documents\Codex\2026-07-22\read-the-attached-emre-aslan-codex\work\overhaul-repos\whisper-turkish-domain-adaptation\whisper_adaptation\segmentation.py`
- `%USERPROFILE%\Documents\Codex\2026-07-22\read-the-attached-emre-aslan-codex\work\overhaul-repos\whisper-turkish-domain-adaptation\whisper_adaptation\routing.py`
- `%USERPROFILE%\Documents\Codex\2026-07-22\read-the-attached-emre-aslan-codex\work\overhaul-repos\whisper-turkish-domain-adaptation\whisper_adaptation\experiments.py`
- `<legacy-prototype-root>\eval.py`
- `<legacy-prototype-root>\inference.py`

Geçmişte kullanılan ancak artık fiziksel olarak bulunmayan scriptlerin mantığı da yeniden kurulabilir: manifest üretimi, Türkçe normalizasyon, base/LoRA karşılaştırması, VAD, uzun ses chunking, repeat-safe decoding ve group-by domain metric raporlaması.

## 14. Tekrar çalıştırılmaması gereken deneyler

Mevcut kanıta göre aşağıdaki koşullar aynı biçimde tekrar çalıştırılmamalıdır:

- Yalnızca MediaSpeech TR üzerinde 1 epoch LoRA eğitimi.
- Dış doğrulama yapılmadan general veya balanced phone LoRA'yı “genel Türkçe modeli” olarak kabul etmek.
- Uzun çağrıyı VAD/chunking olmadan tek parça Transformers pipeline'ına vermek.
- `no_repeat_ngram_size` ve repetition penalty olmadan balanced phone chunked çözümlemeyi üretim koşulu saymak.
- Hedef epoch sayısını doğrulama metriği olmadan 5'e çıkarmak.
- Gerçek bankacılık/telefon verisi olmadan bankacılık başarımı iddiası kurmak.
- Arşivlenmiş manifest, model revision, normalizer ve decoding ayarları olmadan eski sonuçları birebir yeniden üretilebilir kabul etmek.

## 15. Gelecek çalışma için güvenli başlangıç noktası

Yeni deney başlatılacağı zaman önce şu arşivleme adımları tamamlanmalıdır:

1. `%USERPROFILE%\Documents\Whisper ARGE` altında `src`, `data`, `models`, `outputs`, `docs` ve `configs` klasörlerini oluşturmak.
2. Python sürümünü, CUDA/PyTorch sürümünü ve tam `pip freeze` çıktısını kilitlemek.
3. Her manifesti veri seti revision'ı, lisans, split, satır sayısı, toplam süre ve SHA-256 ile arşivlemek.
4. Base model ve her adapter için model config, tokenizer/processor, training args ve checkpoint trainer state dosyalarını saklamak.
5. En az üç ayrı doğrulama grubunu korumak: temiz okuma, genel konuşma ve telefon/gürültülü konuşma.
6. Raw WER/CER ile normalized WER/CER'i birlikte raporlamak; ayrıca sayı, para, tarih, IBAN ve özel isim alt metrikleri eklemek.
7. Base modeli her deneyde sabit referans olarak çalıştırmak; yalnızca tek bir alt kümede iyileşen adapteri genel üstün model olarak adlandırmamak.
8. Bankacılık verisi geldiğinde PII/consent/lisans ve saklama politikasını deney başlamadan belgelemek.

## 16. Sonuç

Denetim sonucunda geçmiş çalışmanın teknik olarak değerli bir deney kaydı bulunduğu, fakat ham deney arşivinin şu anki bilgisayarda erişilebilir bir proje klasörü halinde olmadığı görülmüştür. En güçlü geçmiş bulgu balanced phone LoRA + repeat-safe/VAD çözümlemenin telefon benzeri testte fayda sağlayabilmesidir. En önemli karşı bulgu ise aynı adapterin temiz external doğrulama setlerinde base `large-v3-turbo` modelinden kötü sonuç vermesidir.

Bu nedenle mevcut durumda önerilecek modelleme politikası tek bir “her yerde en iyi” model değil, doğrulama ile seçilen koşullu kullanım yaklaşımıdır: temiz/okuma konuşmada base model, telefon/gürültülü konuşmada uygunluğu kanıtlanmış adapter ve repeat-safe decoding; nihai bankacılık iddiası ise gerçek ve elle düzeltilmiş çağrı verisi elde edilene kadar ertelenmelidir.

