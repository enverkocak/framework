---
description: Memory, plan ve gecici dosyalari temizler - duplikatlari siler, arsivler
argument-hint: Opsiyonel - belirli bir alan (memory, plan, gecici)
---

# Temizlik

Proje ve global memory/plan dosyalarini temizler ve duzenler.

## 1. Tarama

Asagidaki alanlari tara:

### 1.1 Memory Dosyalari
- Proje memory dizinindeki tum dosyalari oku
- Duplikat veya guncel olmayan memory'leri tespit et
- MEMORY.md index'inin dogru olup olmadigini kontrol et

### 1.2 Plan Dosyalari
- `~/.claude/plans/` dizinindeki planlari listele
- Eski/tamamlanmis planlari tespit et

### 1.3 Gecici Dosyalar
- `/tmp/` altindaki proje ile ilgili gecici dosyalar
- Eski screenshot'lar
- Build artifact'lari

## 2. Rapor

```
╔═══════════════════════════════════════╗
║          TEMIZLIK RAPORU             ║
╠═══════════════════════════════════════╣
║                                      ║
║  MEMORY:                             ║
║  - [sayi] dosya mevcut              ║
║  - [sayi] duplikat/eski             ║
║  - Index: [guncel/guncel degil]     ║
║                                      ║
║  PLANLAR:                            ║
║  - [sayi] plan mevcut              ║
║  - [sayi] eski/tamamlanmis         ║
║                                      ║
║  GECICI:                             ║
║  - [sayi] gecici dosya              ║
║                                      ║
╠═══════════════════════════════════════╣
║  ONERILER                            ║
║  [Silinmesi/arsivlenmesi gereken]   ║
╚═══════════════════════════════════════╝
```

## 3. Kullanici Onayi

- Silme/arsivleme islemleri icin MUTLAKA kullanici onayi al
- Otomatik silme YAPMA

## KURALLAR
- Vault dosyalarina DOKUNMA
- Silmeden once her zaman kullaniciya sor
- Eger $ARGUMENTS ile belirli bir alan istenmisse sadece onu temizle
