---
description: Framework ana menusu - tum komutlara tek noktadan eris, 4 sekme 16 kategori 80+ islem
argument-hint: Opsiyonel - bos birak = ana menu, veya direkt (web, api-test, deploy, db, git, iskele...)
---

# Panel Enver - Framework Ana Menu v2.0

Tum framework islemlerine tek noktadan erisim.
4 sekme → 16 kategori → 80+ alt islem.

## CALISMA MANTIGI

1. Once git sync (proje + framework) + kisa dashboard bilgisi goster
2. Arguman yoksa → ANA MENU goster (AskUserQuestion 4 sekme)
3. Kullanici kategori secer → ALT MENU goster (AskUserQuestion)
4. Kullanici islem secer → calistir
5. Arguman varsa → direkt ilgili isleme git

## DASHBOARD (menu ustunde gosterilir)

Once su komutlari calistir:
```bash
git pull 2>&1 || echo "Pull basarisiz"
```
Sonra kisa ozet:
```
ENVER FRAMEWORK v2.0 | Proje: [ad] (v[surum])
Sync: ✅ | Faz: [durum] | Hafiza: [X] | Vault: [X]
```

## ANA MENU (AskUserQuestion - 4 Sekme)

```json
{
  "questions": [
    {
      "question": "Test & Izleme - Site testi, API testi, monitoring, guvenlik",
      "header": "Test",
      "multiSelect": false,
      "options": [
        {
          "label": "Web & Mobil Test",
          "description": "Canli site + localhost: screenshot, giris, link tara, mobil, SEO, tam tarama"
        },
        {
          "label": "API & Socket Test",
          "description": "Tum endpoint'leri test et, Socket.io kontrol, performans olc"
        },
        {
          "label": "Monitoring",
          "description": "Sunucu sagligi: CPU/RAM, PM2, DB baglanti, SSL, uptime, hata takip"
        },
        {
          "label": "Guvenlik",
          "description": "OWASP Top 10, SQL inj, XSS, credentials, npm audit, sunucu config"
        }
      ]
    },
    {
      "question": "Gelistirme - Kod iskele, kalite, git, dokumantasyon",
      "header": "Kod",
      "multiSelect": false,
      "options": [
        {
          "label": "Kod Iskele",
          "description": "Yeni CRUD endpoint, React component, migration, middleware sablonla olustur"
        },
        {
          "label": "Kod Kalitesi",
          "description": "Lint fix, type check, import temizle, TODO, dead code, regex test, faz kontrol"
        },
        {
          "label": "Git & PR",
          "description": "Branch, commit, PR olustur, merge, conflict coz, diff goster"
        },
        {
          "label": "Dokumantasyon",
          "description": "API endpoint listesi, DB sema, changelog, mimari diyagram, README"
        }
      ]
    },
    {
      "question": "Operasyon - Deploy, DB, log, backup, cron",
      "header": "Ops",
      "multiSelect": false,
      "options": [
        {
          "label": "Deploy & Diff",
          "description": "Sunucuya gonder (API/panel/web/tam), rollback, deploy oncesi diff onizleme"
        },
        {
          "label": "DB & Redis",
          "description": "Tablo, migration, seed, sorgu, yavas sorgu, DB diff, Redis key yonetimi"
        },
        {
          "label": "Log & Hata",
          "description": "PM2/Nginx log izle, hata filtrele, arama, hata grupla + trend"
        },
        {
          "label": "Backup & Cron",
          "description": "DB yedek al/yukle, dosya yedek, cron listele/ekle/sil, otomatik yedek"
        }
      ]
    },
    {
      "question": "Proje - Ortam, gorev, rapor, ayarlar",
      "header": "Proje",
      "multiSelect": false,
      "options": [
        {
          "label": "Ortam & Ayar",
          "description": "Ortam degistir (.env), framework ayarlari, memory, vault, hook yonet"
        },
        {
          "label": "Gorev & Rapor",
          "description": "Gorev listesi, haftalik saglik raporu, bagimlilik haritasi, snippet"
        },
        {
          "label": "Durum Kaydet",
          "description": "Nerede kaldigini kaydet, conversation handoff, temizlik"
        },
        {
          "label": "Proje Baslat",
          "description": "Yeni proje sablonla baslat, CLAUDE.md, faz plani, dizin yapisi"
        }
      ]
    }
  ]
}
```

---

## ALT MENULER

Her kategori secildiginde AskUserQuestion ile alt menu goster.
Alt menulerde de max 4 sekme x 4 secenek kullanilabilir (gerekirse).

