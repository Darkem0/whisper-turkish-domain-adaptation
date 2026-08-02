# Public Whisper Ecosystem Workspace

Bu klasör, araştırma sonuçlarını tek bir kanonik depoda tutarken bağımsız çalışır public bileşenleri commit-kilitli biçimde aynı yerel çalışma alanına getirmek için kullanılır.

## Neden submodule veya kod kopyası değil?

Bileşenler farklı amaçlara sahiptir:

- `whisper-turkish-domain-adaptation`: araştırma, metrik, deney geçmişi ve makale.
- `turkish-speech-processing-platform`: gerçek oluşturulmuş stereo WAV üzerinde kanal/timestamp/dedup işleme; ASR varsayılanı sentetik mock.
- `contact-center-ai-evaluation-suite`: sentetik diyalog üzerinde typed downstream değerlendirme.
- `research-publications`: kaynak-doğrulamalı yayın metadata kaydı.
- `applied-ai-engineering-portfolio`: proje ve kanıt seviyesi dizini.

Kodların tamamını buraya kopyalamak geçmişi ve bakım sınırlarını bozar. `components.lock.json` her depoyu sabit commit ile tanımlar. Bootstrap scripti bu commitleri `components/` altında detached HEAD olarak hazırlar.

## Kurulum

```bash
git clone https://github.com/Darkem0/whisper-turkish-domain-adaptation.git
cd whisper-turkish-domain-adaptation
python scripts/bootstrap_public_ecosystem.py --destination components
```

Sadece çalışır bileşenleri getirmek için:

```bash
python scripts/bootstrap_public_ecosystem.py \
  --destination components \
  --include speech_processing contact_center_evaluation
```

Kontrol modu:

```bash
python scripts/bootstrap_public_ecosystem.py --destination components --verify-only
```

## Beklenen klasör yapısı

```text
whisper-turkish-domain-adaptation/
├── docs/
├── paper/
├── public/
├── ecosystem/
├── whisper_adaptation/
└── components/
    ├── speech_processing/
    ├── contact_center_evaluation/
    ├── publication_records/
    └── portfolio_index/
```

`components/` Git tarafından takip edilmez. Her bileşen kendi lisansı ve Git geçmişiyle ayrı repo olarak kalır.

## Çalıştırma örnekleri

### Araştırma deposu

```bash
python -m unittest discover -s tests -v
python -m whisper_adaptation demo
```

### Stereo konuşma işleme demosu

```bash
cd components/speech_processing
python -m pip install -e ".[dev]"
python fixtures/generate_demo_audio.py
python -m turkish_speech demo --output examples/demo-output.json
python -m unittest discover -s tests -v
```

### Downstream çağrı değerlendirme demosu

```bash
cd components/contact_center_evaluation
python -m pip install -e ".[dev]"
python -m contact_center_eval.cli demo --output examples/demo-report.json
pytest -q
```

## Sınırlar

- Script yalnız public GitHub depolarını klonlar.
- Ham çağrı sesi veya transkript indirmez.
- Model indirmez.
- GPU işi başlatmaz.
- Private branch veya secret kullanmaz.
- Lock dosyasındaki commit bulunamazsa hata verir; sessizce branch head kullanmaz.

## Güncelleme

Bir companion repo güncellendiğinde:

1. yeni commit bağımsız depoda test edilir,
2. bu depoda `components.lock.json` güncellenir,
3. değişiklik gerekçesi `docs/repository_ecosystem_audit.md` içinde kaydedilir,
4. bootstrap `--verify-only` ile kontrol edilir.
