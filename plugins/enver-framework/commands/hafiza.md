---
description: Hafiza - nerede kaldik, karar defteri, hata kutuphanesi, oturum ozetleri ve proje index'leri
---

# Hafıza

Ne yapıldığı, neden yapıldığı ve nerede kalındığı kalıcı olarak burada durur.
Böylece her oturumda baştan anlatmak gerekmez.

## İki ayrı alan

| Alan | Ne | Depoya girer mi |
|------|-----|-----------------|
| `hafiza/` | Özetlenmiş kalıcı bilgi | **Evet** — makineler arasında senkron olur |
| `gunluk/` | Ham oturum kaydı | Hayır — üretildiği makinede kalır |

## Komutlar

```bash
H="${CLAUDE_PLUGIN_ROOT}/scripts/hafiza"

python "$H/oturum.py" brifing                 # nerede kaldık
python "$H/oturum.py" durum                   # son durum kaydı
python "$H/oturum.py" durum --yaz "<metin>"   # duruma not düş
python "$H/oturum.py" bitir --not "<devir notu>" --sirada "<sıradaki iş>"

python "$H/defter.py" karar ekle "<başlık>" "<gerekçe>"
python "$H/defter.py" karar liste

python "$H/defter.py" hata ekle "<belirti>" "<çözüm>" --nerede "<bağlam>"
python "$H/defter.py" hata ara "<sorgu>"
python "$H/defter.py" hata liste
```

## Ne zaman ne yapılır

**Oturum başında** — açılış kancası brifingi zaten getirir. Getirmemişse
`brifing` çalıştır ve kullanıcıya özetle.

**Bir karar verildiğinde** — kullanıcı "şunu kullanmayalım", "böyle olsun",
"müşteri bunu istemedi" derse **hemen** `karar ekle` çalıştır. Sonraki
oturumda bu karar tekrar tartışılmasın.

**Bir hata çözüldüğünde** — belirtiyi ve çözümü `hata ekle` ile kaydet.
Aynı hata tekrar çıkarsa çözüm hazır gelir.

**Bir hatayla karşılaşıldığında** — çözmeye başlamadan **önce** `hata ara`
çalıştır. Daha önce çözülmüş olabilir.

**Oturum biterken** — `bitir` çalıştır. Devir notunu ve sıradaki işi yaz.

## Kurallar

- Parolalar kayda geçmeden önce gizlenir; yine de kasa içeriğini hafızaya yazma.
- Karar ve hata kayıtları **kısa ve aranabilir** olsun; uzun anlatım değil,
  belirti ve çözüm yaz.
- `hafiza/` depoya girer — müşteriye özel hassas bilgi buraya yazılmaz,
  o bilgiler kasada durur.

## İlgili

- `/senkron` — başka bilgisayarla eşitleme
- `/kasa` — şifreler ve anahtarlar
- `/index` — bütün komutlar
