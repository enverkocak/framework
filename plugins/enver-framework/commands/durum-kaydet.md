---
description: Conversation handoff - nerede kaldigini kaydeder, sonraki konusmaya hazirlar
argument-hint: Opsiyonel - ozel not eklemek icin
---

# Durum Kaydet - Conversation Handoff

Mevcut calisma durumunu kaydet ki sonraki konusmada kaldigi yerden devam edilebilsin.

## 1. Bilgi Topla

Asagidaki kaynaklardan bilgi topla:

- **Git durumu:** `git status` ve `git log --oneline -10`
- **Faz plani:** `.claude/faz-plani.md` (varsa)
- **Memory:** Proje memory dosyalari
- **Konusma ozeti:** Bu konusmada ne yapildi

## 2. Durum Dosyasini Guncelle

`.claude/durum.md` dosyasini su formatla olustur/guncelle:

```markdown
# [Proje Adi] - Son Durum
**Tarih:** [YYYY-MM-DD HH:MM]
**Aktif Faz:** [Faz bilgisi veya "Faz plani yok"]

## Son Yapilanlar
- [x] [Bu konusmada tamamlanan isler]
- [x] [...]

## Devam Eden Isler
- [ ] [Yarim kalan isler - detayli aciklama]
- [ ] [...]

## Bilinen Sorunlar
- [Cozulmemis hatalar veya teknik borclar]

## Sonraki Adim
[Bir sonraki konusmada ne yapilmasi gerektiginin net aciklamasi]
```

## 3. Memory Guncelle

Eger bu konusmada onemli bir bilgi ogrenmissek (kullanici tercihi, yeni karar, vb.):
- Ilgili memory dosyasini guncelle
- Veya yeni memory olustur

## 4. Git Commit + Push (ZORUNLU - ATLANMAZ!)

**BU ADIM HER ZAMAN CALISTIRILIR.** Iki repo guncellenir:

### 4a. Proje Repo (Proje dizini)
1. Once stage et (hassas dosyalari haric tut):
```bash
git add .claude/durum.md
```
2. Eger baska degismis dosya varsa (git status ile kontrol et), onlari da ekle:
```bash
git add [degisen-dosyalar]
```
3. Commit ve push:
```bash
git commit -m "durum: conversation handoff" && git push 2>&1
```

### 4b. Framework Repo (Komut degisiklikleri varsa)
Eger bu konusmada framework komutlari (panel.md, durum-kaydet.md vb.) degistiyse:
1. Degisen dosyalari framework reposuna kopyala:
```bash
# Windows: D:\Projelerramework\plugins\enver-framework\commands\
# Mac: ~/framework/plugins/enver-framework/commands/
```
2. Framework reposunu commit + push:
```bash
cd [framework-repo] && git add -A && git commit -m "framework: komut guncelleme" && git push 2>&1
```

**NOT:** Framework reposu degismediyse bu adimi atla.

### Sonuc Bildirimi
- Proje push BASARILI: "Proje: GitHub'a yuklendi"
- Proje push BASARISIZ: "UYARI: Proje push basarisiz"
- Framework push BASARILI: "Framework: GitHub'a yuklendi"
- Commit edilecek bir sey yoksa: "Degisiklik yok, push gerekmedi"

## 5. Kullaniciya Bildir

```
╔═══════════════════════════════════════╗
║        DURUM KAYDEDILDI              ║
╠═══════════════════════════════════════╣
║  Dosya: .claude/durum.md             ║
║  Tarih: [tarih]                      ║
║  Yapilanlar: [sayi] is              ║
║  Kalan isler: [sayi] is             ║
║                                      ║
║  Sonraki konusma basinda             ║
║  /panel calistirarak devam edin.    ║
╚═══════════════════════════════════════╝
```

## KURALLAR
- Durum dosyasini HER ZAMAN guncelle, ekleme yapma - tamamen yeniden yaz
- Detayli ol ama gereksiz uzatma
- Eger $ARGUMENTS varsa "Ozel not" olarak durum dosyasina ekle
- Dosya yollarini ve satir numaralarini belirt (yarim kalan isler icin)
