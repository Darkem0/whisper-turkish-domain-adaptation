# Whisper Turkish Domain Adaptation

A clean-room research scaffold for reproducible Turkish ASR adaptation experiments. It uses small synthetic fixtures by default and documents how to add public, licensed datasets without publishing private audio, checkpoints, call-derived metrics, or proprietary experiment logs.

The repository deliberately retains a synthetic negative-result example: fine-tuning can improve one split while degrading another. It treats raw and normalized WER/CER, domain boundaries, VAD/segmentation, repeat-safe decoding, and adapter routing as separate questions.

## Quick start

~~~bash
python -m whisper_adaptation demo
python -m whisper_adaptation evaluate --manifest experiments/adapter-routing.json
python -m whisper_adaptation repeat-safe --text "teşekkür ederim teşekkür ederim bilgi"
python -m unittest discover -s tests -v
~~~

The outputs are deterministic synthetic research demonstrations, not historical measurements or model-quality claims.

## What is included

- Versioned JSON experiment manifests with public-data placeholders.
- Raw and normalized WER/CER implementation.
- Domain-split analysis and synthetic negative-result preservation.
- VAD/segmentation evaluation hooks.
- Repeat-safe decoding utility.
- Adapter-routing rule prototype.
- No model download, training job, private checkpoint, or private audio requirement.

## Documentation

- [Methodology](docs/METHODOLOGY.md)
- [Public-data and fixture provenance](docs/PROVENANCE.md)
- [Negative results](docs/NEGATIVE_RESULTS.md)
- [Limitations](docs/LIMITATIONS.md)

## License

MIT. See [LICENSE](LICENSE).
