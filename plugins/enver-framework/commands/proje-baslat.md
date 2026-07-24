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

### 3.2 Proje Tanimi
```
.claude/proje.json
```

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/projeler/proje.py" olustur --ad "<ad>"
```

### 3.3 Faz Plani
Faz motoru plani `hafiza/faz-plani.json` dosyasindan okur. Elle dosya
yazilmaz, fazlar motora eklenir:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/faz/faz.py" ekle 1 "<faz adi>" \
  --kapi "<kapi komutu>" --madde "<madde>"
```

Kesif yapildiysa taslak `_calisma/faz-plani.md` dosyasindadir
(`kesif.py plana-dok` ciktisi); maddeleri oradan alip motora ekle.

### 3.4 Durum Dosyasi
Durum `hafiza/durum.md` dosyasinda tutulur; acilis brifingi orayi okur:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/hafiza/oturum.py" durum --yaz "Proje kuruldu, Faz 1 bekliyor"
```

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
║  - .claude/proje.json                ║
║  - hafiza/faz-plani.json             ║
║  - hafiza/durum.md                   ║
║                                      ║
║  Sonraki adim:                       ║
║  Faz 1'e baslayin!                   ║
╚═══════════════════════════════════════╝
```

## KURALLAR
- Global CLAUDE.md kurallari otomatik devralinir (tekrar yazma)
- Her proje CLAUDE.md'si sadece proje-spesifik kurallari icerir
- Mevcut bir CLAUDE.md varsa uzerine yazma, once kullaniciya sor
