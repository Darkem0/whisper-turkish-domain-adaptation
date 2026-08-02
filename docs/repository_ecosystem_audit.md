# GitHub Depo Ekosistemi Denetimi ve Birleştirme Kararı

Bu belge, Emre Aslan’ın GitHub hesabındaki Whisper, Türkçe konuşma işleme ve çağrı değerlendirmesiyle ilişkili public depoları denetler. Amaç geçmişi silmeden, tek bir **kanonik araştırma ve makale merkezi** belirlemek; çalışır bileşenleri de sabit commitlerle aynı çalışma alanında kullanılabilir hâle getirmektir.

## 1. Denetim sonucu

Kanonik depo:

- **`Darkem0/whisper-turkish-domain-adaptation`**

Bu depo artık şu rollerin tek merkezidir:

- A0–A7 kontrollü araştırma sonuçları,
- Legacy deney geçmişi,
- neyin işe yaradığı / yaramadığı rehberi,
- ChatGPT ve yerel proje arşivi,
- nihai makale,
- authoritative public metric tabloları,
- diğer public bileşenlerin commit-kilitli kayıtları,
- yeniden üretim ve gizlilik sınırları.

Diğer depolar silinmez veya zorla birleştirilmez. Kendi Git geçmişleri ve bağımsız çalıştırılabilir demoları korunur.

## 2. Denetlenen public depolar

| Depo | Denetlenen commit | Rol | Karar |
|---|---|---|---|
| `whisper-turkish-domain-adaptation` | `06a2ca672dcda383a1a5f89a6f733b6c51bbd7ff` ve sonrası | Araştırma, metrik, makale ve kanonik bilgi merkezi | **CANONICAL_HUB** |
| `turkish-speech-processing-platform` | `6d7d63faba3d20fe3f2556b9348848831a8ad67b` | Stereo WAV inceleme, kanal split, rol eşleme, timestamp merge, duplicate suppression, fixture WER/CER ve API | **PINNED_RUNNABLE_COMPONENT** |
| `contact-center-ai-evaluation-suite` | `2ae18e10eb065579071ef08543bf659a6bf383cd` | Sentetik diyalog üzerinde evidence-linked, typed downstream değerlendirme | **PINNED_RUNNABLE_COMPONENT** |
| `research-publications` | `1c283d97389ea88d9b61c3ff06af5d6da499ce36` | Kaynak-doğrulamalı yayın metadata kaydı | **PINNED_PUBLICATION_RECORD** |
| `applied-ai-engineering-portfolio` | `62385c612a9f13e1a984741e1491afd7666da78a` | Proje ve kanıt seviyesi dizini | **DISCOVERY_INDEX** |
| `Darkem0` profil deposu | `ec3e38eda02d1fd57f5dfd608376a60d813d5494` | GitHub profil ve proje yönlendirmesi | **DISCOVERY_INDEX** |

## 3. Neden kodları tek Git geçmişinde kopyalamıyoruz?

`turkish-speech-processing-platform` ve `contact-center-ai-evaluation-suite` küçük ve çalışır public referanslardır; ancak farklı ürün yüzeyleri, bağımlılıklar ve test sözleşmeleri vardır. Kodların tamamını araştırma deposuna kopyalamak şu sorunları doğurur:

- bağımsız Git geçmişi kaybolur,
- aynı hata iki yerde düzeltilmek zorunda kalır,
- test ve dependency yüzeyleri karışır,
- araştırma iddiası ile ürün demo iddiası birbirine karışır,
- public-safe sentetik demo sınırları belirsizleşir.

Bunun yerine bu depo bir **pinned workspace hub** olur. `ecosystem/components.lock.json` kaynak URL ve commitleri sabitler; `scripts/bootstrap_public_ecosystem.py` bileşenleri aynı yerel çalışma alanına klonlar.

Bu yapı kullanıcı açısından tek giriş noktası sağlarken diğer depoların tarihini korur.

## 4. Bileşenlerden alınan anlamlı parçalar

### 4.1. Türkçe konuşma işleme bileşeni

`turkish-speech-processing-platform` şu parçaları gerçek ve çalışır biçimde sunar:

- oluşturulmuş WAV üzerinde container/kanal/süre inceleme,
- stereo kanalları gerçek mono WAV dosyalarına ayırma,
- konuşmacı rolü eşleme,
- timestamp sıralama ve merge,
- duplicate suppression,
- JSON, text ve SRT render,
- WER/CER fixture hesabı,
- CLI ve FastAPI,
- sentetik fixture testleri.

ASR metni public varsayılanda mock’tur. Bu sınır korunur; repo gerçek model kalitesi iddiası olarak sunulmaz.

### 4.2. Çağrı değerlendirme bileşeni

`contact-center-ai-evaluation-suite` şu parçaları sağlar:

