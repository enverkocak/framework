---
description: Canli siteyi tarayicide acip kontrol eder - UI, fonksiyon, giris, test, link tarama
argument-hint: Opsiyonel - bos birakirsan interaktif menu gosterir
---

# Web Kontrol - Canli Site Testi

Canli domainleri tarayicide acarak gorsel ve fonksiyonel kontrol yapar.

## DOMAIN BILGISINI NEREDEN ALIR?

Domain bilgileri HARDCODED DEGILDIR. Su sirayla aranir:

1. **Projenin CLAUDE.md dosyasi** → `## DOMAIN YAPISI` bolumunu oku
2. **Proje memory** → `project_architecture.md` veya benzeri dosyada domain bilgisi ara
3. **Bulunamazsa** → kullaniciya sor: "Bu projenin domainlerini bilmiyorum. Girebilir misin?"

### CLAUDE.md'de beklenen format:
```markdown
## DOMAIN YAPISI
- `ornek.com` - Herkese acik site
- `panel.ornek.com` - Kullanici paneli
- `admin.ornek.com` - Admin paneli
- `api.ornek.com` - API backend
```

### Kisa ad eslestirme:
Domain bilgisini okuduktan sonra su kurallara gore kisa ad ata:
- Ana domain (www olmayan, panel/admin/api olmayan) → `public`
- `panel.` ile baslayan veya aciklamada "panel" gecen → `panel`
- `admin.` / `cxx.` / `yonetim.` ile baslayan → `admin`
- `api.` ile baslayan → `api`
- Eslesmeyenler → domain adindan turkce kisa ad uret

