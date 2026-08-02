# Sınırlamalar ve Gelecek Çalışma

## Sınırlamalar

### Gerçek çağrı merkezi verisi yok

Bu çalışma açık Türkçe veri setleri ve telefon-benzeri proxy koşulları kullanır. Sonuçlar gerçek banka veya çağrı merkezi performansı olarak yorumlanmamalıdır.

### A7 çoklu müdahale deneyi

A7 aynı anda parent continuation, source rebalancing ve birden fazla augmentasyonu birleştirir. Bu nedenle staged adaptation desteklenirken, augmentasyonların bağımsız nedensel katkısı kesin olarak ayrıştırılamaz.

### Genel-domain maliyet

A7 Phone performansını geliştirirken CV Scripted tarafında maliyet oluşturur. Tek bir adapterın bütün konuşma türlerinde en iyi olduğu iddia edilemez.

### Resume tam değildir

A7 step-200, optimizer state olmadan step-150 adapterından continuation ile tamamlanmıştır. Schedule ve global step korunmuş olsa da exact bit-for-bit resume değildir.

### Kritik entity ölçütleri sınırlı

Sayı, tarih, tutar, IBAN, kişi adı ve kurum adı gibi hata sınıfları için kapsamlı, insan doğrulanmış annotation bulunmamaktadır.

### Tek seed

Ana kontrollü deneyler tek seed üzerinden yürütülmüştür. Confidence interval hesapları evaluation sample belirsizliğini ölçer; training seed belirsizliğini ölçmez.

## Gelecek çalışma

### İnsan doğrulanmış hedef-domain test seti

En yüksek bilgi değerine sahip sonraki adım, gerçek kullanım koşuluna benzeyen ve insan tarafından doğrulanmış bir test setidir. Bu set eğitim veya model seçimi için kullanılmamalıdır.

### Domain-aware adapter seçimi

A0/A4/A7 gibi Pareto adayları arasında basit bir domain router veya güvenli fallback yaklaşımı incelenebilir. Router hataları ayrıca ölçülmelidir.

### Kritik içerik metrikleri

- sayı doğruluğu,
- para/tutar doğruluğu,
- tarih/saat doğruluğu,
- rakam dizisi doğruluğu,
- özel isim doğruluğu,
- bankacılık terminolojisi doğruluğu

için insan annotation protokolü hazırlanmalıdır.

### Çoklu seed doğrulaması

A7 ve A4 gibi güçlü adaylar en az üç seed ile tekrar edilerek training varyansı ölçülebilir.

### Kontrollü augmentasyon ablationı

A7 entegrasyon deneyinden sonra bilimsel olarak ayrıştırılmak istenirse aşağıdaki tek-fark koşulları kurulabilir:

- staged continuation, augmentasyon yok,
- yalnız phone-band,
- yalnız speed perturbation,
- yalnız noise/gain,
- birleşik augmentasyon.

Bu çalışma hattı tamamlandığı için bunlar zorunlu yeni deneyler değil, gelecek araştırma önerileridir.

## Terminal karar

`OPEN_DATA_EXPERIMENT_LINE_COMPLETED`

Mevcut açık-veri sonuçları yeni bir kör ablation zinciri başlatmak için değil, hedef-domain doğrulamasına geçmek için yeterlidir.