- typed Pydantic output sözleşmesi,
- evidence excerpt taşıyan sonuçlar,
- `insufficient_evidence` davranışı,
- sekiz sentetik görev paketi,
- CLI ve local FastAPI,
- schema ve API testleri.

Bu bileşen ASR model ölçümü değildir. Transcript sonrası yapılandırılmış downstream değerlendirme örneğidir.

### 4.3. Yayın ve portföy kayıtları

`research-publications`, `applied-ai-engineering-portfolio` ve profil deposu:

- yayın kaynağı ve DOI/authoritative link kaydı,
- proje kanıt seviyesi,
- ilgili depolara yönlendirme

sağlar. Bunlar araştırma koduna kopyalanmaz; kanonik repodan linklenir.

## 5. Codex branch denetimi

İncelenen uzak branch:

- `codex/publish-whisper-research-docs`
- kaynak commit: `793c730801a91cb6f4212c23326197a077cf7e5d`

Bu branch ile `main` arasında ortak Git ancestor yoktur. Bu nedenle:

- `--allow-unrelated-histories` kullanılmadı,
- force push yapılmadı,
- main resetlenmedi,
- branch doğrudan merge edilmedi.

### 5.1. İçeriği alınan parçalar

- daha sıkı private-artifact ignore ilkeleri,
- authoritative A7 checkpoint/dataset metric tablosu,
- concise Phone karşılaştırma tablosu,
- A7 checkpoint trajectory,
- A5–A6 self-comparison bug kaydı,
- P7/MEM2 discrepancy notu,
- project archaeology envanter fikri.

Bu parçalar mevcut daha kapsamlı belgeleri ezmeden `public/` ve `docs/` altında yeniden düzenlenir.

### 5.2. Alınmayan veya doğrudan kullanılmayan parçalar

- mevcut ana README’den daha kısa README sürümü,
- aynı bilgiyi tekrar eden üç–on satırlık çok sayıda Markdown dosyası,
- yerel cache ve mutlak path içeren scriptler,
- public repoda çalışmayan `whisper_arge` CLI komutları,
- “şirket yetkilendirmesi tek sonraki adımdır” şeklindeki kişisel proje bağlamıyla uyumsuz ifade,
- tamamı private/generated `reports/` klasörünü public hâle getirecek geniş ignore değişikliği.

## 6. Bilimsel otorite sırası

Çelişki olduğunda sıralama:

1. prediction JSONL ve SHA-256,
2. checkpoint/model SHA ve lock,
3. prediction’dan yeniden hesaplanan metric,
4. training/evaluation progress,
5. final integrity raporu,
6. düzeltilmiş final rapor,
7. arşiv raporu,
8. ChatGPT konuşma hafızası,
9. araştırma planı.

Bu sıra A5–A6 self-comparison hatasının düzeltilmesinde ve A7 step-200 provenance kararında kullanılmıştır.

## 7. Nihai kanonik iddialar

Public ana sonuçlar:

- A7 step-200 Phone normalized WER: `0.15428452289943706`
- A7 step-150 robustness proxy normalized WER: `0.14757801098061019`
- A2 Phone: `0.170825`
- A4 Phone: `0.158385`
- A6 Phone: `0.157203`
- A7 frozen evaluation: 28/28 target
- A7 step-200: `ADAPTER_CONTINUATION_WITH_OPTIMIZER_RESET`
- A5–A6 eski zero-delta sonucu: `SUPERSEDED_DUE_TO_REFERENCE_PATH_BUG`
- Açık veri terminal kararı: `OPEN_DATA_EXPERIMENT_LINE_COMPLETED`

Bu sonuçlar gerçek şirket çağrısı performansı değildir; açık veri telefon proxy sonuçlarıdır.

## 8. Muhafaza politikası

Aşağıdaki kayıtlar korunur:

- diğer public depolar ve Git geçmişleri,
- Codex’in unrelated-history branch’i,
- PR ve commit geçmişi,
- başarısız/negatif deneyler,
- superseded analiz kayıtları,
- resume ve checkpoint hata dersleri.

Hiçbiri silinerek “temiz” bir başarı hikâyesi üretilmez.

## 9. Birleştirilmiş çalışma alanı

Kullanıcı tek klasörde çalışmak isterse:

```bash
python scripts/bootstrap_public_ecosystem.py --destination components
```

Script commit-kilitli public bileşenleri klonlar. Araştırma deposu ana çalışma dizini olarak kalır; companion repos `components/` altında yer alır ve Git tarafından takip edilmez.

## 10. Denetçi kararı

- Tek kanonik repo oluşturuldu: mevcut `whisper-turkish-domain-adaptation` genişletildi.
- Diğer repolar arşivlenmedi veya silinmedi; bağımsız çalışır kayıt olarak kaldı.
- Unrelated Codex branch zorla merge edilmedi; benzersiz ve doğrulanabilir içerikler seçici olarak taşındı.
- Final makale, metrik tabloları, runnable component registry ve citation metadata aynı kanonik repoda toplandı.
