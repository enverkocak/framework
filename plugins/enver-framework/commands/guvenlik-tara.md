---
description: Projedeki guvenlik aciklarini tarar - OWASP Top 10, credentials sizintisi, bagimlilik kontrolu
argument-hint: Opsiyonel - bos birakirsan interaktif menu gosterir
---

# Guvenlik Taramasi

Projenin guvenlik durumunu kapsamli sekilde tarar.

## INTERAKTIF MENU SISTEMI

### Arguman varsa → direkt calistir
Ornek: `/guvenlik-tara kod` → direkt kod taramasi

### Arguman yoksa → menu goster

AskUserQuestion araci ile kullanicidan secim al:

```
╔══════════════════════════════════════════════╗
║        GUVENLIK TARAMASI - MENU             ║
╠══════════════════════════════════════════════╣
║                                             ║
║  1. Tam Tarama                              ║
║     Tum guvenlik kontrollerini calistir     ║
║     (kod + bagimlilik + env + sunucu)       ║
║                                             ║
║  2. Kod Taramasi                            ║
║     SQL injection, XSS, CSRF, eval,        ║
║     hardcoded credentials                   ║
║                                             ║
║  3. Bagimlilik Kontrolu                     ║
║     npm audit, outdated paketler,           ║
║     bilinen zafiyetler                      ║
║                                             ║
║  4. Credentials Sizinti                     ║
║     .env kontrolu, git history,             ║
║     hardcoded API key/sifre/token           ║
║                                             ║
║  5. Sunucu Yapilandirma                     ║
║     HTTPS, CORS, rate limit, helmet,        ║
║     guvenlik header'lari                    ║
║                                             ║
║  6. OWASP Top 10                            ║
║     Injection, Broken Auth, XSS,           ║
║     SSRF, Security Misconfig vb.            ║
║                                             ║
╚══════════════════════════════════════════════╝
Numara sec (1-6):
```

## ARGUMAN ESLESTIRME
- `kod` / `code` → Secim 2
- `bagimlilik` / `dep` / `audit` → Secim 3
- `env` / `credentials` / `sizinti` → Secim 4
- `sunucu` / `server` / `header` → Secim 5
- `owasp` → Secim 6
- `tam` / `full` / (bos) → menu goster veya tam tarama

## TARAMA DETAYLARI

### Secim 1: Tam Tarama
guvenlik-ajani'ni Agent araci ile calistir. Tum kontrolleri sirayla yapar.

### Secim 2: Kod Taramasi
- SQL injection riskleri (raw SQL parametreli sorgu kontrolu)
- XSS riskleri (kullanici girdisi render kontrolu)
- CSRF korumalari
- Path traversal riskleri
- Eval/exec kullanimlari
- Hardcoded credentials
- dangerouslySetInnerHTML kullanimlari

### Secim 3: Bagimlilik Kontrolu
```bash
npm audit 2>&1
```
- Kritik (critical) ve yuksek (high) seviye zafiyetler
- Outdated paketler

### Secim 4: Credentials Sizinti
- .env dosyalarinin .gitignore'da olup olmadigi
- Kodda hardcoded API key, sifre, token
- Git history'de credentials olup olmadigi
- Vault dosyalarinin git'e eklenmedigini dogrula

### Secim 5: Sunucu Yapilandirma
- HTTPS kontrolu
- CORS ayarlari
- Rate limiting
- Helmet/guvenlik header'lari
- Cookie guvenlik flag'leri

### Secim 6: OWASP Top 10
- A01: Broken Access Control
- A02: Cryptographic Failures
- A03: Injection
- A07: XSS
- A09: Security Logging
- A10: SSRF

## SONUC RAPORU

```
╔═══════════════════════════════════════════╗
║         GUVENLIK TARAMASI SONUCU         ║
╠═══════════════════════════════════════════╣
║                                           ║
║  KRITIK:  [sayi] bulgu                   ║
║  YUKSEK:  [sayi] bulgu                   ║
║  ORTA:    [sayi] bulgu                   ║
║  DUSUK:   [sayi] bulgu                   ║
║                                           ║
╠═══════════════════════════════════════════╣
║  DETAYLAR                                ║
║  [Her bulgu: dosya, satir, aciklama]     ║
╠═══════════════════════════════════════════╣
║  ONERILER                                ║
║  [Duzeltme onerileri]                    ║
╚═══════════════════════════════════════════╝
```

Tarama sonrasi: "X kritik bulgu var. Duzeltmemi ister misin?"

## KURALLAR
- Kritik bulgularda hemen duzeltme oner
- Vault icerigini ASLA raporlama
- Menu gosterirken AskUserQuestion ile secim al
- Kullanicinin secimini bekle, varsayilan secim YAPMA