---

### [Test-1] Web & Mobil Test

```json
{
  "questions": [{
    "question": "Web & Mobil Test - Ne yapmak istersin?",
    "header": "WebTest",
    "multiSelect": false,
    "options": [
      {"label": "Hizli Kontrol", "description": "Tum domainler: screenshot + konsol + network hata kontrol"},
      {"label": "Giris Yap", "description": "Admin / Tedarikci / Bayi hesabiyla panele giris yap"},
      {"label": "Link & SEO Tara", "description": "Kirik link bul, meta tag kontrol, robots, structured data"},
      {"label": "Mobil & Tam Tarama", "description": "Responsive test (telefon+tablet) veya tum sayfalari gez"}
    ]
  }, {
    "question": "Ortam sec:",
    "header": "Ortam",
    "multiSelect": false,
    "options": [
      {"label": "Canli Site", "description": "Production domainleri test et (ornek-site.com)"},
      {"label": "Localhost", "description": "Dev ortamini test et (localhost:5173/3000/3003)"}
    ]
  }]
}
```

**Hizli Kontrol secilirse** → domain sec (tumu/public/panel/admin/api) → tara → rapor
**Giris Yap secilirse** → hesap sec (admin/tedarikci/bayi) → vault'tan bilgi oku → form doldur → giris → dashboard kontrol
**Link & SEO secilirse** → domain sec → linkleri topla → tek tek kontrol → rapor VEYA SEO meta tag analizi
**Mobil & Tam Tarama secilirse** → cihaz sec (telefon/tablet/ikisi) → resize + screenshot VEYA giris + tum sayfalari gez

Domain: CLAUDE.md → `## DOMAIN YAPISI` | Port: package.json | Hesap: vault/test-hesaplari.md

---

### [Test-2] API & Socket Test

```json
{
  "questions": [{
    "question": "API & Socket Test",
    "header": "API",
    "multiSelect": false,
    "options": [
      {"label": "Tam API Tara", "description": "Tum endpoint'leri otomatik kesfet ve test et (status + response time)"},
      {"label": "Tek Endpoint", "description": "Belirli bir endpoint'i detayli test et (GET/POST/PUT/DELETE)"},
      {"label": "Socket.io Test", "description": "WebSocket baglanti, auth, event dinle/gonder, reconnect testi"},
      {"label": "Performans Olc", "description": "Endpoint response time sirala, yavas olanlari bul, N+1 tespit"}
    ]
  }]
}
```

### Tam API Tara nasil calisir:
1. `apps/api/routes/` dizinindeki tum dosyalari oku
2. `router.get/post/put/patch/delete` satirlarini bul
3. Auth gerektiren ve gerektirmeyen endpoint'leri ayir
4. Auth gerektirenlerde vault'tan token al (once login endpoint'i cagir)
5. Her endpoint'e istek gonder, status + response time kaydet
6. Rapor:
```
╔══════════════════════════════════════════════╗
║          API TEST RAPORU                    ║
╠══════════════════════════════════════════════╣
║  Taranan: 48 endpoint                      ║
║  Basarili: 45 (200/201)                    ║
║  Hatali: 3                                 ║
║                                             ║
║  HATALI ENDPOINT'LER:                      ║
║  ❌ GET /api/admin/xxx → 500 (142ms)       ║
║  ❌ POST /api/yyy → 404 (12ms)             ║
║  ❌ GET /api/zzz → timeout (>5s)           ║
║                                             ║
║  EN YAVAS 5:                               ║
║  ⚠ GET /api/vitrin/urunler → 2.3s         ║
║  ⚠ GET /api/admin/dashboard → 1.8s        ║
╚══════════════════════════════════════════════╝
```

### Socket.io Test nasil calisir:
1. `io.connect(API_URL)` ile baglanti kur
2. Handshake basarili mi kontrol et
3. JWT token ile auth event gonder
4. Bildirim event'lerini dinle
5. Reconnect senaryosu test et
6. Sonuc raporu ver

---

### [Test-3] Monitoring

```json
{
  "questions": [{
    "question": "Monitoring - Sunucu sagligi",
    "header": "Monitor",
    "multiSelect": false,
    "options": [
      {"label": "Genel Bakis", "description": "Tek seferde: API health, CPU, RAM, disk, PM2, DB, SSL, uptime"},
      {"label": "Hata Takip", "description": "Son 24h benzersiz hatalari grupla, tekrar sayisi, trend (artis/azalis)"},
      {"label": "SSL & Domain", "description": "SSL sertifika bitis tarihi + tum domainlerin HTTP status kontrolu"},
      {"label": "Kaynak Detay", "description": "CPU/RAM/disk detay, PM2 process listesi, DB baglanti pool durumu"}
    ]
  }]
}
```

