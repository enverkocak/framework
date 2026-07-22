---
description: Framework ayarlari - memory, vault, hook, izin, versiyon yonetimi
argument-hint: Opsiyonel - bos birak = menu, veya direkt (memory, vault, hook, izin, guncelle)
---

# Framework Ayarlari

Memory, vault, hook ve framework versiyon yonetimi.

## MENU (arguman yoksa AskUserQuestion ile goster)

```
[1] Memory Goruntule     Tum memory dosyalari
[2] Memory Duzenle       Belirli memory guncelle
[3] Memory Sil           Gereksiz memory kaldir
[4] Vault Durumu         Vault dosya listesi (icerik GIZLI)
[5] Vault Guncelle       Vault dosyasina bilgi ekle
[6] Hook Yonet           settings.json hook'lari
[7] Framework Guncelle   Plugin versiyonu guncelle
[8] Izinler              Izin ayarlari goruntule/duzenle
[0] ← Ana Menu
```

## NASIL CALISIR

### [1] Memory Goruntule
Proje memory dizinindeki tum .md dosyalarini listele.
Her birinin basligini ve aciklamasini goster.

### [2] Memory Duzenle
1. Memory dosyalarini listele
2. Kullanici secer
3. Mevcut icerigi goster
4. Ne degisecegini sor
5. Guncelle + MEMORY.md index'ini guncelle

### [3] Memory Sil
1. Listele, kullanici secer
2. Onay iste
3. Sil + MEMORY.md'den kaldir

### [4] Vault Durumu
`~/.claude/vault/index.md` oku, SADECE dosya adlarini goster.
Icerik ASLA gosterilmez.

### [5] Vault Guncelle
Kullaniciya hangi dosyayi sorunsun.
Yeni icerigi al, dosyaya yaz.
Icerigi ekrana YAZMA.

### [6] Hook Yonet
`~/.claude/settings.json` ve proje `.claude/settings.local.json` oku.
Hook'lari listele, duzenleme sor.

### [7] Framework Guncelle
Framework repo'dan git pull + dosyalari kopyala.
Versiyon numarasini goster.

### [8] Izinler
settings.json'daki izin ayarlarini goster.
Degisiklik gerekiyorsa update-config skill'ini kullan.

## KURALLAR
- Vault icerigi ASLA ekrana yazilmaz
- Memory silmede onay zorunlu
- Framework guncelleme oncesinde mevcut versiyonu goster
