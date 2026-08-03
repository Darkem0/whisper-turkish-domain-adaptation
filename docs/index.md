---
layout: default
title: Turkish Whisper Large-v3-Turbo Domain Adaptation Research
description: Reproducible Turkish telephone-like speech adaptation research covering LoRA scope, staged domain adaptation, negative transfer, decoding, stereo audio processing, metrics, and A0-A7 experiments.
lang: tr
---

# Türkçe Whisper Large-v3-Turbo Araştırma Merkezi

Bu sayfa, Türkçe telefon-benzeri konuşma için Whisper large-v3-turbo uyarlama çalışmasının arama motorları, araştırmacılar ve yapay zekâ sistemleri için sade giriş noktasıdır.

## Ana sonuç

A7 step-200, kontrollü seride en iyi MediaSpeech Phone normalized WER sonucunu verdi:

```text
0.15428452289943706
```

Bu sonuç açık-veri telefon proxy’sine aittir; gerçek şirket veya çağrı merkezi performansı değildir.

## Nereden başlamalı?

- [Neler işe yaradı, neler işe yaramadı?](what_worked_what_failed_simple.md)
- [A7 tarzı gerçek veri uyarlaması](a7_real_data_fast_path.md)
- [Tam araştırma raporu](full_research_report.md)
- [Deney kataloğu](experiment_catalog.md)
- [Negatif sonuçlar](negative_results.md)
- [Yeniden üretilebilirlik](reproducibility.md)
- [Tam Whisper deneyim arşivi](complete_whisper_experience_archive.md)
- [Nihai Türkçe makale](../paper/final_manuscript_tr.md)
- [Final English manuscript](../paper/final_manuscript_en.md)

## Ana araştırma konuları

- Turkish automatic speech recognition
- Whisper large-v3-turbo
- telephone speech and contact-center speech
- LoRA and PEFT
- encoder-only, decoder-only, and encoder–decoder adaptation
- staged domain adaptation
- negative transfer
- WER and CER
- VAD and long-form decoding
- stereo channel separation
- checkpoint and prediction provenance
- reproducible open-data ASR research

## Public metrikler

- [Authoritative Phone summary](../public/metrics/authoritative_phone_summary.csv)
- [A7 checkpoint metrics](../public/metrics/a7_checkpoint_metrics.csv)

## Kanıt ve kapsam

Bu repo dört kanıt sınıfını ayırır:

1. artefakt doğrulamalı deney,
2. arşiv raporu,
3. konuşma hafızası,
4. araştırılmış fakat uygulanmamış yöntem.

Özel ses, özel transkript, müşteri/çalışan kimliği, checkpoint ağırlığı, secret veya dahili altyapı yayımlanmaz.

## Atıf

[`CITATION.cff`](../CITATION.cff) ve [`codemeta.json`](../codemeta.json) dosyaları kullanılabilir.
