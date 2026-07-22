---
description: Toplu islemler - ESLint auto-fix, import temizle, TODO listele, paket guncelle, dead code bul
argument-hint: Opsiyonel - bos birak = menu, veya direkt (fix, todo, paket, istatistik, dead)
---

# Toplu Islemler

Proje genelinde toplu kod kalitesi ve temizlik islemleri.

## MENU (arguman yoksa AskUserQuestion ile goster)

```
[1] ESLint Auto-Fix     Tum projede eslint --fix
[2] Import Temizle      Kullanilmayan import'lari kaldir
[3] TODO Listele        Tum TODO/FIXME/HACK yorumlari
[4] Paket Guncelle      Outdated paketleri guncelle
[5] Kod Istatistik      Satir/dosya sayisi, dil dagilimi
[6] Dead Code Bul       Kullanilmayan fonksiyon/degisken
[0] ← Ana Menu
```

## NASIL CALISIR

### [1] ESLint Auto-Fix
```bash
# Onceki hata sayisi
npx eslint . --ext .js,.jsx,.ts,.tsx 2>&1 | tail -1
# Fix
npx eslint . --ext .js,.jsx,.ts,.tsx --fix 2>&1
# Sonraki hata sayisi - karsilastir
```
Oncesi/sonrasi hata sayisi raporu goster.

### [2] Import Temizle
Kullanilmayan import'lari bul ve temizle:
```bash
npx eslint . --rule '{"no-unused-vars": "warn", "@typescript-eslint/no-unused-vars": "warn"}' --fix
```

### [3] TODO Listele
```bash
grep -rn "TODO\|FIXME\|HACK\|XXX\|WORKAROUND" --include="*.ts" --include="*.tsx" --include="*.js" apps/
```
Sonucu tablo formatinda goster: dosya, satir, icerik

### [4] Paket Guncelle
```bash
npm outdated
```
Kullaniciya hangilerini guncellemek istedigini sor, secilenleri guncelle.

### [5] Kod Istatistik
Dosya sayisi, satir sayisi, dil dagilimi, en buyuk dosyalar.

### [6] Dead Code Bul
Export edilip hicbir yerde import edilmeyen fonksiyonlari bul.

## KURALLAR
- Auto-fix oncesinde git status kontrol et (uncommitted changes varsa uyar)
- Her islem sonucunda oncesi/sonrasi karsilastirma goster
- Tehlikeli islem yok, ama yine de buyuk degisikliklerde bilgilendir
