#!/usr/bin/env python3
"""Proje devralma - var olan bir projeyi tarar, öğrenir, çerçeveye uyarlar.

`tani.py` klasöre bakıp tanımın boş alanlarını doldurur; bu betik bir
adım öteye geçer ve projenin **tamamını** çıkarır:

    yapı          dizin haritası, giriş noktaları, katmanlar
    geçmiş        depo geçmişi, katkıcılar, en çok dokunulan dosyalar
    yarım iş      TODO/FIXME izleri, boş bırakılmış yerler
    risk          depoya girmiş sır, eksik .gitignore satırı
    kural uyumu   kimlik kuralına aykırı izler
    boşluk        çerçevenin beklediği hangi dosya yok

Çıkarılan her şey **tahmindir**. Bu betik hiçbir şeyi kendiliğinden
yazmaz; `uygula --onay` denmeden tek dosyaya dokunulmaz ve var olan
dosyanın üzerine hiçbir koşulda yazılmaz.

Sır değerleri rapora **yazılmaz**; yalnız dosya ve satır bildirilir.

Komutlar:
    tara      Derin envanter çıkar (hiçbir şey yazmaz)
    bosluk    Çerçeveye göre neyin eksik olduğunu göster
    plan      Envanterden uyarlama planı üret
    uygula    Plandaki üretimleri yaz (--onay şart)
    rapor     Son taramanın okunabilir raporu

Geliştirici: Enver KOCAK
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))

import proje  # noqa: E402
import tani  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

# Taramaya girmeyen dizinler - üretilmiş ya da dışarıdan gelmiş içerik
ATLANACAK_DIZINLER = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "bower_components",
    "dist", "build", "out", ".next", ".nuxt", ".output", ".parcel-cache",
    "__pycache__", ".venv", "venv", ".tox", ".mypy_cache", ".pytest_cache",
    ".idea", ".vscode", ".gradle", "Pods", ".terraform", "coverage",
    "target", "obj", "_arsiv", "_calisma", "gunluk", "storage",
}

# İçeriği okunacak uzantılar
METIN_UZANTILARI = {
    ".py", ".php", ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte",
    ".java", ".cs", ".go", ".rb", ".rs", ".kt", ".swift", ".dart",
    ".sql", ".sh", ".ps1", ".bat", ".yml", ".yaml", ".json", ".toml",
    ".ini", ".conf", ".env", ".md", ".txt", ".html", ".css", ".scss",
    ".xml", ".twig", ".blade", ".ejs", ".hbs",
}

# Kaynak sayılan uzantılar (satır sayımı bunlar üzerinden)
KAYNAK_UZANTILARI = {
    ".py", ".php", ".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte",
    ".java", ".cs", ".go", ".rb", ".rs", ".kt", ".swift", ".dart", ".sql",
}

ENCOK_DOSYA = 40000       # yürünecek azami dosya
ENCOK_ICERIK = 4000       # içeriği okunacak azami dosya
ENCOK_BOYUT = 400_000     # bir dosyadan okunacak azami karakter

# Dizin adından görev tahmini
DIZIN_ROLLERI = [
    (r"^(src|app|lib|kaynak|source)$", "kaynak"),
    (r"^(test|tests|spec|__tests__|testler)$", "test"),
    (r"^(doc|docs|documentation|belge|belgeler)$", "doküman"),
    (r"^(public|static|assets|varliklar|media|uploads|img|images)$", "varlık"),
    (r"^(config|conf|ayarlar|settings)$", "yapılandırma"),
    (r"^(migrations|db|database|veritabani|sql|seeds)$", "veri"),
    (r"^(scripts|bin|tools|betikler|araclar|utils)$", "betik"),
    (r"^(templates|views|resources|sablonlar|pages|components)$", "arayüz"),
    (r"^(routes|controllers|api|handlers)$", "yönlendirme"),
    (r"^(models|entities|domain|varliklar)$", "model"),
    (r"^\.github$", "otomasyon"),
]

# Giriş noktası adayları
GIRIS_ADAYLARI = [
    "index.php", "index.js", "index.ts", "index.html", "main.py", "app.py",
    "manage.py", "wsgi.py", "asgi.py", "server.js", "server.ts", "app.js",
    "app.ts", "bot.py", "main.go", "main.rs", "Program.cs", "artisan",
    "main.dart", "src/main.ts", "src/main.js", "src/main.py", "src/index.ts",
    "src/index.js", "src/App.vue", "src/App.tsx", "cmd/main.go",
    "public/index.php", "docker-compose.yml", "Makefile",
]

# Yarım iş izleri - yalnız büyük harfli işaret sayılır.
# "geçici", "bug report" gibi sıradan metin işaret değildir.
YARIM_DESENI = re.compile(r"(?<![A-Za-z_])(TODO|FIXME|HACK|XXX|BUG|YAPILACAK)(?![A-Za-z_])[:\s\-]")

# Sır izleri - eşleşen değer rapora yazılmaz, yalnız adı geçer
GIZLI_DESENLER = [
    ("özel anahtar bloğu", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("AWS erişim anahtarı", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Google API anahtarı", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Slack belirteci", re.compile(r"\bxox[abprs]-[0-9A-Za-z-]{10,}")),
    ("oturum belirteci", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.")),
    ("bağlantı dizesinde parola", re.compile(r"(?:mysql|postgres|postgresql|mongodb(?:\+srv)?|redis)://[^\s'\"]+:[^\s'\"]+@")),
    ("gömülü parola", re.compile(r"(?i)(?:password|passwd|sifre|parola|db_pass)\s*[:=]\s*['\"][^'\"]{6,}['\"]")),
    ("gömülü anahtar", re.compile(r"(?i)(?:api[_-]?key|secret[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]\s*['\"][A-Za-z0-9_\-/+]{16,}['\"]")),
]

# Yol ve değişken adı olarak geçenler ihlal değildir: `.claude/`, `CLAUDE.md`,
# `CLAUDE_PLUGIN_ROOT`, `claude plugin install` gibi kullanımlar kurulumun
# kendisidir. Muaf satır kimlik taramasına girmez.
KIMLIK_MUAF = re.compile(
    r"(?i)(\.claude|claude\.md|CLAUDE_[A-Z_]+|claude[-_]plugin|claude plugin|claude/)"
)

# Kimlik kuralına aykırı izler (kural 1-3)
KIMLIK_DESENLERI = [
    ("araç adı", re.compile(r"(?i)\b(claude|copilot|chatgpt|gemini|cursor\.ai)\b")),
    ("model adı", re.compile(r"(?i)\bgpt-?[0-9]|\bllm\b")),
    ("yapay zeka ifadesi", re.compile(r"(?i)yapay\s*zeka|\bAI\b|\bA\.I\.")),
    ("ortak yazar satırı", re.compile(r"(?i)co-authored-by:.*(claude|copilot|gpt|bot)")),
]

# .gitignore'da olması beklenen satırlar
BEKLENEN_YOKSAY = [".env", "_calisma/", "_arsiv/", "gunluk/"]

# Çerçevenin beklediği dosyalar.
# Yollar motorun gerçekten okuduğu yerlerdir: faz motoru hafiza/faz-plani.json,
# oturum katmanı hafiza/durum.md okur. Buraya başka yol yazılırsa üretilen
# dosya motora görünmez.
CERCEVE_DOSYALARI = [
    ("claude-md", "CLAUDE.md", "Projeye özgü kurallar", "yuksek"),
    ("proje-json", ".claude/proje.json", "Proje tanımı", "yuksek"),
    ("hafiza", "hafiza", "Durum, karar defteri, hata kütüphanesi", "yuksek"),
    ("faz-plani", "hafiza/faz-plani.json", "Faz planı", "orta"),
    ("tasarim-kimligi", ".claude/tasarim-kimligi.json", "Tasarım kimliği", "dusuk"),
    ("imza", ".claude/imza.json", "İmza ayarı", "dusuk"),
]


# ------------------------------------------------------------------ yardımcı

def _rapor_dizini(kok):
    yol = Path(kok) / "_calisma" / "devralma"
    yol.mkdir(parents=True, exist_ok=True)
    return yol


def _goreli(kok, yol):
    try:
        return str(Path(yol).relative_to(kok)).replace("\\", "/")
    except ValueError:
        return str(yol)


def _oku(yol, sinir=ENCOK_BOYUT):
    try:
        with open(yol, "r", encoding="utf-8", errors="ignore") as dosya:
            return dosya.read(sinir)
    except OSError:
        return ""


def _git(kok, *argumanlar, zaman_asimi=20):
    try:
        sonuc = subprocess.run(
            ["git", *argumanlar], cwd=str(kok), capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=zaman_asimi,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return sonuc.stdout.strip() if sonuc.returncode == 0 else ""


def yuru(kok):
    """Proje dosyalarını gez - üretilmiş dizinleri atlayarak."""
    kok = Path(kok)
    dosyalar = []
    yigin = [kok]

    while yigin and len(dosyalar) < ENCOK_DOSYA:
        dizin = yigin.pop()
        try:
            girdiler = list(dizin.iterdir())
        except OSError:
            continue

        for girdi in girdiler:
            if girdi.is_dir():
                if girdi.name in ATLANACAK_DIZINLER or girdi.is_symlink():
                    continue
                yigin.append(girdi)
            elif girdi.is_file():
                dosyalar.append(girdi)
                if len(dosyalar) >= ENCOK_DOSYA:
                    break

    return dosyalar


# ------------------------------------------------------------------ tarama

def yapi_cikar(kok, dosyalar):
    """Dizin haritası, boyut ve giriş noktaları."""
    kok = Path(kok)
    dizinler = {}
    uzantilar = {}
    kaynak_satir = 0
    buyukler = []

    for yol in dosyalar:
        goreli = _goreli(kok, yol)
        ust = goreli.split("/")[0] if "/" in goreli else "."
        dizinler[ust] = dizinler.get(ust, 0) + 1

        uzanti = yol.suffix.lower()
        if uzanti:
            uzantilar[uzanti] = uzantilar.get(uzanti, 0) + 1

        if uzanti in KAYNAK_UZANTILARI:
            try:
                boyut = yol.stat().st_size
            except OSError:
                continue
            if boyut > 2_000_000:
                continue
            satir = _oku(yol).count("\n") + 1
            kaynak_satir += satir
            buyukler.append({"dosya": goreli, "satir": satir})

    buyukler.sort(key=lambda kayit: kayit["satir"], reverse=True)

    harita = []
    for ad, sayi in sorted(dizinler.items(), key=lambda ikili: ikili[1], reverse=True):
        rol = ""
        for desen, etiket in DIZIN_ROLLERI:
            if re.match(desen, ad, re.IGNORECASE):
                rol = etiket
                break
        harita.append({"dizin": ad, "dosya": sayi, "rol": rol})

    girisler = [aday for aday in GIRIS_ADAYLARI if (kok / aday).is_file()]

    return {
        "dosya_sayisi": len(dosyalar),
        "kaynak_satir": kaynak_satir,
        "dizin_haritasi": harita[:25],
        "uzantilar": dict(sorted(uzantilar.items(), key=lambda i: i[1], reverse=True)[:12]),
        "en_buyuk_dosyalar": buyukler[:10],
        "giris_noktalari": girisler,
    }


def bagimlilik_cikar(kok):
    """Bağımlılık dosyalarından paket listesi."""
    kok = Path(kok)
    cikti = {}

    paket = kok / "package.json"
    if paket.is_file():
        try:
            veri = json.loads(_oku(paket) or "{}")
        except json.JSONDecodeError:
            veri = {}
        adlar = list(veri.get("dependencies", {})) + list(veri.get("devDependencies", {}))
        cikti["node"] = {"sayi": len(adlar), "baslica": adlar[:15],
                         "betikler": list(veri.get("scripts", {}))[:12]}

    besteci = kok / "composer.json"
    if besteci.is_file():
        try:
            veri = json.loads(_oku(besteci) or "{}")
        except json.JSONDecodeError:
            veri = {}
        adlar = list(veri.get("require", {})) + list(veri.get("require-dev", {}))
        cikti["php"] = {"sayi": len(adlar), "baslica": adlar[:15]}

    for ad in ("requirements.txt", "pyproject.toml"):
        yol = kok / ad
        if not yol.is_file():
            continue
        satirlar = [
            re.split(r"[=<>~!\[ ]", satir.strip())[0]
            for satir in _oku(yol).splitlines()
            if satir.strip() and not satir.strip().startswith("#")
        ]
        temiz = [satir for satir in satirlar if re.match(r"^[A-Za-z][A-Za-z0-9._-]*$", satir)]
        if temiz:
            cikti.setdefault("python", {"sayi": len(temiz), "baslica": temiz[:15]})

    return cikti


def gecmis_cikar(kok):
    """Depo geçmişi - kim, ne zaman, neye dokunmuş."""
    if not (Path(kok) / ".git").exists():
        return {"depo": False}

    sayi = _git(kok, "rev-list", "--count", "HEAD")
    ilk = _git(kok, "log", "--reverse", "--format=%cI", "--max-count=1")
    son = _git(kok, "log", "-1", "--format=%cI")
    dal = _git(kok, "rev-parse", "--abbrev-ref", "HEAD")
    uzak = _git(kok, "config", "--get", "remote.origin.url")

    katkicilar = []
    for satir in _git(kok, "shortlog", "-sne", "HEAD").splitlines()[:10]:
        parcalar = satir.strip().split("\t", 1)
        if len(parcalar) == 2:
            katkicilar.append({"katki": parcalar[0].strip(), "kisi": parcalar[1].strip()})

    sicak = {}
    for satir in _git(kok, "log", "--format=", "--name-only", "--max-count=400").splitlines():
        ad = satir.strip()
        if ad:
            sicak[ad] = sicak.get(ad, 0) + 1
    encok = sorted(sicak.items(), key=lambda ikili: ikili[1], reverse=True)[:10]

    son_isler = []
    for satir in _git(kok, "log", "--format=%cs|%s", "--max-count=15").splitlines():
        if "|" in satir:
            tarih, konu = satir.split("|", 1)
            son_isler.append({"tarih": tarih, "konu": konu[:110]})

    return {
        "depo": True,
        "dal": dal,
        "uzak_var": bool(uzak),
        "commit_sayisi": int(sayi) if sayi.isdigit() else 0,
        "ilk_tarih": ilk[:10],
        "son_tarih": son[:10],
        "katkicilar": katkicilar,
        "en_cok_degisen": [{"dosya": ad, "dokunma": adet} for ad, adet in encok],
        "son_isler": son_isler,
    }


def icerik_tara(kok, dosyalar):
    """Yarım iş, sır ve kimlik izlerini tek geçişte topla."""
    kok = Path(kok)
    yarim = []
    yarim_sayac = {}
    sirlar = []
    kimlik = []
    okunan = 0

    for yol in dosyalar:
        if okunan >= ENCOK_ICERIK:
            break
        if yol.suffix.lower() not in METIN_UZANTILARI and yol.name not in (".env", ".gitignore"):
            continue

        icerik = _oku(yol)
        if not icerik:
            continue
        okunan += 1
        goreli = _goreli(kok, yol)
        belge_mi = yol.suffix.lower() in (".md", ".txt")

        for numara, satir in enumerate(icerik.splitlines(), 1):
            if len(satir) > 1000:
                continue

            eslesme = YARIM_DESENI.search(satir)
            if eslesme:
                etiket = eslesme.group(1).upper()
                yarim_sayac[etiket] = yarim_sayac.get(etiket, 0) + 1
                if len(yarim) < 40:
                    yarim.append({"dosya": goreli, "satir": numara,
                                  "etiket": etiket, "metin": satir.strip()[:120]})

            for ad, desen in GIZLI_DESENLER:
                if desen.search(satir):
                    sirlar.append({"dosya": goreli, "satir": numara, "tur": ad})
                    break

            if not belge_mi and not KIMLIK_MUAF.search(satir):
                for ad, desen in KIMLIK_DESENLERI:
                    if desen.search(satir):
                        kimlik.append({"dosya": goreli, "satir": numara, "tur": ad})
                        break

    return {
        "yarim_isler": {"sayac": yarim_sayac, "ornekler": yarim},
        "sirlar": sirlar[:40],
        "sir_sayisi": len(sirlar),
        "kimlik_izleri": kimlik[:40],
        "kimlik_sayisi": len(kimlik),
        "okunan_dosya": okunan,
    }


def risk_cikar(kok, tarama):
    """Depoya girmiş sır, eksik yoksayma satırı."""
    kok = Path(kok)
    riskler = []

    yoksay_yolu = kok / ".gitignore"
    yoksay = _oku(yoksay_yolu) if yoksay_yolu.is_file() else ""

    if not yoksay_yolu.is_file():
        riskler.append({"seviye": "yuksek", "konu": ".gitignore yok",
                        "aciklama": "Hiçbir dosya yoksayılmıyor; sır dosyası kazara commit edilebilir."})
    else:
        eksikler = [satir for satir in BEKLENEN_YOKSAY if satir.rstrip("/") not in yoksay]
        if eksikler:
            riskler.append({"seviye": "orta", "konu": ".gitignore eksik satır",
                            "aciklama": "Beklenen satırlar yok: " + ", ".join(eksikler)})

    if (kok / ".git").exists():
        izlenen = _git(kok, "ls-files", "*.env", ".env", "*.pem", "*.key", "*credentials*")
        if izlenen:
            riskler.append({
                "seviye": "kritik", "konu": "Depoya girmiş sır dosyası",
                "aciklama": "Depo takibinde: " + ", ".join(izlenen.splitlines()[:8]),
            })

    if tarama["sir_sayisi"]:
        riskler.append({
            "seviye": "kritik", "konu": "Kodda gömülü sır",
            "aciklama": f"{tarama['sir_sayisi']} satırda anahtar/parola izi var (değerler rapora yazılmadı).",
        })

    if tarama["kimlik_sayisi"]:
        riskler.append({
            "seviye": "yuksek", "konu": "Kimlik kuralına aykırı iz",
            "aciklama": f"{tarama['kimlik_sayisi']} satırda araç/model adı geçiyor (kural 1-3).",
        })

    return riskler


def test_cikar(kok, dosyalar):
    """Test ve doküman durumu."""
    kok = Path(kok)
    test_dosyalari = [
        _goreli(kok, yol) for yol in dosyalar
        if re.search(r"(^|/)(test|tests|spec|__tests__|testler)(/|$)", _goreli(kok, yol), re.IGNORECASE)
        or re.match(r"^(test_|.*[._-]test\.|.*\.spec\.)", yol.name, re.IGNORECASE)
    ]

    belgeler = [
        ad for ad in ("README.md", "readme.md", "CHANGELOG.md", "DEGISIKLIKLER.md",
                      "LICENSE", "CONTRIBUTING.md", "docs", "belgeler")
        if (kok / ad).exists()
    ]

    return {
        "test_dosya_sayisi": len(test_dosyalari),
        "test_ornekleri": test_dosyalari[:8],
        "belgeler": belgeler,
        "surekli_entegrasyon": (kok / ".github" / "workflows").is_dir(),
    }


def cerceve_durumu(kok):
    """Çerçevenin beklediği dosyalardan hangisi var."""
    kok = Path(kok)
    durum = []
    for anahtar, goreli_yol, aciklama, oncelik in CERCEVE_DOSYALARI:
        durum.append({
            "anahtar": anahtar, "yol": goreli_yol, "aciklama": aciklama,
            "oncelik": oncelik, "var": (kok / goreli_yol).exists(),
        })
    return durum


def envanter_cikar(kok):
    """Bütün tarama katmanlarını tek envantere topla."""
    kok = Path(kok).resolve()
    dosyalar = yuru(kok)
    tarama = icerik_tara(kok, dosyalar)

    return {
        "ad": kok.name,
        "yol": str(kok),
        "tarandi": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "teknolojiler": tani.teknolojileri_bul(kok),
        "aciklama": tani.aciklama_bul(kok),
        "yapi": yapi_cikar(kok, dosyalar),
        "bagimliliklar": bagimlilik_cikar(kok),
        "gecmis": gecmis_cikar(kok),
        "yarim_isler": tarama["yarim_isler"],
        "sirlar": tarama["sirlar"],
        "kimlik_izleri": tarama["kimlik_izleri"],
        "riskler": risk_cikar(kok, tarama),
        "olgunluk": test_cikar(kok, dosyalar),
        "cerceve": cerceve_durumu(kok),
        "okunan_dosya": tarama["okunan_dosya"],
    }


# ------------------------------------------------------------------ plan

def plan_uret(envanter):
    """Envanterden uyarlama planı - ne üretilecek, ne elle düzeltilecek."""
    isler = []

    for kayit in envanter["cerceve"]:
        if kayit["var"]:
            continue
        isler.append({
            "anahtar": kayit["anahtar"],
            "baslik": f"{kayit['yol']} üret",
            "aciklama": kayit["aciklama"],
            "oncelik": kayit["oncelik"],
            "eylem": "uret" if kayit["anahtar"] in URETILEBILIR else "elle",
            "hedef": kayit["yol"],
        })

    for risk in envanter["riskler"]:
        isler.append({
            "anahtar": "risk",
            "baslik": risk["konu"],
            "aciklama": risk["aciklama"],
            "oncelik": "kritik" if risk["seviye"] == "kritik" else risk["seviye"],
            "eylem": "gitignore" if ".gitignore" in risk["konu"] else "elle",
            "hedef": ".gitignore" if ".gitignore" in risk["konu"] else "-",
        })

    if not envanter["olgunluk"]["test_dosya_sayisi"]:
        isler.append({
            "anahtar": "test", "baslik": "Test yok",
            "aciklama": "Projede test dosyası bulunamadı; faz kapılarına test şartı konmalı.",
            "oncelik": "orta", "eylem": "elle", "hedef": "-",
        })

    toplam_yarim = sum(envanter["yarim_isler"]["sayac"].values())
    if toplam_yarim:
        isler.append({
            "anahtar": "yarim", "baslik": f"{toplam_yarim} yarım iş izi",
            "aciklama": "TODO/FIXME izleri faz planına dökülmeli.",
            "oncelik": "orta", "eylem": "elle", "hedef": ".claude/faz-plani.md",
        })

    sira = {"kritik": 0, "yuksek": 1, "orta": 2, "dusuk": 3}
    isler.sort(key=lambda kayit: sira.get(kayit["oncelik"], 9))
    return isler


URETILEBILIR = {"claude-md", "proje-json", "faz-plani", "hafiza"}


# ------------------------------------------------------------------ üretim

def claude_md_uret(envanter):
    """Envanterden projeye özgü kural dosyası taslağı."""
    yapi = envanter["yapi"]
    teknoloji = ", ".join(envanter["teknolojiler"]) or "belirlenemedi"

    satirlar = [
        f"# {envanter['ad']}",
        "",
        "> Bu dosya devralma taramasıyla üretildi. Yanlış olan satırı düzelt,",
        "> doğru olanı olduğu gibi bırak. Global kurallar ayrıca geçerlidir;",
        "> burada yalnız **bu projeye özgü** olanlar yazar.",
        "",
        "## Ne yapar",
        "",
        envanter["aciklama"] or "<tek cümleyle yaz>",
        "",
        "## Teknik",
        "",
        f"- **Yığın:** {teknoloji}",
    ]

    if yapi["giris_noktalari"]:
        satirlar.append(f"- **Giriş noktası:** {', '.join(yapi['giris_noktalari'][:4])}")
    satirlar.append(f"- **Büyüklük:** {yapi['dosya_sayisi']} dosya, {yapi['kaynak_satir']} kaynak satırı")

    betikler = envanter["bagimliliklar"].get("node", {}).get("betikler")
    if betikler:
        satirlar.append(f"- **Betikler:** {', '.join(betikler[:8])}")

    satirlar += ["", "## Dizin düzeni", ""]
    for kayit in yapi["dizin_haritasi"][:12]:
        if kayit["dizin"] == ".":
            continue
        rol = f" - {kayit['rol']}" if kayit["rol"] else ""
        satirlar.append(f"- `{kayit['dizin']}/` ({kayit['dosya']} dosya){rol}")

    satirlar += [
        "",
        "## Bu projede dikkat",
        "",
        "<taramada çıkan kurallar buraya - dokunulmaması gereken yerler,",
        "kurulu desenler, müşteriye özel şartlar>",
        "",
        "## Durum",
        "",
    ]

    gecmis = envanter["gecmis"]
    if gecmis.get("depo"):
        satirlar.append(
            f"- Depo: {gecmis['commit_sayisi']} kayıt, "
            f"{gecmis['ilk_tarih']} - {gecmis['son_tarih']}, dal `{gecmis['dal']}`"
        )
    yarim = sum(envanter["yarim_isler"]["sayac"].values())
    if yarim:
        satirlar.append(f"- Kodda {yarim} yarım iş izi var (`/proje-devral` raporuna bak)")
    if not envanter["olgunluk"]["test_dosya_sayisi"]:
        satirlar.append("- Test yok")

    satirlar += ["", "---", "", "Geliştirici: Enver KOCAK | enverkocak.com | mail@enverkocak.com", ""]
    return "\n".join(satirlar)


def faz_plani_uret(envanter):
    """Yarım işlerden ve boşluklardan ilk faz planı.

    Faz motorunun okuduğu biçimde üretilir (hafiza/faz-plani.json).
    Kapı komutu boş bırakılır; devralmayı yürüten kişi doldurur, çünkü
    her projenin kapısı kendi test komutudur.
    """
    fazlar = [{
        "no": 1,
        "ad": "Devralma",
        "aciklama": "Taramadan çıkan tanım doğrulanır.",
        "kapi_komutu": "",
        "maddeler": [
            "CLAUDE.md gözden geçirildi, yanlış satırlar düzeltildi",
            "Proje tanımı (.claude/proje.json) doğrulandı",
            "Devralma raporu okundu",
        ],
        "durum": "bekliyor",
    }]

    kritikler = [risk for risk in envanter["riskler"] if risk["seviye"] in ("kritik", "yuksek")]
    if kritikler:
        fazlar.append({
            "no": len(fazlar) + 1,
            "ad": "Risk kapatma",
            "aciklama": "Taramada çıkan sır ve kural riskleri kapatılır.",
            "kapi_komutu": "",
            "maddeler": [f"{risk['konu']}: {risk['aciklama']}" for risk in kritikler],
            "durum": "bekliyor",
        })

    sayac = envanter["yarim_isler"]["sayac"]
    if sayac:
        ozet = ", ".join(f"{etiket} {adet}" for etiket, adet in sorted(sayac.items()))
        maddeler = [
            f"{kayit['dosya']}:{kayit['satir']} {kayit['metin']}"
            for kayit in envanter["yarim_isler"]["ornekler"][:15]
        ]
        fazlar.append({
            "no": len(fazlar) + 1,
            "ad": "Yarım işler",
            "aciklama": f"Kodda bırakılmış izler: {ozet}",
            "kapi_komutu": "",
            "maddeler": maddeler,
            "durum": "bekliyor",
        })

    if not envanter["olgunluk"]["test_dosya_sayisi"]:
        fazlar.append({
            "no": len(fazlar) + 1,
            "ad": "Test tabanı",
            "aciklama": "Projede test yok; kritik akış için ilk testler yazılır.",
            "kapi_komutu": "",
            "maddeler": ["Kritik akış için ilk testler yazıldı"],
            "durum": "bekliyor",
        })

    return {"fazlar": fazlar}


def durum_uret(envanter):
    gecmis = envanter["gecmis"]
    return "\n".join([
        f"# {envanter['ad']} - Durum",
        "",
        f"## {envanter['tarandi']} - devralma",
        "",
        "### Yapılan iş",
        "",
        "- Proje tarandı ve çerçeveye bağlandı",
        "",
        "### Nerede kaldık",
        "",
        f"Proje devralındı. {gecmis.get('commit_sayisi', 0)} kayıtlık geçmiş,"
        f" son çalışma {gecmis.get('son_tarih') or 'bilinmiyor'}.",
        "Devralma raporu: `_calisma/devralma/rapor.md`",
        "",
        "### Sırada ne var",
        "",
        "Faz 1 - CLAUDE.md ve proje tanımı doğrulanacak.",
        "",
    ])


def hafiza_uret(kok, envanter):
    """Hafıza iskeleti - karar defteri ve hata kütüphanesi."""
    dizin = Path(kok) / "hafiza"
    dizin.mkdir(parents=True, exist_ok=True)
    yazilan = []

    dosyalar = {
        "kararlar.md": f"# {envanter['ad']} - Kararlar\n\n"
                       f"## {envanter['tarandi']}\n\n"
                       "- Proje çerçeveye devralındı\n",
        "hatalar.md": f"# {envanter['ad']} - Hata Kütüphanesi\n\n"
                      "Çözülen her hata buraya yazılır: belirti, sebep, çözüm.\n",
        "durum.md": durum_uret(envanter),
    }

    for ad, icerik in dosyalar.items():
        yol = dizin / ad
        if yol.exists():
            continue
        yol.write_text(icerik, encoding="utf-8")
        yazilan.append(_goreli(kok, yol))

    return yazilan


def gitignore_tamamla(kok):
    """Eksik yoksayma satırlarını ekler - var olan satıra dokunmaz."""
    yol = Path(kok) / ".gitignore"
    mevcut = _oku(yol) if yol.is_file() else ""
    eksikler = [satir for satir in BEKLENEN_YOKSAY if satir.rstrip("/") not in mevcut]

    if not eksikler:
        return []

    ek = "\n# Çerçeve\n" + "\n".join(eksikler) + "\n"
    with open(yol, "a", encoding="utf-8") as dosya:
        if mevcut and not mevcut.endswith("\n"):
            dosya.write("\n")
        dosya.write(ek)

    return eksikler


# ------------------------------------------------------------------ rapor

def rapor_metni(envanter, isler):
    yapi = envanter["yapi"]
    gecmis = envanter["gecmis"]
    satirlar = [
        f"# Devralma raporu - {envanter['ad']}",
        "",
        f"Tarama: {envanter['tarandi']}  ",
        f"Yol: `{envanter['yol']}`",
        "",
        "## Özet",
        "",
        f"- **Yığın:** {', '.join(envanter['teknolojiler']) or 'belirlenemedi'}",
        f"- **Büyüklük:** {yapi['dosya_sayisi']} dosya, {yapi['kaynak_satir']} kaynak satırı",
        f"- **Giriş noktası:** {', '.join(yapi['giris_noktalari'][:5]) or 'bulunamadı'}",
        f"- **Test:** {envanter['olgunluk']['test_dosya_sayisi']} dosya",
        f"- **Belge:** {', '.join(envanter['olgunluk']['belgeler']) or 'yok'}",
    ]

    if gecmis.get("depo"):
        satirlar.append(
            f"- **Geçmiş:** {gecmis['commit_sayisi']} kayıt, "
            f"{gecmis['ilk_tarih']} - {gecmis['son_tarih']}, "
            f"{len(gecmis['katkicilar'])} katkıcı"
        )
    else:
        satirlar.append("- **Geçmiş:** depo yok")

    satirlar += ["", "## Dizin düzeni", "", "| Dizin | Dosya | Rol |", "|---|---|---|"]
    for kayit in yapi["dizin_haritasi"][:15]:
        satirlar.append(f"| `{kayit['dizin']}` | {kayit['dosya']} | {kayit['rol'] or '-'} |")

    if gecmis.get("en_cok_degisen"):
        satirlar += ["", "## En çok dokunulan dosyalar", ""]
        for kayit in gecmis["en_cok_degisen"][:8]:
            satirlar.append(f"- `{kayit['dosya']}` ({kayit['dokunma']} kayıt)")

    if envanter["riskler"]:
        satirlar += ["", "## Riskler", ""]
        for risk in envanter["riskler"]:
            satirlar.append(f"- **{risk['seviye'].upper()}** {risk['konu']} - {risk['aciklama']}")

    if envanter["sirlar"]:
        satirlar += ["", "## Sır izleri", "", "Değerler yazılmadı; yalnız yer bildirildi.", ""]
        for kayit in envanter["sirlar"][:15]:
            satirlar.append(f"- `{kayit['dosya']}:{kayit['satir']}` - {kayit['tur']}")

    if envanter["kimlik_izleri"]:
        satirlar += ["", "## Kimlik kuralına aykırı izler", ""]
        for kayit in envanter["kimlik_izleri"][:15]:
            satirlar.append(f"- `{kayit['dosya']}:{kayit['satir']}` - {kayit['tur']}")

    sayac = envanter["yarim_isler"]["sayac"]
    if sayac:
        ozet = ", ".join(f"{etiket} {adet}" for etiket, adet in sorted(sayac.items()))
        satirlar += ["", f"## Yarım işler ({ozet})", ""]
        for kayit in envanter["yarim_isler"]["ornekler"][:15]:
            satirlar.append(f"- `{kayit['dosya']}:{kayit['satir']}` {kayit['metin']}")

    satirlar += ["", "## Uyarlama planı", "", "| Öncelik | İş | Eylem | Hedef |", "|---|---|---|---|"]
    for is_kaydi in isler:
        satirlar.append(
            f"| {is_kaydi['oncelik']} | {is_kaydi['baslik']} | {is_kaydi['eylem']} | `{is_kaydi['hedef']}` |"
        )

    satirlar += [
        "",
        "---",
        "",
        "Üretilenler tahmindir. Yazmadan önce `plan` çıktısını oku,",
        "sonra `uygula --onay` de.",
        "",
    ]
    return "\n".join(satirlar)


# ------------------------------------------------------------------ komutlar

def _kok_bul(args):
    return Path(args.yol).resolve() if args.yol else Path(yollar.proje_kok()).resolve()


def _envanter_yukle(kok):
    yol = _rapor_dizini(kok) / "envanter.json"
    if not yol.is_file():
        return None
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def komut_tara(args):
    kok = _kok_bul(args)
    if not kok.is_dir():
        print(f"Klasör yok: {kok}")
        return 1

    print(f"Taranıyor: {kok}")
    envanter = envanter_cikar(kok)
    isler = plan_uret(envanter)

    dizin = _rapor_dizini(kok)
    (dizin / "envanter.json").write_text(
        json.dumps(envanter, ensure_ascii=False, indent=2), encoding="utf-8")
    (dizin / "rapor.md").write_text(rapor_metni(envanter, isler), encoding="utf-8")

    yapi = envanter["yapi"]
    print()
    print(f"  Yığın        {', '.join(envanter['teknolojiler']) or 'belirlenemedi'}")
    print(f"  Büyüklük     {yapi['dosya_sayisi']} dosya / {yapi['kaynak_satir']} satır")
    print(f"  Okunan       {envanter['okunan_dosya']} dosya")
    print(f"  Risk         {len(envanter['riskler'])}")
    print(f"  Yarım iş     {sum(envanter['yarim_isler']['sayac'].values())}")
    print(f"  Eksik dosya  {sum(1 for k in envanter['cerceve'] if not k['var'])}")
    print()
    print(f"Rapor: {_goreli(kok, dizin / 'rapor.md')}")
    return 0


def komut_bosluk(args):
    kok = _kok_bul(args)
    for kayit in cerceve_durumu(kok):
        isaret = "var" if kayit["var"] else "YOK"
        print(f"  [{isaret:3}] {kayit['yol']:32} {kayit['aciklama']}")
    return 0


def komut_plan(args):
    kok = _kok_bul(args)
    envanter = _envanter_yukle(kok)
    if envanter is None:
        print("Önce tarama gerekli: devral.py tara")
        return 1

    isler = plan_uret(envanter)
    if not isler:
        print("Yapılacak bir şey yok; proje çerçeveye uygun.")
        return 0

    print(f"{envanter['ad']} - uyarlama planı\n")
    for is_kaydi in isler:
        print(f"  [{is_kaydi['oncelik']:7}] {is_kaydi['baslik']}")
        print(f"            {is_kaydi['aciklama']}")
        print(f"            eylem: {is_kaydi['eylem']}  hedef: {is_kaydi['hedef']}")
        print()

    uretilecek = [kayit for kayit in isler if kayit["eylem"] in ("uret", "gitignore")]
    print(f"{len(uretilecek)} iş üretilebilir, {len(isler) - len(uretilecek)} iş elle çözülecek.")
    print("Üretmek için: devral.py uygula --onay")
    return 0


def komut_uygula(args):
    kok = _kok_bul(args)
    envanter = _envanter_yukle(kok)
    if envanter is None:
        print("Önce tarama gerekli: devral.py tara")
        return 1

    if not args.onay:
        print("Dosya yazılacak. Onay verilmedi, hiçbir şey yapılmadı.")
        print("Yazmak için: devral.py uygula --onay")
        return 1

    yazilan = []
    atlanan = []

    uretimler = {
        "claude-md": ("CLAUDE.md", lambda: claude_md_uret(envanter)),
        "faz-plani": (
            "hafiza/faz-plani.json",
            lambda: json.dumps(faz_plani_uret(envanter), ensure_ascii=False, indent=2) + "\n",
        ),
    }

    istenen = set(args.yalniz.split(",")) if args.yalniz else None

    for anahtar, (goreli_yol, uretici) in uretimler.items():
        if istenen and anahtar not in istenen:
            continue
        hedef = kok / goreli_yol
        if hedef.exists():
            atlanan.append(goreli_yol)
            continue
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(uretici(), encoding="utf-8")
        yazilan.append(goreli_yol)

    if not istenen or "proje-json" in istenen:
        if not (kok / ".claude" / "proje.json").exists():
            tahmin = tani.tani(kok)
            tanim, _ = tani.birlestir(None, tahmin)
            proje.yaz(tanim, kok)
            yazilan.append(".claude/proje.json")
        else:
            atlanan.append(".claude/proje.json")

    if not istenen or "hafiza" in istenen:
        yazilan += hafiza_uret(kok, envanter)

    if not istenen or "gitignore" in istenen:
        eklenen = gitignore_tamamla(kok)
        if eklenen:
            yazilan.append(f".gitignore (+{len(eklenen)} satır)")

    print(f"{len(yazilan)} dosya yazıldı:")
    for ad in yazilan:
        print(f"  + {ad}")

    if atlanan:
        print(f"\n{len(atlanan)} dosya zaten vardı, dokunulmadı:")
        for ad in atlanan:
            print(f"  = {ad}")

    print("\nÜretilenler taslaktır. Okumadan doğru sayma.")
    return 0


def komut_rapor(args):
    kok = _kok_bul(args)
    yol = _rapor_dizini(kok) / "rapor.md"
    if not yol.is_file():
        print("Rapor yok. Önce: devral.py tara")
        return 1
    print(yol.read_text(encoding="utf-8"))
    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Proje devralma")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("tara", help="Derin envanter çıkar")
    p.add_argument("--yol")
    p.set_defaults(islev=komut_tara)

    p = alt.add_parser("bosluk", help="Eksik çerçeve dosyaları")
    p.add_argument("--yol")
    p.set_defaults(islev=komut_bosluk)

    p = alt.add_parser("plan", help="Uyarlama planı")
    p.add_argument("--yol")
    p.set_defaults(islev=komut_plan)

    p = alt.add_parser("uygula", help="Planı yaz")
    p.add_argument("--yol")
    p.add_argument("--onay", action="store_true", help="Yazma onayı")
    p.add_argument("--yalniz", help="Yalnız bu üretimler (virgülle)")
    p.set_defaults(islev=komut_uygula)

    p = alt.add_parser("rapor", help="Son raporu göster")
    p.add_argument("--yol")
    p.set_defaults(islev=komut_rapor)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
