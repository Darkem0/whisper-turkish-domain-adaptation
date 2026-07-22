# Whisper Türkçe Alan Uyarlama

Tekrarlanabilir Türkçe ASR uyarlama deneyleri için temiz-oda araştırma iskeletidir. Varsayılan olarak küçük sentetik örnekler kullanır; özel ses, kontrol noktası, çağrıdan türetilmiş metrik veya şirket içi deney günlüğü yayınlamadan herkese açık ve lisanslı veri ekleme yöntemini açıklar.

Depo, sentetik bir negatif sonuç örneğini korur: ince ayar bir veri bölümünde iyileştirirken başka bir bölümde kötüleşebilir. Ham ve normalize WER/CER, alan sınırları, VAD/parçalama, tekrar-güvenli çözme ve adaptör yönlendirmeyi ayrı sorular olarak ele alır.

## Hızlı başlangıç

~~~bash
python -m whisper_adaptation demo
python -m whisper_adaptation evaluate --manifest experiments/adapter-routing.json
python -m unittest discover -s tests -v
~~~

Çıktılar deterministik sentetik araştırma gösterimleridir; tarihsel ölçüm veya model kalite iddiası değildir.
