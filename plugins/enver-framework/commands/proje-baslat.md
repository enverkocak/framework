---
description: Yeni proje sablonla baslatir - CLAUDE.md, faz plani, dizin yapisi olusturur
argument-hint: Proje turu (web, mobil) ve proje adi
---

# Proje Baslat

Yeni bir projeyi framework sablonlariyla baslatir.

## 1. Bilgi Topla

Kullaniciya sor:
- **Proje adi:** (eger $ARGUMENTS'ta yoksa)
- **Proje turu:** web / mobil / desktop
- **Teknik stack:** (veya varsayilani kullan)
- **Domain yapisi:** (varsa)

## 2. Sablonu Oku

Proje turune gore uygun sablonu oku:
- Web: `~/.claude/sablonlar/claude-md-web.md`
- Mobil: `~/.claude/sablonlar/claude-md-mobil.md`

## 3. Proje Dosyalarini Olustur

### 3.1 CLAUDE.md
- Sablondaki placeholder'lari doldur
- Proje spesifik kurallari ekle

### 3.2 Faz Plani
```
.claude/faz-plani.md
```
Faz sablonunu (`~/.claude/sablonlar/faz-sablonu.md`) kullanarak ilk faz planini olustur.

### 3.3 Durum Dosyasi
```
.claude/durum.md
```
Bos durum dosyasi olustur.

## 4. Vault'a Ekle (gerekiyorsa)

Eger proje icin ozel credentials varsa, vault'a yeni dosya eklenmesi gerektigini bildir.

## 5. Sonuc

```
╔═══════════════════════════════════════╗
║      PROJE BASLATILDI                ║
╠═══════════════════════════════════════╣
║  Proje: [ad]                         ║
║  Tur: [web/mobil]                    ║
║  Stack: [stack bilgisi]              ║
║                                      ║
║  Olusturulan dosyalar:               ║
║  - CLAUDE.md                         ║
║  - .claude/faz-plani.md              ║
║  - .claude/durum.md                  ║
║                                      ║
║  Sonraki adim:                       ║
║  Faz 1'e baslayin!                   ║
╚═══════════════════════════════════════╝
```

## KURALLAR
- Global CLAUDE.md kurallari otomatik devralinir (tekrar yazma)
- Her proje CLAUDE.md'si sadece proje-spesifik kurallari icerir
- Mevcut bir CLAUDE.md varsa uzerine yazma, once kullaniciya sor