### Test hesaplari:
`~/.claude/vault/test-hesaplari.md` dosyasindan oku.
Proje adina gore (CLAUDE.md'deki proje adi) ilgili bolumu bul.
Yoksa kullaniciya sor.

## INTERAKTIF MENU SISTEMI

### Arguman varsa → direkt calistir
Eger kullanici arguman verdiyse (ornek: `/web-kontrol admin giris yap`) direkt ilgili islemi yap.
Asagidaki arguman ayristirma kurallarini kullan.

### Arguman yoksa → ana menuyu goster
Eger arguman bos veya sadece domain adiysa, kullaniciya interaktif menu goster.
Kullanici numara secerek ilerler. AskUserQuestion araci ile secim al.

```
╔══════════════════════════════════════════════╗
║          WEB KONTROL - ANA MENU             ║
╠══════════════════════════════════════════════╣
║                                             ║
║  1. Hizli Kontrol                           ║
║     Tum domainleri hizlica tara             ║
║     (screenshot + konsol + network)         ║
║                                             ║
║  2. Giris Yap                               ║
║     Test hesabiyla panele giris yap         ║
║                                             ║
║  3. Sayfa Test                              ║
║     Belirli bir sayfayi detayli test et     ║
║                                             ║
║  4. Link Tarama                             ║
║     Kirik linkleri ve 404 sayfalari bul     ║
║                                             ║
║  5. Mobil Test                              ║
║     Responsive tasarim kontrolu             ║
║                                             ║
║  6. SEO Kontrol                             ║
║     Meta tag, baslik, robots kontrolu       ║
║                                             ║
║  7. Performans                              ║
║     Yukleme suresi, kaynak boyutlari        ║
║                                             ║
║  8. Tam Tarama                              ║
║     Giris yap + tum sayfalari gez +         ║
║     butonlari tikla + hatalari raporla      ║
║                                             ║
╚══════════════════════════════════════════════╝
Numara sec (1-8):
```

Her secim kendi alt menusune yonlendirir:

---

### Secim 1: Hizli Kontrol
Domain sec alt menusu goster:
```
Hangi domaini kontrol edeyim?
1. Tumu (public + panel + admin + api)
2. Public (ornek-site.com)
3. Panel (panel.ornek-site.com)
4. Admin (cxx.ornek-site.com)
5. API (api.ornek-site.com)
```
Secime gore ilgili domain(ler)e git, screenshot + konsol + network kontrol et, rapor ver.

---

### Secim 2: Giris Yap
```
Hangi hesapla giris yapayim?
1. Admin (cxx.ornek-site.com)
2. Tedarikci (panel.ornek-site.com)
3. Bayi (panel.ornek-site.com)
```
Secime gore vault'tan hesap bilgilerini oku, formu doldur, giris yap, dashboard kontrol et.

---

### Secim 3: Sayfa Test
Once giris gerekip gerekmedigi sor:
```
Hangi sayfayi test edeyim?
1. Public anasayfa
2. Public blog
3. Public kategori sayfasi
4. Panel dashboard (giris gerekir)
5. Panel urunler (giris gerekir)
6. Panel siparisler (giris gerekir)
7. Admin dashboard (giris gerekir)
8. Admin kullanici yonetimi (giris gerekir)
9. Ozel URL gir
```
"Giris gerekir" olanlarda once giris yap, sonra ilgili sayfaya git ve kontrol et.
Secim 9 ise kullanicidan URL al.

---

### Secim 4: Link Tarama
```
Hangi domainde kirik link tarayayim?
1. Public (ornek-site.com)
2. Panel (giris sonrasi)
3. Admin (giris sonrasi)
```
Secime gore:
1. Sayfadaki TUM <a> linklerini topla (snapshot'tan)
2. Her linke tek tek git
3. HTTP status kodunu kontrol et
4. 404, 500, hata veren linkleri listele
5. Sonuc raporu ver:
```
╔══════════════════════════════════════╗
║       LINK TARAMA RAPORU            ║
╠══════════════════════════════════════╣
║  Taranan: X link                    ║
║  Basarili: X (200)                  ║
║  Kirik: X (404/500/hata)            ║
║                                     ║
║  KIRIK LINKLER:                     ║
║  - /sayfa/xxx → 404                 ║
║  - /kategori/yyy → 500              ║
╚══════════════════════════════════════╝
```

---

### Secim 5: Mobil Test
```
Hangi sayfayi mobilde test edeyim?
1. Public anasayfa (375x812)
2. Public anasayfa (768x1024 - tablet)
3. Panel login (375x812)
4. Admin login (375x812)
5. Ozel URL + boyut gir
```
Secime gore:
1. Tarayiciyi resize et (mcp__playwright__browser_resize)
2. Sayfaya git
3. Screenshot al
4. Tasma, kirik layout, gizlenen elemanlar kontrol et
5. Masaustu ile karsilastirmali rapor ver

---

### Secim 6: SEO Kontrol
```
Hangi sayfanin SEO'sunu kontrol edeyim?
1. Anasayfa
2. Kategori sayfasi
3. Blog
4. Tum public sayfalar (toplu)
5. Ozel URL gir
```
Kontrol edilecekler:
- title tag var mi ve uygun mu?
- meta description var mi?
- h1 var mi ve tekil mi?
- canonical URL var mi?
- og:title, og:description, og:image var mi?
- robots meta tag
- alt tag'siz img var mi?
- Yapısal veri (JSON-LD) var mi?

Raporu tablo formatinda goster.

---

### Secim 7: Performans
```
Hangi domainin performansini olceyim?
1. Public (ornek-site.com)
2. Panel (panel.ornek-site.com)
3. Admin (cxx.ornek-site.com)
```
Kontrol edilecekler:
- Toplam yukleme suresi
- Network istek sayisi ve toplam boyut
- En buyuk kaynaklar (JS, CSS, img)
- Konsol hatalari
- Yavas yuklenenleri raporla

---

### Secim 8: Tam Tarama
En kapsamli test. Sirasiyla:
```
Tam tarama baslatiliyor...
1. Hangi domain? (admin/panel/public)
2. (Giris gerekiyorsa) giris yap
3. Sidebar/menu'deki TUM sayfalari gez
4. Her sayfada:
   - Screenshot al
   - Konsol hatalarini kontrol et
   - Network hatalarini kontrol et
   - Tiklanabilir butonlari kontrol et
5. Toplu rapor ver
```

Tam tarama akisi:
1. Giris yap (gerekiyorsa)
2. Sidebar/navigation'daki tum linkleri snapshot'tan topla
3. Her linke sirayla git
4. Her sayfada: screenshot + konsol + network
5. Hata bulunan sayfalari ayri listele
6. Toplam rapor:
```
╔══════════════════════════════════════════╗
║         TAM TARAMA RAPORU               ║
╠══════════════════════════════════════════╣
║  Domain: [domain]                       ║
║  Taranan sayfa: X                       ║
║  Basarili: X                            ║
║  Hatali: X                              ║
║                                         ║
║  SAYFA DETAYLARI:                       ║
║  ✅ /dashboard - 0 hata                 ║
║  ✅ /urunler - 0 hata                   ║
║  ❌ /siparisler - 2 konsol hatasi       ║
║  ✅ /ayarlar - 0 hata                   ║
║                                         ║
║  TOPLAM HATALAR:                        ║
║  Konsol: X hata                         ║
║  Network: X basarisiz istek             ║
║  Kirik link: X                          ║
╚══════════════════════════════════════════╝
```

---

## DOMAIN TABLOSU

Domain tablosu projenin CLAUDE.md dosyasindan dinamik olarak okunur.
Eger CLAUDE.md'de `## DOMAIN YAPISI` bolumu yoksa kullaniciya sor.

## ARGUMAN AYRISTIRMA (direkt kullanim icin)

Eger kullanici arguman verdiyse menuyu GOSTERME, direkt calistir.

Ornek argumanlar ve ne yapacagi:
- `admin giris yap` → Secim 2 > Admin
- `panel tedarikci giris` → Secim 2 > Tedarikci
- `panel bayi giris` → Secim 2 > Bayi
- `public` → Secim 1 > Public
- `admin` → Secim 1 > Admin
- `public mobil` → Secim 5 > Public anasayfa mobil
- `public seo` → Secim 6 > Anasayfa SEO
- `admin tam tarama` → Secim 8 > Admin
- `panel link tara` → Secim 4 > Panel
- `public kirik link` → Secim 4 > Public
- `public/blog` → Secim 3 > Public blog

## GIRIS AKISI

### 1. Test Hesabini Oku
```
~/.claude/vault/test-hesaplari.md dosyasini oku
Ilgili projenin test hesaplarini bul
```

**ONEMLI**: Eger test hesaplari dosyasi bos veya eksikse:
- Kullaniciya "Test hesaplari tanimli degil. Giris bilgilerini girer misin?" diye sor
- Kullanicidan alinan bilgileri TARAYICIYA gir ama KAYDETME

### 2. Admin Girisi (cxx.ornek-site.com)
```
1. mcp__playwright__browser_navigate → https://cxx.ornek-site.com
2. Snapshot al → login formu elemanlarini bul
3. E-posta alanina yaz → mcp__playwright__browser_type
4. Sifre alanina yaz → mcp__playwright__browser_type
5. "Yonetici Girisi" butonuna tikla → mcp__playwright__browser_click
6. Sayfa yuklenene kadar bekle → mcp__playwright__browser_wait_for
7. SMS dogrulama varsa → kullaniciya sor, kodu gir
8. Dashboard yuklendigini dogrula → screenshot + snapshot
```

### 3. Panel Girisi (panel.ornek-site.com)
```
1. mcp__playwright__browser_navigate → https://panel.ornek-site.com
2. Snapshot al → login formu elemanlarini bul
3. E-posta alanina yaz
4. Sifre alanina yaz
5. "Giris Yap" butonuna tikla
6. SMS dogrulama varsa → kullaniciya sor, kodu gir
7. Dashboard yuklendigini dogrula → screenshot + snapshot
```

## GENEL KONTROL ADIMLARI (her sayfa icin)

1. **Ekran goruntusu al** → `mcp__playwright__browser_take_screenshot`
2. **Snapshot al** → `mcp__playwright__browser_snapshot` (DOM yapisi)
3. **Konsol hatalarini kontrol et** → `mcp__playwright__browser_console_messages`
4. **Network hatalarini kontrol et** → `mcp__playwright__browser_network_requests`

## RAPOR FORMATI

Her islem sonunda rapor goster:
```
╔═══════════════════════════════════════╗
║         WEB KONTROL RAPORU           ║
╠═══════════════════════════════════════╣
║  Domain: [kontrol edilen domain]     ║
║  Aksiyon: [yapilan islem]            ║
║                                      ║
║  Durum:     ✅ / ❌                  ║
║  Konsol:    X hata, X uyari          ║
║  Network:   X basarisiz istek        ║
║  Tasarim:   [duzgun/sorunlu]         ║
║  Giris:     ✅ / ❌ / N/A           ║
║                                      ║
║  SORUNLAR:                           ║
║  - [varsa sorunlar listelenir]       ║
╚═══════════════════════════════════════╝
```

## HATA DUZELTME (Opsiyonel)
Sorun bulunursa kullaniciya sor:
- "X sorun bulundu. Duzeltmemi ister misin?"

## KURALLAR
- Playwright MCP araclari kullan (mcp__playwright__*)
- Her sayfada mutlaka screenshot al ve kullaniciya goster
- Konsol ve network hatalarini mutlaka raporla
- Vault'taki test hesabi bilgilerini SADECE tarayici formuna girmek icin kullan
- Test hesabi bilgilerini ASLA ekrana/log'a yazma
- Test hesabi yoksa kullaniciya sor
- SMS dogrulama kodu gerekirse kullaniciya sor ve bekle
- Menu gosterirken AskUserQuestion araci ile kullanicidan secim al
- Kullanicinin secimini bekle, varsayilan secim YAPMA