### Hata Takip nasil calisir:
1. SSH → `pm2 logs --err --lines 500 --nostream` ile hata loglarini cek
2. Hatalari mesaj bazinda grupla (ayni hatalar tek satirda)
3. Her hata grubu icin: sayi, ilk gorunme, son gorunme, dosya:satir
4. Trendi goster (dun vs bugun karsilastir)
5. Rapor:
```
╔══════════════════════════════════════════════╗
║          HATA TAKIP RAPORU                  ║
╠══════════════════════════════════════════════╣
║  Son 24 saat: 3 benzersiz hata, 47 tekrar  ║
║  Trend: ↗ artis (dun: 12 tekrar)           ║
║                                             ║
║  1. DB timeout (38 tekrar) ↗               ║
║     → config/database.js:45                ║
║     İlk: 08:15 | Son: 14:22               ║
║                                             ║
║  2. CORS rejected (7 tekrar) →             ║
║     → index.js:232                         ║
║                                             ║
║  3. File not found (2 tekrar) ↘            ║
║     → routes/uploads.js:89                 ║
╚══════════════════════════════════════════════╝
```

---

### [Test-4] Guvenlik

```json
{
  "questions": [{
    "question": "Guvenlik Taramasi",
    "header": "Guvenlik",
    "multiSelect": false,
    "options": [
      {"label": "Tam Tarama", "description": "Kod + bagimlilik + credentials + sunucu + OWASP hepsini tara"},
      {"label": "Kod Taramasi", "description": "SQL injection, XSS, CSRF, eval, path traversal, hardcoded secret"},
      {"label": "Bagimlilik & Audit", "description": "npm audit, outdated paketler, bilinen zafiyetler"},
      {"label": "Sunucu & OWASP", "description": "HTTPS, CORS, rate limit, helmet, cookie flag, OWASP A01-A10"}
    ]
  }]
}
```

---

### [Kod-1] Kod Iskele (Scaffolding)

```json
{
  "questions": [{
    "question": "Ne olusturmak istersin?",
    "header": "Iskele",
    "multiSelect": false,
    "options": [
      {"label": "CRUD Endpoint", "description": "Route + service + migration + tip dosyasi (Express REST API)"},
      {"label": "React Sayfa", "description": "Yeni panel sayfasi: component + route + sidebar link"},
      {"label": "Migration", "description": "Yeni DB migration dosyasi (CREATE TABLE / ALTER TABLE)"},
      {"label": "Middleware", "description": "Yeni Express middleware (auth, validation, rate-limit sablonu)"}
    ]
  }]
}
```

### CRUD Endpoint nasil calisir:
1. Kullaniciya sor: kaynak adi (ornek: "urun-yorumlari")
2. Mevcut projenin route/service desenini analiz et (ornek dosya oku)
3. Olustur:
   - `apps/api/routes/urun-yorumlari.js` (GET list, GET detail, POST, PUT, DELETE)
   - `apps/api/services/urunYorumlariService.js` (is mantigi)
   - `apps/api/migrations/[timestamp]_urun_yorumlari.sql` (CREATE TABLE)
   - index.js'e route import'u ekle
4. Kullaniciya dosyalari goster, onay iste, yaz

### React Sayfa nasil calisir:
1. Kullaniciya sor: sayfa adi, hangi panelde (panel/admin)
2. Mevcut sayfa desenini analiz et
3. Olustur:
   - `apps/panel/src/pages/[SayfaAdi].tsx` (component)
   - App.tsx'e lazy import + route ekle
   - Sidebar'a link ekle
4. Onay + yaz

---

### [Kod-2] Kod Kalitesi

```json
{
  "questions": [{
    "question": "Kod Kalitesi - Hangi islem?",
    "header": "Kalite",
    "multiSelect": false,
    "options": [
      {"label": "Faz Kontrol", "description": "Lint + TypeScript + guvenlik + test + build kapi kontrolleri"},
      {"label": "Auto-Fix & Temizle", "description": "ESLint fix, kullanilmayan import kaldir, dead code bul"},
      {"label": "TODO & Istatistik", "description": "TODO/FIXME listele, satir sayisi, dosya dagilimi, en buyuk dosyalar"},
      {"label": "Regex & Desen Test", "description": "Projede kullanilan regex'leri test verisiyle dogrula (telefon, email, slug)"}
    ]
  }]
}
```

