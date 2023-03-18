# Belge Biçimlendirme Yardımcısı

Görme engelli kullanıcılar için belge biçimlendirme bilgisini ve yönetimini kolaylaştıran bir eklenti.

* Yazar: Alberto Buffolino;
* [Geliştirme sürümünü indirin;][dev]
* NVDA uyumluluğu: muhtemelen 2021.1 ve sonrası.


## Zaten var olan

NVDA+shift+ctrl+o ile erişilecek, bazı bölümlere (yani yaygın olmayan) özgü biçimlendirmenin kontrol edilebilir bir listesini ve belge içeriği üzerinde yenilenebilir, filtrelenmiş bir görünümü ortaya çıkaran bir biçimlendirme görüntüleyici önceki listede seçilen biçimlendirme.  

Kontrol edilebilir liste, kullanıcının kontrol edebileceği öznitelikleri (stilleri, yazı tiplerini, renkleri...) ve parantezler arasında, belirli öznitelikle bulunan ardışık olmayan blokların sayısını sunar.  

Varsayılan erişim kısayolu Girdi hareketleri iletişim kutusunda özelleştirilebilir.  

Filtrelenmiş görünümde bir kelimeye enter basmak, odağı tekrar belgeye taşır ve bu kelimenin üzerine gelir (bu arada belgeyi değiştirmediyseniz).  

İlgili kısayol tuşlarına ilk basıldığında, belge büyüklüğüne göre değişen ve biraz zaman alabilen bir analiz gerçekleştirilir.  
Aynı tuşlara tekrar basıldığında işlem iptal edilir.  
İşlem arkaplanda çalışıyorsa, sadece bir bip sesi ile sürecin devam ettiği bilgisi kullanıcıya bildirilmiş olur.  
Eğer ilgili pencere aktif ise, bir bip sesi ve yüzdelik ilerlemesi ile aşama gösterilir.  

Ne yazık ki, şu anda biçimlendirme görüntüleyiciyi her açtığımızda (veya güncellenmiş bir görünüm istediğimizde) analiz yapılmak zorundadır.  

Ayrıca UIA desteklenmiyor (Şu an için).  

## Gelecekte olabilecekler (umuyoruz).

Genel yapılacaklar ve tüm senaryolarda yardımcı olabilecek özelliklerin listesi (ayrıca bkz. [NVDA sorunu 9527][ilgili sorun]).

* İlgili tüm teknolojileri (IAccessible, VBA, UIA...) hızlandırmak ve desteklemek için daha iyi bir kod organizasyonu.
* biçimlendirilmiş öğeler arasında hızlı gezinme (kalın, italik, renkli/aynı renkle...);
* bir "git" özelliği (analiz olmadan);
* "benzerine git" özelliği (yalnızca şapka işaretinin altındaki kelime analiz edilir);
* bir "hedef" özelliği ("git" gibi, ancak tam belge analizi ile);
* "göz alıcı uyarı" özelliği (yazı tipi boyutu, metin veya arka plan rengi için bir şeyin farklılık gösterip göstermediğinin duyurulması... gören kişiler için çok belirgin olacak şekilde).


[dev]: https://github.com/ABuffEr/documentFormattingHelper/releases/download/20230208-dev/documentFormattingHelper-20230208-dev.nvda-addon
[related-issue]: https://github.com/nvaccess/nvda/issues/9527
