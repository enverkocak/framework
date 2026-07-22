---
description: Coklu bilgisayar senkronu - makine tanitma, hafizayi cekme ve gonderme, cakisma kontrolu
---

# Senkron

Enver birden çok bilgisayarda çalışıyor. Bir makinede yarım bırakılan iş,
diğerinde kaldığı yerden devam edebilmeli.

## Komutlar

```bash
S="${CLAUDE_PLUGIN_ROOT}/scripts/senkron"

python "$S/makine.py" durum                    # bu makine tanınıyor mu
python "$S/makine.py" tanit --ad "<ad>"        # bu bilgisayarı kaydet
python "$S/makine.py" liste                    # bütün makineler

python "$S/senkron.py" durum                   # yerel ile depo arasında fark
python "$S/senkron.py" cek                     # depodan güncel hali al
python "$S/senkron.py" gonder                  # yerel hafızayı depoya işle
```

## Yeni bilgisayara geçildiğinde

1. `makine.py durum` çalıştır.
2. Makine tanınmıyorsa kullanıcıya sor: **"Bu bilgisayara ne ad verelim?"**
   Cevabı al, `makine.py tanit --ad "<ad>"` çalıştır.
3. `senkron.py cek` ile güncel hafızayı al.
4. Gelen brifingi kullanıcıya özetle: nerede kalmıştık, sırada ne var.

## İş bitiminde

1. `oturum.py bitir` ile özeti yaz.
2. `senkron.py gonder` ile depoya işle.

Böylece diğer bilgisayarda açıldığında bilgi hazır olur.

## Çakışma

`gonder`, depoda bizde olmayan kayıt varsa **durur ve üzerine yazmaz**.
Bu durumda önce `cek` çalıştırılır.

`cek` ise yerelde işlenmemiş değişiklik varsa durur. Önce `gonder` gerekir.

Bu iki kural birlikte, iki makinede yapılan işin birbirini silmesini engeller.

## Kapsam

Senkrona **yalnız `hafiza/` klasörü** girer.

| Girer | Girmez |
|-------|--------|
| Durum, kararlar, hatalar, oturum özetleri, makine kayıtları | Kasa (şifreli, ayrı taşınır) |
| | Ham günlük (makineye özel) |
| | Çalışma ve arşiv klasörleri |

## İlgili

- `/hafiza` — kayıtların kendisi
- `/kasa` — şifreler (senkrona dahil değil)
