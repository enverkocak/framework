# plugins/enver-framework/references - içindekiler

> Bu belge otomatik üretilir. Elle satır eklenmez;
> açıklamalar dosyaların kendisinden okunur.

## Dosyalar

| Dosya | Ne işe yarar |
|-------|--------------|
| `dizin-duzeni.json` | Ana dizinde ne bulunabilecegini tanimlar. Kapi testleri bu dosyayi okur. Yeni bir ust duzey klasor eklendiginde SADECE burasi guncellenir; testlerin i |
| `kurallar.md` | Geliştirici bilgisi her zaman aynıdır ve tek yerden gelir: |
| `sunucu-haritasi.json` | Sunucu ve proje haritasi. Hangi sitenin hangi dizinde, hangi veritabaniyla calistigi burada durur. Sunucu korumasi bu dosyayi okur. BU DOSYAYA PAROLA, |
| `sunucu-haritasi.ornek.json` | ORNEK DOSYA. Kendi sunucularini tanimlayip sunucu-haritasi.json olarak kaydet. Sunucu ve proje haritasi. Hangi sitenin hangi dizinde, hangi veritabani |
| `yazi-tipi-eslesmeleri.json` | Yazi tipi eslesmeleri katalogu. Her eslesme bir KARAKTER tasir; amac ayni tipografiyi her projede tekrarlamamak. Kaynak: Google Fonts. Yuklemek icin a |

---

Açıklaması eksik olan bir dosya varsa iki yol var:
dosyanın başına açıklama yaz, ya da bu klasöre `aciklamalar.json` koy.
