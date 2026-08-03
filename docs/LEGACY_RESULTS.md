# Legacy sonuçların statüsü

Kaynaklar:

- `docs/danisman_whisper_turkce_genisletilmis_rapor.md`
- `docs/LEGACY_PROJECT_HANDOFF.md`

Bu belgelerdeki A0–A5 sonuçları `ledger/experiments.jsonl` içine işlendi.
Orijinal manifest, prediction, environment snapshot ve LoRA checkpointleri
bulunmadığı için:

- sonuçlar tarihsel kanıttır,
- yeniden üretilebilir koşu değildir,
- sayılar yeni eval suite ile doğrudan birleştirilemez,
- eksik artifactler sonradan “tahmini hash” ile doldurulamaz,
- aynı tarifleri tekrar etmek yeni araştırma önceliği değildir.

Özellikle MediaSpeech-only 1 epoch, eski CV+MediaSpeech karışımı, eski
balanced-phone tarifi, VAD'siz uzun ses ve repeat-safe ayarsız decode denylist'e
alınmıştır.