### Regex & Desen Test nasil calisir:
1. Projede regex pattern'leri bul (grep ile `/regex/` veya `new RegExp`)
2. Her pattern icin test verileri olustur (gecerli + gecersiz ornekler)
3. Canli test calistir, yanlis eslesen/eslesmeyen ornekleri goster
4. Ozellikle Turkce karakter iceren pattern'lerde i/I problemini kontrol et
5. Rapor: pattern, dosya, gecen/kalan test sayisi

---

### [Kod-3] Git & PR

```json
{
  "questions": [{
    "question": "Git Islemleri",
    "header": "Git",
    "multiSelect": false,
    "options": [
      {"label": "Durum & Log", "description": "git status, son commitler, degisen dosyalar, branch bilgisi"},
      {"label": "Branch & Commit", "description": "Yeni branch olustur, degisiklikleri commit et (mesaj yardimi)"},
      {"label": "PR Olustur", "description": "GitHub PR olustur: baslik + aciklama + commit ozeti"},
      {"label": "Merge & Conflict", "description": "Branch birlestir, conflict varsa dosya dosya coz"}
    ]
  }]
}
```

---

### [Kod-4] Dokumantasyon

```json
{
  "questions": [{
    "question": "Dokumantasyon",
    "header": "Docs",
    "multiSelect": false,
    "options": [
      {"label": "API Docs", "description": "Route dosyalarindan endpoint listesi cikar (method, path, auth, aciklama)"},
      {"label": "DB Sema", "description": "Tum tablo ve kolonlari dokumante et, iliskileri goster"},
      {"label": "Changelog", "description": "Son commit'lerden degisiklik notu olustur (feature/fix/improvement)"},
      {"label": "README & Env", "description": "README guncelle, .env.example olustur (degerler gizli), mimari diyagram"}
    ]
  }]
}
```

---

### [Ops-1] Deploy & Diff

```json
{
  "questions": [{
    "question": "Deploy & Diff",
    "header": "Deploy",
    "multiSelect": false,
    "options": [
      {"label": "Tam Deploy", "description": "git push + pull + pnpm install + build + restart (hepsi sirayla)"},
      {"label": "Parcali Deploy", "description": "Sadece API / sadece Panel / sadece Web secenekleri"},
      {"label": "Diff Onizleme", "description": "Deploy oncesi: degisen dosyalar, yeni endpoint'ler, .env key farki"},
      {"label": "Rollback & Durum", "description": "Onceki versiyona don veya PM2 status + son deploy bilgisi"}
    ]
  }]
}
```

### Diff Onizleme nasil calisir:
1. `git log --oneline origin/master..HEAD` ile deploy edilecek commit'leri goster
2. `git diff --stat origin/master..HEAD` ile degisen dosya listesi
3. Yeni/silinen route dosyalarini tespit et → yeni endpoint raporu
4. .env key farki: lokal vs sunucu .env dosyalarindaki KEY isimlerini karsilastir (deger DEGIL)
5. Migration kontrolu: yeni migration dosyasi var mi? sunucuda calistirildi mi?
6. Rapor:
```
╔══════════════════════════════════════════════╗
║        DEPLOY ONCESI DIFF                   ║
╠══════════════════════════════════════════════╣
║  Commit: 5 yeni commit                     ║
║  Dosya:  12 degisti, 3 yeni, 1 silindi     ║
║                                             ║
║  YENi ENDPOINT'LER:                        ║
║  + POST /api/urun-yorumlari                ║
║  + GET  /api/urun-yorumlari/:id            ║
║                                             ║
║  MIGRATION:                                ║
║  ⚠ 1 yeni migration bekliyor              ║
║                                             ║
║  ENV FARKI:                                ║
║  ⚠ REDIS_URL lokal'de var, sunucuda yok   ║
╚══════════════════════════════════════════════╝
```

---

### [Ops-2] DB & Redis

```json
{
  "questions": [{
    "question": "DB & Redis Yonetimi",
    "header": "DB",
    "multiSelect": false,
    "options": [
      {"label": "Tablo & Sorgu", "description": "Tablo listele, kolon incele, SELECT sorgu calistir, yavas sorgular"},
      {"label": "Migration & Seed", "description": "Migration olustur/calistir/geri al, test verisi yukle"},
      {"label": "DB Karsilastir", "description": "Localhost vs sunucu sema farki: eksik tablo, farkli kolon, bekleyen migration"},
      {"label": "Redis Yonet", "description": "Key listele/ara, TTL kontrol, cache temizle, rate-limit debug"}
    ]
  }]
}
```

