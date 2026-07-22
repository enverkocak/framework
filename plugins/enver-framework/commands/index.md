---
description: Komut rehberi - butun komutlar, beceriler, ajanlar ve korumalar tek listede, detayli kullanimla
---

# Komut Rehberi

Framework'te ne varsa burada. Elle liste tutulmaz; rehber dosyalardan otomatik üretilir.

## Nasıl çalışır

Rehberi üret ve göster:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/index-uret.py"
```

Ham veri (başka bir işte kullanmak için):

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/index-uret.py" --json
```

## Kullanıcıya sunum

1. Yukarıdaki üreteci çalıştır.
2. Çıktıyı olduğu gibi göster — kategorilere ayrılmış tablolar hâlinde gelir.
3. Çıktının altına şu kısa yardımı ekle:

```
Bir komutu detaylı öğrenmek için:  /index <komut-adi>
Örnek:                             /index panel
```

## Tek komut sorulduysa

Kullanıcı `/index panel` gibi bir argüman verdiyse:

1. `commands/<ad>.md` dosyasını oku.
2. Şu başlıklarla özetle:
   - **Ne yapar** — bir cümle
   - **Ne zaman kullanılır** — hangi durumda işe yarar
   - **Kullanım** — çağırma biçimi ve varsa argümanlar
   - **Örnek** — gerçek bir kullanım örneği
   - **İlgili komutlar** — birlikte kullanılanlar
3. Dosya yoksa, en yakın komut adlarını öner.

## Kurallar

- Rehberdeki bütün metinler `diller/` altındaki dil dosyasından gelir. Kod içine metin gömülmez.
- Yeni komut eklendiğinde rehber kendiliğinden güncellenir; buraya elle satır eklenmez.
- Çıktı Türkçe karakterlerle gösterilir (ö, ç, ü, ğ, ı, ş, İ).
