---
description: Dokumantasyon olustur - API endpoint listesi, DB sema, changelog, mimari diyagram
argument-hint: Opsiyonel - bos birak = menu, veya direkt (api, db, changelog, mimari, readme, env)
---

# Dokumantasyon

Proje dokumantasyonunu otomatik olustur ve guncelle.

## MENU (arguman yoksa AskUserQuestion ile goster)

```
[1] API Endpoint Liste   Route dosyalarindan endpoint cikar
[2] DB Sema Dokuman      Tablo ve iliskiler dokumante et
[3] Changelog Olustur    Commit'lerden degisiklik notu yaz
[4] Mimari Diyagram      Mermaid ile diyagram guncelle
[5] README Guncelle      Proje README'si
[6] Env Ornegi           .env.example dosyasi guncelle
[0] ← Ana Menu
```

## NASIL CALISIR

### [1] API Endpoint Liste
`apps/api/routes/` dizinindeki dosyalari tara:
- `router.get/post/put/patch/delete` satirlarini bul
- Method, path, auth gereksinimi, aciklama cikar
- Markdown tablo formatinda yaz

### [2] DB Sema Dokuman
```sql
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;
```
Tablo bazinda grupla, iliskileri goster.

### [3] Changelog Olustur
`git log --oneline --since="[tarih]"` ile commit'leri oku.
Kategorize et: feature, fix, improvement, breaking change.
Formatli changelog yaz.

### [4] Mimari Diyagram
Mevcut mimari bilgisini (CLAUDE.md + kod) analiz et.
Mermaid syntax ile diyagram olustur/guncelle.

### [5] README Guncelle
CLAUDE.md + package.json + proje yapisindan README.md olustur.

### [6] Env Ornegi
Mevcut .env dosyasindan key isimlerini cikar.
Degerleri GIZLE, ornek format + aciklama ekle.

## KURALLAR
- .env.example'da gercek degerler ASLA yazilmaz
- Dokumantasyon Turkce yazilir
- Mevcut dosya varsa ustten yaz degil, GUNCELLE
