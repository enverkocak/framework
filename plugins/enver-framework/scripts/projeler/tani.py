#!/usr/bin/env python3
"""Proje tanıma - klasöre bakıp tanımı kendi doldurur.

Yirmi üç projenin tanımını elle yazmak yerine, klasördeki izlerden
çıkarılabilecek ne varsa çıkarılır:

    teknolojiler   hangi dosyalar var (package.json, composer.json, *.php ...)
    açıklama       README'nin ilk anlamlı satırı
    alan_adı       depo adresinden ya da yapılandırma dosyalarından
    durum          son değişiklik tarihine göre tahmin
    servisler      tanınan yapı taşları (site, API, bot, masaüstü ...)

Çıkarılan bilgi **tahmindir**, işaretlenir. Enver düzeltir ya da onaylar.
Elle yazılmış alanların üzerine yazılmaz.

Komutlar:
    bu        Bu projeyi tanı
    hepsi     Kayıtlı bütün projeleri tanı

Geliştirici: Enver KOCAK
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))

import kayit  # noqa: E402
import proje  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

# Dosya izinden teknoloji çıkarımı
TEKNOLOJI_IZLERI = [
    ("package.json", "Node.js"),
    ("composer.json", "PHP"),
    ("requirements.txt", "Python"),
    ("pyproject.toml", "Python"),
    ("Gemfile", "Ruby"),
    ("go.mod", "Go"),
    ("pom.xml", "Java"),
    ("Cargo.toml", "Rust"),
    ("wp-config.php", "WordPress"),
    ("artisan", "Laravel"),
    ("manage.py", "Django"),
    ("next.config.js", "Next.js"),
    ("nuxt.config.js", "Nuxt"),
    ("angular.json", "Angular"),
    ("docker-compose.yml", "Docker"),
    ("Dockerfile", "Docker"),
    ("pubspec.yaml", "Flutter"),
    ("build.gradle", "Android"),
    ("*.sln", ".NET"),
    ("*.csproj", ".NET"),
]

# Bağımlılık adından çerçeve çıkarımı
BAGIMLILIK_IZLERI = {
    "react": "React", "vue": "Vue", "svelte": "Svelte",
    "express": "Express", "fastify": "Fastify", "nestjs": "NestJS",
    "laravel/framework": "Laravel", "symfony/": "Symfony",
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI",
    "telegraf": "Telegram Bot", "python-telegram-bot": "Telegram Bot",
    "electron": "Electron", "tauri": "Tauri",
    "selenium": "Selenium", "playwright": "Playwright",
    "pandas": "Pandas", "openpyxl": "Excel",
}

# Klasör adından görev tahmini
AD_IPUCLARI = [
    (r"bot\b", "bot", "Otomasyon botu"),
    (r"api\b", "api", "API servisi"),
    (r"panel", "panel", "Yönetim paneli"),
    (r"site|web|www", "site", "Web sitesi"),
    (r"masaustu|desktop", "masaustu", "Masaüstü uygulaması"),
    (r"mobil|mobile|app", "mobil", "Mobil uygulama"),
    (r"pos\b|odeme|payment", "odeme", "Ödeme entegrasyonu"),
    (r"muhasebe|hesap", "muhasebe", "Muhasebe uygulaması"),
    (r"export|import|xml", "aktarim", "Veri aktarımı"),
    (r"kurulum|setup", "kurulum", "Kurulum aracı"),
    (r"haber|news", "icerik", "İçerik toplama"),
    (r"album|galeri|foto", "medya", "Medya uygulaması"),
]


def _dosya_var(kok, desen):
    if "*" in desen:
        return any(kok.glob(desen))
    return (kok / desen).exists()


def teknolojileri_bul(kok):
    bulunanlar = []

    for desen, ad in TEKNOLOJI_IZLERI:
        if _dosya_var(kok, desen) and ad not in bulunanlar:
            bulunanlar.append(ad)

    # Bağımlılık dosyalarının içine bak
    for dosya in ("package.json", "composer.json", "requirements.txt", "pyproject.toml"):
        yol = kok / dosya
        if not yol.is_file():
            continue
        try:
            icerik = yol.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        for anahtar, ad in BAGIMLILIK_IZLERI.items():
            if anahtar in icerik and ad not in bulunanlar:
                bulunanlar.append(ad)

    # Baskın kaynak dosya uzantısı
    if not bulunanlar:
        sayac = {}
        try:
            for yol in list(kok.rglob("*"))[:1500]:
                if yol.is_file() and yol.suffix.lower() in (".py", ".php", ".js", ".ts", ".cs", ".java"):
                    sayac[yol.suffix.lower()] = sayac.get(yol.suffix.lower(), 0) + 1
        except OSError:
            pass
        if sayac:
            baskin = max(sayac, key=sayac.get)
            bulunanlar.append({".py": "Python", ".php": "PHP", ".js": "JavaScript",
                               ".ts": "TypeScript", ".cs": "C#", ".java": "Java"}[baskin])

    return bulunanlar


def aciklama_bul(kok):
    for ad in ("README.md", "readme.md", "README.txt", "OKUBENI.md"):
        yol = kok / ad
        if not yol.is_file():
            continue
        try:
            icerik = yol.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for satir in icerik.splitlines():
            temiz = satir.strip().lstrip("#").strip()
            if temiz and len(temiz) > 8 and not temiz.startswith(("!", "[", "|", "`", "<")):
                return temiz[:160]
    return ""


def alan_adi_bul(kok, ad):
    """Klasör adı alan adı gibi duruyorsa ya da yapılandırmada geçiyorsa çıkar."""
    if re.match(r"^[a-z0-9-]+-(com|net|org|gen-tr|com-tr)$", ad):
        parcalar = ad.rsplit("-", 1)
        uzanti = parcalar[1].replace("-", ".")
        return f"{parcalar[0]}.{uzanti}"

    for dosya in ("wp-config.php", ".env", "config.php"):
        yol = kok / dosya
        if not yol.is_file():
            continue
        try:
            icerik = yol.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        eslesme = re.search(r"https?://([a-z0-9.-]+\.[a-z]{2,})", icerik, re.IGNORECASE)
        if eslesme:
            return eslesme.group(1)

    return None


def son_degisiklik(kok):
    """Depo geçmişinden son çalışma tarihi."""
    try:
        sonuc = subprocess.run(
            ["git", "log", "-1", "--format=%cI"],
            cwd=str(kok), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    if sonuc.returncode != 0 or not sonuc.stdout.strip():
        return None

    try:
        return datetime.fromisoformat(sonuc.stdout.strip()).replace(tzinfo=None)
    except ValueError:
        return None


def durum_tahmin(kok):
    """Son değişikliğe göre durum tahmini."""
    tarih = son_degisiklik(kok)
    if tarih is None:
        return "beklemede", None

    gecen = datetime.now() - tarih

    if gecen < timedelta(days=14):
        return "gelistirmede", tarih
    if gecen < timedelta(days=120):
        return "yarim", tarih
    return "beklemede", tarih


def servis_tahmin(kok, ad, teknolojiler):
    """Klasör adından ve teknolojiden yapı taşı tahmini."""
    kucuk = ad.lower()

    for desen, tur, gorev in AD_IPUCLARI:
        if re.search(desen, kucuk):
            return [{"ad": ad, "tur": tur, "gorev": gorev, "tahmin": True}]

    if "WordPress" in teknolojiler:
        return [{"ad": ad, "tur": "site", "gorev": "İçerik yönetim sistemi", "tahmin": True}]

    return []


def tani(kok, mevcut=None):
    """Klasörden çıkarılabilecek her şeyi çıkar."""
    kok = Path(kok)
    ad = kok.name

    teknolojiler = teknolojileri_bul(kok)
    durum, tarih = durum_tahmin(kok)

    tahmin = {
        "ad": ad,
        "aciklama": aciklama_bul(kok),
        "teknolojiler": teknolojiler,
        "durum": durum,
        "alan_adi": alan_adi_bul(kok, ad),
        "servisler": servis_tahmin(kok, ad, teknolojiler),
        "yerel_yol": str(kok),
    }

    if tarih:
        tahmin["tarihler"] = {"son_calisma": tarih.strftime("%Y-%m-%d")}

    # Görev alanı boşsa açıklamadan türet
    if tahmin["aciklama"]:
        tahmin["gorev"] = tahmin["aciklama"][:100]
    else:
        for desen, _, gorev in AD_IPUCLARI:
            if re.search(desen, ad.lower()):
                tahmin["gorev"] = gorev
                break

    return {anahtar: deger for anahtar, deger in tahmin.items() if deger}


def birlestir(mevcut, tahmin):
    """Elle yazılmış alanların üzerine yazma; yalnız boşları doldur."""
    sonuc = dict(mevcut) if mevcut else dict(proje.SABLON)
    doldurulan = []

    for anahtar, deger in tahmin.items():
        eski = sonuc.get(anahtar)

        bos_mu = eski in (None, "", [], {}) or (
            anahtar == "durum" and eski == proje.SABLON["durum"]
        )

        if bos_mu:
            sonuc[anahtar] = deger
            doldurulan.append(anahtar)

    if doldurulan:
        sonuc["_tahmin_edilen_alanlar"] = doldurulan
        sonuc["_tahmin_notu"] = (
            "Bu alanlar klasör içeriğinden tahmin edildi. Yanlışsa düzelt, "
            "doğruysa bu notu silebilirsin."
        )

    return sonuc, doldurulan


# ---------------------------------------------------------------- komutlar

def komut_bu(args):
    kok = Path(args.yol) if args.yol else Path(yollar.proje_kok())

    mevcut = proje.oku(kok)
    tahmin = tani(kok, mevcut)
    yeni, doldurulan = birlestir(mevcut, tahmin)

    if not doldurulan:
        print(f"{kok.name}: doldurulacak boş alan yok.")
        return 0

    if args.deneme:
        print(f"{kok.name} - tahmin edilenler:")
        for anahtar in doldurulan:
            print(f"  {anahtar}: {tahmin[anahtar]}")
        return 0

    proje.yaz(yeni, kok)
    print(f"{kok.name}: {len(doldurulan)} alan dolduruldu ({', '.join(doldurulan)})")
    return 0


def komut_hepsi(args):
    veri = kayit.kayit_oku()
    projeler = veri.get("projeler", {})

    if not projeler:
        print("Kayıtlı proje yok. Önce: python kayit.py tara")
        return 1

    islenen = 0
    atlanan = 0

    for ad, kayit_bilgisi in sorted(projeler.items()):
        kok = Path(kayit_bilgisi.get("yol", ""))
        if not kok.is_dir():
            atlanan += 1
            continue

        mevcut = proje.oku(kok)
        tahmin = tani(kok, mevcut)
        yeni, doldurulan = birlestir(mevcut, tahmin)

        if not doldurulan:
            continue

        if not args.deneme:
            proje.yaz(yeni, kok)

        islenen += 1
        durum = proje.DURUM_ETIKETLERI.get(yeni.get("durum"), yeni.get("durum"))
        teknoloji = ", ".join(yeni.get("teknolojiler", [])[:3]) or "-"
        print(f"  {ad:34} {durum:14} {teknoloji}")

    print()
    if args.deneme:
        print(f"{islenen} projede doldurulacak alan var (deneme, yazılmadı).")
    else:
        print(f"{islenen} projenin tanımı dolduruldu.")

    if atlanan:
        print(f"{atlanan} proje klasörü bulunamadı.")

    print()
    print("Tahmin edilen alanlar tanımda işaretli. Yanlış olanları düzelt.")
    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Proje tanıma")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("bu", help="Bu projeyi tanı")
    p.add_argument("--yol")
    p.add_argument("--deneme", action="store_true", help="Yazma, sadece göster")
    p.set_defaults(islev=komut_bu)

    p = alt.add_parser("hepsi", help="Bütün projeleri tanı")
    p.add_argument("--deneme", action="store_true", help="Yazma, sadece göster")
    p.set_defaults(islev=komut_hepsi)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
