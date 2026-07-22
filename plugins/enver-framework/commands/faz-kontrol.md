---
description: Aktif fazin kapi kontrollerini calistirir - lint, type check, guvenlik, test, build
argument-hint: Opsiyonel - bos birakirsan interaktif menu gosterir
---

# Faz Kontrol - Kapi Kontrolu

Aktif fazin kapi kontrollerini calistirir.

## INTERAKTIF MENU SISTEMI

### Arguman varsa → direkt calistir
Ornek: `/faz-kontrol lint` → direkt lint kontrolu

### Arguman yoksa → menu goster

AskUserQuestion araci ile kullanicidan secim al:

```
╔══════════════════════════════════════════════╗
║        FAZ KONTROL - MENU                   ║
╠══════════════════════════════════════════════╣
║                                             ║
║  1. Tum Kapi Kontrolleri                    ║
║     Lint + Type + Guvenlik + Test + Build   ║
║     hepsini sirayla calistir                ║
║                                             ║
║  2. Lint Kontrolu                           ║
║     ESLint ile kod kalitesi kontrolu        ║
║                                             ║
║  3. Type Check                              ║
║     TypeScript tip kontrolu (tsc --noEmit)  ║
║                                             ║
║  4. Guvenlik Taramasi                       ║
║     Guvenlik ajani ile hizli tarama         ║
║                                             ║
║  5. Test                                    ║
║     Unit/integration testleri calistir      ║
║                                             ║
║  6. Build                                   ║
║     Production build kontrolu               ║
║                                             ║
╚══════════════════════════════════════════════╝
Numara sec (1-6):
```

## ARGUMAN ESLESTIRME
- `lint` / `eslint` → Secim 2
- `type` / `tsc` / `typescript` → Secim 3
- `guvenlik` / `security` → Secim 4
- `test` / `vitest` → Secim 5
- `build` → Secim 6
- `tum` / `full` / (bos) → menu goster

## KONTROL ADIMLARI

### 0. Faz Planini Oku
- `.claude/faz-plani.md` dosyasini oku
- Aktif fazi bul (DEVAM_EDIYOR durumundaki)
- Faz plani yoksa kullaniciya bildir ve dur

### Secim 1: Tum Kontroller
Asagidaki 5 kontrolu sirayla calistir, her birinin sonucunu raporla.

### Secim 2: Lint Kontrolu
```bash
npx eslint . --ext .js,.jsx,.ts,.tsx 2>&1 || echo "LINT_HATASI"
```
- Hata yoksa: GECTI
- Hata varsa: KALDI + hata sayisi + duzeltme oner

### Secim 3: Type Check
```bash
npx tsc --noEmit 2>&1 || echo "TYPE_HATASI"
```
- Hata yoksa: GECTI
- Hata varsa: KALDI + hata sayisi + duzeltme oner

### Secim 4: Guvenlik Taramasi
- guvenlik-ajani'ni calistir (Agent araci ile)
- Kritik bulgu yoksa: GECTI
- Kritik bulgu varsa: KALDI + bulgu listesi

### Secim 5: Test
```bash
npm test 2>&1 || npx vitest run 2>&1 || echo "TEST_HATASI"
```
- Hepsini gecerse: GECTI
- Basarisiz varsa: KALDI + basarisiz test sayisi

### Secim 6: Build
```bash
npm run build 2>&1 || echo "BUILD_HATASI"
```
- Basarili: GECTI
- Basarisiz: KALDI + hata

## SONUC RAPORU

```
╔═══════════════════════════════════════╗
║     FAZ [N] KAPI KONTROLU            ║
╠═══════════════════════════════════════╣
║  Lint:       [GECTI/KALDI]           ║
║  Type Check: [GECTI/KALDI/ATLA]      ║
║  Guvenlik:   [GECTI/KALDI]           ║
║  Test:       [GECTI/KALDI/ATLA]      ║
║  Build:      [GECTI/KALDI]           ║
╠═══════════════════════════════════════╣
║  SONUC: [TUMU GECTI / X KALDI]       ║
╚═══════════════════════════════════════╝
```

## FAZ PLANI GUNCELLEME
- Tumu gectiyse: Faz durumunu TAMAMLANDI yap
- Kalan varsa: Sorunlari listele, "Duzeltmemi ister misin?" sor

## KURALLAR
- Her kontrolu calistirmadan once kullaniciya bilgi ver
- Basarisiz kontrollerde detayli hata mesaji goster
- Menu gosterirken AskUserQuestion ile secim al
- Kullanicinin secimini bekle, varsayilan secim YAPMA
