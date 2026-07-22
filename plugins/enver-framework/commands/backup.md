---
description: Veritabani ve dosya yedekleme - pg_dump, restore, uploads yedek, otomatik yedek
argument-hint: Opsiyonel - bos birak = menu, veya direkt (db-al, db-yukle, dosya, liste)
---

# Backup - Yedekleme

Veritabani ve dosya yedekleme/geri yukleme islemleri.

## MENU (arguman yoksa AskUserQuestion ile goster)

```
[1] DB Yedek Al         pg_dump ile veritabani yedegi
[2] DB Geri Yukle       Yedekten geri yukle
[3] Dosya Yedek Al      uploads/ dizinini yedekle
[4] Yedek Listele       Mevcut yedekleri goster
[5] Otomatik Yedek      Cron job ile zamanli yedek
[0] ← Ana Menu
```

## NASIL CALISIR

SSH ve DB bilgisi vault'tan okunur.

### [1] DB Yedek Al
```bash
ssh [sunucu] "pg_dump -Fc [db_name] > /var/www/vhosts/[domain]/app/backups/db_$(date +%Y%m%d_%H%M).dump && ls -lh /var/www/vhosts/[domain]/app/backups/db_*.dump | tail -1"
```
- Yedek boyutunu goster
- Disk alani kontrolu: `df -h`

### [2] DB Geri Yukle
1. Mevcut yedekleri listele
2. Kullanici yedek secer
3. **UYARI: "Bu islem mevcut veriyi SILER. Emin misin?"** → onay iste
4. `pg_restore -c -d [db_name] [yedek_dosya]`

### [3] Dosya Yedek
```bash
ssh [sunucu] "tar czf /var/www/vhosts/[domain]/app/backups/uploads_$(date +%Y%m%d).tar.gz /var/www/vhosts/[domain]/app/apps/api/uploads/"
```

### [4] Yedek Listele
```bash
ssh [sunucu] "ls -lh /var/www/vhosts/[domain]/app/backups/"
```

### [5] Otomatik Yedek
Cron job olustur: gunluk veya haftalik secim

## KRITIK KURALLAR
- Geri yukleme ONCESINDE mutlaka ONAY iste
- Yedek boyutunu her zaman goster
- Disk alani %90 uzeri ise UYARI ver
- Sunucuda sadece proje dizininde calis
