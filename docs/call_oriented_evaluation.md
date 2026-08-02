# Çağrı ve Telefon Odaklı Değerlendirme

## Temel yaklaşım

Genel Türkçe benchmark başarısı, telefon veya karşılıklı konuşma başarısıyla eşdeğer değildir. Bu çalışma sonuçları iki ayrı panelde değerlendirir.

## Telefon/karşılıklı konuşma paneli

- MediaSpeech Phone
- MediaSpeech G.711
- robustness proxy
- CV Spontaneous
- mevcutsa kısa utterance analizi
- deletion/insertion/substitution dağılımı
- tekrar ve hallucination göstergeleri

## Genel Türkçe izleme paneli

- MediaSpeech Clean
- CV Scripted
- FLEURS
- TSC

Genel-domain regresyonu raporlanır; fakat telefon hedefindeki kazancı otomatik olarak geçersiz kılan bir hard gate değildir.

## Neden normalize WER/CER?

Türkçe ASR’de noktalama, büyük-küçük harf ve yüzey biçimleri ham WER’i önemli ölçüde etkileyebilir. Bu nedenle:

- raw WER,
- normalized WER,
- raw CER,
- normalized CER

birlikte verilmelidir. Ana telefon-domain karşılaştırmalarında normalize WER/CER kullanılır.

## Kritik operasyonel hata sınıfları

Gerçek bir çağrı testinde ayrıca ölçülmesi gerekenler:

- boş çıktı,
- hallucination,
- tekrar döngüsü,
- kısa cevap silinmesi,
- sayı/rakam dizisi hatası,
- para tutarı hatası,
- tarih/saat hatası,
- kişi, kurum ve ürün adı hatası,
- kanal karışması,
- konuşma başı/sonu kaybı,
- crosstalk ve üst üste konuşma.

Bu açık-veri çalışmasında bütün sınıflar için güvenilir annotation bulunmadığından, rapor yalnız mevcut artefaktların desteklediği metrikleri kesin sonuç olarak sunar.

## Nihai telefon sonucu

A7 step-200 controlled Phone normalized WER:

`0.154285`

Karşılaştırma:

| Model | Phone normalized WER |
|---|---:|
| A2 | 0.170825 |
| A4 | 0.158385 |
| A6 | 0.157203 |
| A7 step-200 | **0.154285** |

## Robustness yorumu

A7’nin en iyi robustness sonucu step-150’de `0.147578` oldu. Phone ve robustness için farklı checkpointlerin öne çıkması, model seçiminin tek metrikle yapılmaması gerektiğini gösterir.

## Decode stratejisi

Legacy çalışmada repeat-safe decode, uzun telefon örneğinde tekrar döngüsünü azaltmıştı. Bu sonuç decode stratejisinin ayrı bir deney koşulu olarak tutulması gerektiğini gösterir. Decode iyileştirmesi, model eğitimindeki kaliteyi kanıtlayan bir ikame değildir.

## Sonuç

A7 telefon proxy’sinde en iyi kontrollü sonucu verdi. Bununla birlikte gerçek çağrı merkezi performansı iddiası için insan doğrulanmış, leakage-safe ve temsil edici bir hedef-domain test seti gerekir.