### DB Karsilastir nasil calisir:
1. Lokal DB'den tablo + kolon listesi cek (veya migration dosyalarindan)
2. Sunucu DB'den ayni bilgiyi cek (SSH + psql)
3. Fark raporu:
   - Lokal'de var, sunucuda yok → migration calistirilmamis
   - Sunucuda var, lokal'de yok → sunucuda manuel degisiklik yapilmis
   - Kolon tipi/nullable farki
4. Rapor goster, "Migration calistir?" sor

### Redis Yonet nasil calisir:
1. SSH → `redis-cli KEYS "pattern*"` ile key listele
2. `redis-cli TTL "key"` ile sure kontrol
3. `redis-cli GET "key"` ile deger goster
4. `redis-cli DEL "key"` ile sil (onay ile)
5. Yaygin pattern'ler: `giris_kilit:*`, `sms_bekleme:*`, `oturum:*`

---

### [Ops-3] Log & Hata

```json
{
  "questions": [{
    "question": "Log & Hata Izleme",
    "header": "Log",
    "multiSelect": false,
    "options": [
      {"label": "Canli Log", "description": "PM2 API/Web loglarini goster (son X satir veya X dakika)"},
      {"label": "Hata Takip", "description": "Son 24h hatalari grupla, tekrar sayisi, trend, dosya:satir"},
      {"label": "Nginx Log", "description": "Access ve error loglari goster, filtrele"},
      {"label": "Log Ara", "description": "Tum loglarda belirli kelime/pattern ara"}
    ]
  }]
}
```

---

### [Ops-4] Backup & Cron

```json
{
  "questions": [{
    "question": "Backup & Cron",
    "header": "Backup",
    "multiSelect": false,
    "options": [
      {"label": "DB Yedek Al", "description": "pg_dump ile veritabani yedegi al, boyutu goster"},
      {"label": "DB Geri Yukle", "description": "Mevcut yedeklerden sec ve geri yukle (ONAY GEREKIR)"},
      {"label": "Dosya Yedek", "description": "uploads/ dizinini tar.gz ile yedekle"},
      {"label": "Cron Yonet", "description": "Cron job listele, ekle, sil, son calisma zamanlari"}
    ]
  }]
}
```

### Cron Yonet nasil calisir:
1. SSH → `crontab -l` ile mevcut cron'lari listele
2. Her cron'un son calisma zamanini log'dan bul
3. Yeni cron ekle: kullaniciya zaman (gunluk/haftalik/ozel) ve komut sor
4. Cron sil: listele, kullanici secer, onay iste
5. Basarisiz cron tespiti: log'da hata olan cron'lari isaretle

---

### [Proje-1] Ortam & Ayar

```json
{
  "questions": [{
    "question": "Ortam & Framework Ayarlari",
    "header": "Ayar",
    "multiSelect": false,
    "options": [
      {"label": "Ortam Degistir", "description": ".env.development / .staging / .production arasi gecis yap"},
      {"label": "Memory Yonet", "description": "Memory dosyalari goruntule, duzenle, sil"},
      {"label": "Vault & Hook", "description": "Vault durumu, hook listele/duzenle, izin ayarlari"},
      {"label": "Framework Guncelle", "description": "Plugin versiyonunu guncelle, repo sync"}
    ]
  }]
}
```

### Ortam Degistir nasil calisir:
1. Mevcut .env dosyasini oku, hangi ortam oldugunu tespit et
2. Mevcut .env dosyalarini listele (.env.development, .env.staging, .env.production)
3. Kullanici hedef ortami secer
4. Mevcut .env'yi yedekle, secilen ortamin .env'sini kopyala
5. PM2 restart (gerekiyorsa)
6. UYARI: "Production .env'ye geciyorsun. Emin misin?"

---

### [Proje-2] Gorev & Rapor

