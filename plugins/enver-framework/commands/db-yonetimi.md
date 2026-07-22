---
description: Veritabani yonetimi - migration, seed, tablo incele, sorgu calistir
argument-hint: Opsiyonel - bos birak = menu, veya direkt (tablo, migration, seed, sorgu)
---

# DB Yonetimi - Veritabani Islemleri

PostgreSQL veritabani yonetim islemleri.

## MENU (arguman yoksa AskUserQuestion ile goster)

```
[1] Tablo Listele       Tum tablolar ve satir sayilari
[2] Tablo Incele        Belirli tablonun kolonlari
[3] Migration Olustur   Yeni SQL migration yaz
[4] Migration Calistir  Bekleyen migration'lari calistir
[5] Migration Geri Al   Son migration'i geri al
[6] Seed Yukle          Test verisi yukle
[7] Sorgu Calistir      Ozel SQL sorgusu (SADECE SELECT)
[8] Yavas Sorgular      En yavas sorgulari listele
[0] ← Ana Menu
```

## NASIL CALISIR

DB bilgisi sunucudaki .env dosyasindan okunur.
SSH bilgisi vault'tan okunur.

### [1] Tablo Listele
```sql
SELECT schemaname, tablename, n_live_tup as satir_sayisi
FROM pg_stat_user_tables ORDER BY n_live_tup DESC;
```

### [2] Tablo Incele
Kullaniciya tablo sor →
```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns WHERE table_name = '[tablo]' ORDER BY ordinal_position;
```

### [3] Migration Olustur
`apps/api/migrations/` dizinine yeni dosya:
- Dosya adi: `[timestamp]_[aciklama].sql`
- UP ve DOWN bloklari icersin
- Kullaniciya migration icerigini sor

### [7] Sorgu Calistir
- SADECE SELECT sorgularina izin ver
- INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER → ENGELLE
- Kullaniciya uyari: "Sadece SELECT sorgusu calistirabilirsiniz"

### [8] Yavas Sorgular
```sql
SELECT query, calls, mean_exec_time, total_exec_time
FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;
```

## GUVENLIK KURALLARI
- [7] SADECE SELECT izin ver, digerleri ENGELLE
- DROP, DELETE, TRUNCATE ASLA calistirilmaz
- DB credentials ekrana YAZILMAZ
