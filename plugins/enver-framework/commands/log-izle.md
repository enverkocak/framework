---
description: PM2, Nginx loglarini izle - hata filtrele, arama yap, canli izle
argument-hint: Opsiyonel - bos birak = menu, veya direkt (api, web, error, nginx, ara)
---

# Log Izle - Uygulama Loglari

Sunucudaki uygulama ve web sunucu loglarini goruntule ve filtrele.

## MENU (arguman yoksa AskUserQuestion ile goster)

```
[1] API Loglari        PM2 API son loglar
[2] Web Loglari        PM2 Web son loglar
[3] Hata Loglari       Sadece error (tum uygulamalar)
[4] Nginx Access       Son erisim loglari
[5] Nginx Error        Nginx hata loglari
[6] Canli Izle         Son X dakikanin loglari
[7] Log Ara            Belirli kelimeyi loglarda ara
[0] ← Ana Menu
```

## NASIL CALISIR

SSH bilgisi vault'tan okunur. PM2 process isimleri `pm2 list` ile tespit edilir.

### [1-2] PM2 Loglari
```bash
ssh [sunucu] "pm2 logs [process] --lines 50 --nostream"
```

### [3] Hata Loglari
```bash
ssh [sunucu] "pm2 logs --err --lines 30 --nostream"
```

### [4-5] Nginx Loglari
```bash
ssh [sunucu] "tail -50 /var/www/vhosts/system/[domain]/logs/proxy_access_ssl_log"
ssh [sunucu] "tail -50 /var/www/vhosts/system/[domain]/logs/proxy_error_log"
```

### [6] Canli Izle
Kullaniciya "Kac dakika?" sor → `pm2 logs --since "X minutes ago" --nostream`

### [7] Log Ara
Kullaniciya "Ne arayalim?" sor → `pm2 logs --lines 500 --nostream | grep "arama"`

## KURALLAR
- SSH bilgisi vault'tan okunur
- Log ciktisinda hassas veri (token, sifre) varsa MASKELE
- Cok uzun ciktilari ozet goster, detay icin "devami?" sor