```json
{
  "questions": [{
    "question": "Gorev, Rapor & Analiz",
    "header": "Gorev",
    "multiSelect": false,
    "options": [
      {"label": "Gorev Listesi", "description": "Proje bazli gorev ekle/duzenle/tamamla (kalici, conversation arasi)"},
      {"label": "Saglik Raporu", "description": "Haftalik 360 ozet: uptime, hata trend, disk, SSL, TODO, outdated"},
      {"label": "Bagimlilik Haritasi", "description": "Bu dosyayi degistirirsem ne etkilenir? Circular dependency bul"},
      {"label": "Snippet Kaydet", "description": "Sik kullanilan kod parcalarini kaydet ve tek komutla yapistir"}
    ]
  }]
}
```

### Gorev Listesi nasil calisir:
- `.claude/gorevler.md` dosyasinda kalici olarak tutulur
- Her gorev: baslik, oncelik (yuksek/orta/dusuk), durum, tarih
- Conversation'lar arasi kalici (memory degil, dosya bazli)
- Gorev ekle / duzenle / tamamla / sil islemleri
- Rapor: acik gorevler, tamamlanan, geciken

### Saglik Raporu nasil calisir:
1. API health + response time
2. PM2 uptime + restart sayisi
3. Disk kullanimi + trend
4. SSL kalan gun
5. npm outdated sayisi
6. Acik TODO/FIXME sayisi
7. Son 7 gun hata trendi
8. Tek sayfada formatli rapor

### Bagimlilik Haritasi nasil calisir:
1. Kullaniciya dosya sor
2. O dosyayi import eden tum dosyalari bul (grep)
3. O dosyalari import eden dosyalari bul (2. seviye)
4. Etki agaci goster
5. Circular dependency varsa uyar

### Snippet Kaydet nasil calisir:
- `.claude/snippets/` dizininde saklanir
- Her snippet: isim, aciklama, kod, dil
- Kaydet: kullanicidan isim + kod al
- Kullan: listele, sec, dosyaya yapistir
- Ornek: "auth-middleware", "pagination-helper", "form-validation"

---

### [Proje-3] Durum Kaydet

Alt menu yok, direkt calistir:
- `hafiza/durum.md` guncellenir (`scripts/hafiza/oturum.py bitir`)
- Nerede kalindi, ne yapildi, sirada ne var
- Git commit + push
- Opsiyonel: temizlik de yap (gecici dosyalar)

---

### [Proje-4] Proje Baslat

Alt menu yok, direkt calistir:
- Proje adi, tipi (web/mobil/api), stack sor
- Sablon kullanarak CLAUDE.md, faz plani, dizin yapisi olustur
- `~/.claude/sablonlar/` dizininden sablon kullan
- git init + ilk commit

---

## ARGUMAN ESLESTIRME (direkt kullanim)

| Arguman | Gidecegi Yer |
|---------|-------------|
| `web` / `site` / `test` | Web & Mobil Test |
| `api-test` / `endpoint` | API & Socket Test |
| `monitor` / `saglik` / `health` | Monitoring |
| `guvenlik` / `security` / `owasp` | Guvenlik |
| `iskele` / `scaffold` / `crud` | Kod Iskele |
| `lint` / `fix` / `kalite` / `faz` | Kod Kalitesi |
| `git` / `branch` / `pr` | Git & PR |
| `doc` / `changelog` / `api-doc` | Dokumantasyon |
| `deploy` / `diff` | Deploy & Diff |
| `db` / `migration` / `redis` | DB & Redis |
| `log` / `hata` / `error` | Log & Hata |
| `backup` / `yedek` / `cron` | Backup & Cron |
| `ortam` / `env` / `ayar` / `memory` | Ortam & Ayar |
| `gorev` / `rapor` / `snippet` | Gorev & Rapor |
| `durum` / `handoff` | Durum Kaydet |
| `proje` / `yeni` / `baslat` | Proje Baslat |

---

## GENEL KURALLAR

1. **AskUserQuestion ile secim al** - Her menude kullanicidan secim bekle
2. **Alt menu derinligi sinursiz** - Gerekirse 3. seviye menu ac
3. **Domain bilgisi CLAUDE.md'den okunur** - Hardcoded degil
4. **Test hesaplari vault'tan okunur** - Ekrana yazilmaz
5. **SSH bilgisi vault'tan okunur** - Hardcoded degil
6. **Varsayilan secim YAPMA** - Her zaman kullaniciya sor
7. **Screenshot her zaman al** - Tarayici testlerinde mutlaka goster
8. **Rapor formatli olsun** - Her islem sonunda kutulu rapor ver
9. **Tehlikeli islemler onay ister** - DB restore, rollback, silme, ortam degisiklik
10. **Sunucu islemleri proje dizininde kalir** - Diger sitelere DOKUNMA
