# Codex Prompt — Kalan Yerel Whisper Artefaktlarını Kanonik Repoyla Uzlaştırma

Aşağıdaki prompt, GitHub’da yayımlanan kanonik depo tamamlandıktan sonra yerel `Whisper ARGE` klasöründe kalmış olabilecek benzersiz ve public-safe artefaktları denetlemek için kullanılmalıdır.

```text
AGENTS.md dosyasını oku.

Yerel proje kökü:
C:\Users\emre\Documents\Whisper ARGE

Kanonik GitHub deposu:
Darkem0/whisper-turkish-domain-adaptation

Amaç:
Yerel çalışma klasöründe olup kanonik GitHub main üzerinde bulunmayan, gerçekten
benzersiz, doğrulanabilir ve public-safe Whisper araştırma içeriğini seçici olarak
aktarmak. Mevcut kapsamlı belgeleri kısa veya eksik sürümlerle değiştirme.

YASAK:
- dirty worktree üzerinde branch değiştirme
- stash/reset/clean/restore
- force push
- --allow-unrelated-histories
- main’e doğrudan push
- WAV/transkript/checkpoint/cache/log/state yükleme
- özel path, IP, hostname, port, credential, PII yayımlama
- yeni training/inference/evaluation çalıştırma

1. ORİJİNAL WORKTREE’Yİ SALT OKUNUR TUT

Yalnız incele:
- README.md
- docs/
- reports/
- scripts/
- contracts/
- schemas/
- evaluation/
- experiments/
- ledger/
- public-safe config ve metric özetleri

Aşağıdakilerin içeriğini public olarak kopyalama:
- runs/
- logs/
- state/
- outputs/
- data/materialized/
- model cache
- checkpoint/adapter
- raw prediction text
- audio/transcript

2. TEMİZ SECOND WORKTREE KULLAN

git fetch origin main:refs/remotes/origin/main

git worktree add -b codex/final-local-reconciliation \
  "C:\Users\emre\Documents\Whisper-ARGE-final-reconciliation" \
  origin/main

Bütün edit/commit/push yalnız bu temiz worktree içinde yapılmalı.

3. KANONİK MAIN’İ İNCELE

Önce şu dosyaları oku:
- README.md
- paper/final_manuscript_tr.md
- docs/repository_ecosystem_audit.md
- docs/canonical_system_architecture.md
- docs/complete_whisper_experience_archive.md
- docs/whisper_experience_timeline.md
- docs/research_vs_executed_matrix.md
- docs/practical_research_guide.md
- docs/negative_results.md
- docs/reproducibility.md
- public/metrics/*.csv
- ecosystem/components.lock.json

4. YEREL DOSYA SINIFLANDIRMASI

Her aday dosya için:
- UNIQUE_PUBLIC_EVIDENCE
- DUPLICATE_OF_MAIN
- SUPERSEDED
- PRIVATE_LOCAL_TOOL
- GENERATED_INTERMEDIATE
- CONTAINS_PRIVATE_PATH
- CONTAINS_AUDIO_OR_TRANSCRIPT
- NOT_VERIFIABLE
- RESEARCHED_NOT_EXECUTED

kararı ver.

5. KANIT ÖNCELİĞİ

1. prediction/checkpoint SHA
2. prediction’dan yeniden hesaplanan metric
3. progress ve integrity raporu
4. düzeltilmiş final rapor
5. arşiv raporu
6. ChatGPT hafızası
7. plan/öneri

Çelişkiyi sessizce çözme; discrepancy loguna yaz.

6. ZORUNLU KONTROLLER

- A7 Phone step-200 ≈ 0.1542845229
- A7 robustness step-150 ≈ 0.1475780110
- A7 frozen evaluation 28/28
- A7 final adapter SHA mevcut public kayda uyuyor
- A7 step-200 optimizer-reset continuation
- A5–A6 eski zero-delta sonucu SUPERSEDED
- 4.059 farklı prediction ve 27/28 farklı aggregate metric
- MEM2 microbenchmark-positive / deployment-inconclusive
- MEM3/MEM4 prediction drift nedeniyle reddedilmiş
- Legacy ve kontrollü seri karıştırılmamış

7. GİZLİLİK TARAMASI

Tracked olacak bütün dosyalarda ara:
- C:\Users\
- /home/
- özel IP/hostname
- token/secret/password
- gerçek kişi/müşteri adı
- telefon/IBAN/kart/hesap
- private checkpoint veya cache yolu
- internal project/service/database bilgisi

Bulunan private içerik redakte edilemiyorsa dosyayı yayımlama.

8. YALNIZ BENZERSİZ İÇERİĞİ EKLE

Tercih sırası:
- mevcut kapsamlı belgeye küçük doğrulanmış bölüm eklemek
- public/metrics altında aggregate tablo eklemek
- yeni implementation playbook/failure catalog oluşturmak

Aynı konuyu anlatan kısa duplicate Markdown dosyaları ekleme.

9. TEST

- Markdown relative link kontrolü
- JSON/CSV parse kontrolü
- UTF-8 kontrolü
- git diff --check
- secret/local-path scan
- large-file scan
- CPU-only unittest/pytest mevcutsa çalıştır

GPU işi veya model/dataset indirme yok.

10. GIT

Tek commit:
docs: reconcile remaining local Whisper artefacts with canonical archive

Normal push ve origin/main’e PR.
Force push veya unrelated histories yok.

11. FINAL ÇIKTI

RECONCILIATION_STATUS:
NEW_BRANCH:
FINAL_COMMIT:
PR_URL:
FILES_REVIEWED:
FILES_IMPORTED:
FILES_REJECTED:
NEW_AUTHORITATIVE_EVIDENCE:
NEW_DISCREPANCIES:
PRIVACY_SCAN:
TEST_STATUS:
UNRESOLVED_GAPS:
```

Bu promptun amacı bütün yerel klasörü GitHub’a taşımak değil; yalnız kanonik repoda eksik kalan benzersiz, doğrulanabilir ve güvenli parçaları seçmektir.
