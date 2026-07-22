---
description: Localhost tarayicide acip kontrol eder - gelistirme ortaminda UI ve fonksiyon testi
argument-hint: Opsiyonel - bos birakirsan interaktif menu gosterir
---

# Canli Kontrol - Localhost Testi

Gelistirme ortamindaki uygulamalari tarayicide acarak gorsel ve fonksiyonel kontrol yapar.

## PORT BILGISINI NEREDEN ALIR?

Port bilgileri HARDCODED DEGILDIR. Su sirayla aranir:

1. **Projenin CLAUDE.md dosyasi** → `## TEKNIK STACK` veya `## PROJE YAPISI` bolumundan cikarsanabilir
2. **package.json dosyalari** → `scripts.dev` komutundaki port numaralari
3. **Calisanlardan** → `lsof -i` veya `netstat` ile aktif portlari bul
4. **Bulunamazsa** → kullaniciya sor

### Yaygin port desenleri:
- Next.js → 3000
- Vite → 5173
- Express → 3003 veya 3001
- package.json'daki --port flag'i

## INTERAKTIF MENU SISTEMI

### Arguman varsa → direkt calistir
Ornek: `/canli-kontrol panel` → direkt panel kontrolu

### Arguman yoksa → menu goster

AskUserQuestion araci ile kullanicidan secim al:

```
╔══════════════════════════════════════════════╗
║       CANLI KONTROL - LOCALHOST MENU        ║
╠══════════════════════════════════════════════╣
║                                             ║
║  1. Hizli Kontrol                           ║
║     Tum uygulamalari kontrol et             ║
║     (panel + web + api)                     ║
║                                             ║
║  2. Panel (localhost:5173)                  ║
║     Vite dev server - React panel           ║
║                                             ║
║  3. Web (localhost:3000)                    ║
║     Next.js public frontend                 ║
║                                             ║
║  4. API (localhost:3003)                    ║
║     Express backend health check            ║
║                                             ║
║  5. Giris Yap + Test                        ║
║     Panel'e giris yap ve sayfalari gez      ║
║                                             ║
║  6. Mobil Test                              ║
║     Responsive tasarim kontrolu             ║
║                                             ║
║  7. Tam Tarama                              ║
║     Tum sayfalari gez + hatalari raporla    ║
║                                             ║
╚══════════════════════════════════════════════╝
Numara sec (1-7):
```

## LOCALHOST PORTLARI

| Uygulama | Port | URL |
|----------|------|-----|
| API | 3003 | http://localhost:3003 |
| Panel (Vite) | 5173 | http://localhost:5173 |
| Web (Next.js) | 3000 | http://localhost:3000 |

## ARGUMAN ESLESTIRME
- `panel` → Secim 2
- `web` → Secim 3
- `api` → Secim 4
- `giris` / `login` → Secim 5
- `mobil` / `responsive` → Secim 6
- `tam` / `full` → Secim 7
- `panel/login`, `web/blog` → belirli sayfa yolu

## PORT KONTROL (ONCELIKLI)

Her testten once uygulamanin calisip calismadigini kontrol et:
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:PORT
```
Calismiyorsa: "Uygulama calismiyor. Baslatayim mi?" sor.

## KONTROL ADIMLARI (her sayfa icin)

1. **Ekran goruntusu al** → `mcp__playwright__browser_take_screenshot`
2. **Snapshot al** → `mcp__playwright__browser_snapshot`
3. **Konsol hatalarini kontrol et** → `mcp__playwright__browser_console_messages`
4. **Network hatalarini kontrol et** → `mcp__playwright__browser_network_requests`

## SECIM DETAYLARI

### Secim 5: Giris Yap + Test
Alt menu:
```
Hangi hesapla giris yapayim?
1. Admin
2. Tedarikci
3. Bayi
```
Vault'tan test hesap bilgilerini oku, giris yap, dashboard kontrol et.

### Secim 6: Mobil Test
Alt menu:
```
Hangi uygulamayi mobilde test edeyim?
1. Panel (375x812 - telefon)
2. Panel (768x1024 - tablet)
3. Web (375x812 - telefon)
4. Web (768x1024 - tablet)
```

### Secim 7: Tam Tarama
1. Giris yap
2. Sidebar'daki tum linkleri topla
3. Her sayfaya git + screenshot + konsol + network
4. Toplu rapor ver

## RAPOR FORMATI

```
╔═══════════════════════════════════════╗
║       CANLI KONTROL RAPORU           ║
╠═══════════════════════════════════════╣
║  Uygulama: [panel/web/api]           ║
║  URL: http://localhost:XXXX          ║
║                                      ║
║  Durum:     ✅ / ❌                  ║
║  Konsol:    X hata, X uyari          ║
║  Network:   X basarisiz istek        ║
║  Tasarim:   [duzgun/sorunlu]         ║
║                                      ║
║  SORUNLAR:                           ║
║  - [varsa sorunlar listelenir]       ║
╚═══════════════════════════════════════╝
```

Sorun bulunursa: "X sorun bulundu. Duzeltmemi ister misin?" sor.

## KURALLAR
- Playwright MCP araclari kullan (mcp__playwright__*)
- Her kontrolde mutlaka screenshot al
- Uygulama calismiyorsa otomatik baslatMA, kullaniciya sor
- API testlerinde hassas veri gosterME
- Menu gosterirken AskUserQuestion ile secim al
- Kullanicinin secimini bekle, varsayilan secim YAPMA
