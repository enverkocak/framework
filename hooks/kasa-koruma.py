#!/usr/bin/env python3
"""PreToolUse kancasi: Kasa ve sir korumasi.

Iki kural zorlanir:

  1. KASA ERISIMI (E1)
     Kasa dosyalari dogrudan okunamaz. Icerik yalniz kasa betigi uzerinden,
     parola verilmis bir oturumda alinir.

  2. SIR SIZINTISI (T12)
     Anahtar, parola ve ozel anahtar iceren metnin dosyaya yazilmasi engellenir.
     Sirlar kasada durur, kaynak kodda degil.

Gelistirici: Enver KOCAK
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _ortak_yol as ortak_yol  # noqa: E402

BETIKLER_HAZIR = ortak_yol.hazirla()

if BETIKLER_HAZIR:
    import gerekce
else:
    gerekce = None


# --- Kasa dosyalari: dogrudan okunamaz -------------------------------------

KASA_YOL_DESENLERI = [
    re.compile(r"\bkasa\.kilit\b", re.IGNORECASE),
    re.compile(r"\bkasa-oturum\.json\b", re.IGNORECASE),
    # vault/ yolu satir basinda, bosluktan veya tirnaktan sonra da gelebilir
    re.compile(r"(?:^|[/\\\s'\"=])vault[/\\][^/\\\s'\"]+", re.IGNORECASE),
]

# Kasa dosyasini ekrana dokecek kabuk komutlari
DOKME_KOMUTLARI = re.compile(
    r"\b(cat|type|more|less|head|tail|Get-Content|gc|strings|xxd|od|base64)\b",
    re.IGNORECASE,
)

# Kasa betiginin kendisi muaf - kasaya erisimin mesru yolu odur
KASA_BETIGI = re.compile(r"kasa[/\\]kasa\.py", re.IGNORECASE)


# --- Sir desenleri: dosyaya yazilmasi engellenir ---------------------------

# (desen, aciklama, deger_grubu)
# deger_grubu: yer tutucu denetiminin uygulanacagi yakalama grubu.
# Butun eslesmeye bakmak yanlis sonuc veriyordu: 'ghp_...0123456789' icindeki
# rakam dizisi yuzunden gercek jeton yer tutucu saniliyordu.
SIR_DESENLERI = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "özel anahtar bloğu", 0),
    (re.compile(r"\bsk-[A-Za-z0-9]{24,}"), "gizli API anahtarı", 0),
    (re.compile(r"\bghp_[A-Za-z0-9]{30,}"), "depo erişim jetonu", 0),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}"), "depo erişim jetonu", 0),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "bulut erişim anahtarı", 0),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"), "mesajlaşma uygulaması jetonu", 0),
    (re.compile(
        r"(?i)\b(password|passwd|parola|sifre|secret|api[_-]?key|token|private[_-]?key)"
        r"\s*[:=]\s*['\"]([^'\"]{8,})['\"]"),
     "koda gömülü parola veya anahtar", 2),
]

# Yer tutucu belirtileri - yalniz DEGERE bakilir, degisken adina degil
YER_TUTUCU_KELIMELERI = re.compile(
    r"(?i)(degistir|change[_-]?me|your[_-]|placeholder|example|ornek|sample"
    r"|dummy|fake|demo|buraya|doldur)"
)

# Deger bir ortam degiskeninden geliyorsa sir sayilmaz
ORTAM_DEGISKENI = re.compile(
    r"(?i)(process\.env|os\.environ|getenv|ENV\[|\$\{[^}]+\}|<[^>]+>)"
)


def _yer_tutucu_mu(deger):
    """Bu deger gercek bir sir mi, yoksa doldurulacak bir ornek mi?"""
    if not deger or len(deger) < 8:
        return True

    if ORTAM_DEGISKENI.search(deger):
        return True

    if YER_TUTUCU_KELIMELERI.search(deger):
        return True

    # xxxx, ****, ...... gibi tekrarlar
    if re.search(r"(.)\1{3,}", deger):
        return True

    # Tek tur karakterden olusan degerler (sadece harf ya da sadece rakam)
    if deger.isalpha() or deger.isdigit():
        return True

    return False


def kasa_yolu_mu(metin_parcasi):
    if not metin_parcasi:
        return False
    return any(desen.search(str(metin_parcasi)) for desen in KASA_YOL_DESENLERI)


def okuma_kontrol(dosya_yolu):
    """Read aracıyla kasa dosyasi okunmaya calisiliyor mu?"""
    if not kasa_yolu_mu(dosya_yolu):
        return None

    return gerekce.engelle(
        "Kasa erişimi",
        f"Okuma: {dosya_yolu}",
        "Kasa dosyaları doğrudan okunamaz.\n"
        "Kural: Kasa içeriği yalnız parola verilmiş bir oturumda alınır.",
        [
            "Kasayı aç:   python scripts/kasa/kasa.py ac",
            "Listele:     python scripts/kasa/kasa.py liste",
            "Oku:         python scripts/kasa/kasa.py oku <dosya>",
            "İşin bitince: python scripts/kasa/kasa.py kilitle",
        ],
        "Kasa dosyası zaten şifrelidir; doğrudan okumak işe yaramaz, sadece risk yaratır.",
    )


def bash_kontrol(komut):
    """Kabuk komutu kasayi ekrana dokmeye mi calisiyor?"""
    if not komut:
        return None

    if KASA_BETIGI.search(komut):
        return None

    if not kasa_yolu_mu(komut):
        return None

    if not DOKME_KOMUTLARI.search(komut):
        return None

    return gerekce.engelle(
        "Kasa erişimi",
        komut,
        "Bu komut kasa dosyasını ekrana dökmeye çalışıyor.\n"
        "Kural: Kasa içeriği log'a, ekrana veya çıktıya doğrudan basılmaz.",
        [
            "Kasayı aç: python scripts/kasa/kasa.py ac",
            "Sonra oku: python scripts/kasa/kasa.py oku <dosya>",
        ],
    )


def _sir_ara(icerik):
    if not icerik:
        return None

    for desen, ad, deger_grubu in SIR_DESENLERI:
        for eslesme in desen.finditer(icerik):
            try:
                deger = eslesme.group(deger_grubu)
            except IndexError:
                deger = eslesme.group(0)

            # Jeton desenlerinde degerin kendisi zaten sirdir; uzunluk esigi
            # uygulanmaz, yalniz acik yer tutucu belirtilerine bakilir.
            if deger_grubu == 0:
                if ORTAM_DEGISKENI.search(deger) or YER_TUTUCU_KELIMELERI.search(deger):
                    continue
                return ad

            if _yer_tutucu_mu(deger):
                continue
            return ad

    return None


def yazma_kontrol(dosya_yolu, icerik):
    """Dosyaya sir yazilmasini engelle."""
    if kasa_yolu_mu(dosya_yolu):
        return gerekce.engelle(
            "Kasa erişimi",
            f"Yazma: {dosya_yolu}",
            "Kasa dosyasına doğrudan yazılamaz.",
            ["Kasaya yaz: python scripts/kasa/kasa.py yaz <dosya>"],
        )

    bulunan = _sir_ara(icerik)
    if not bulunan:
        return None

    return gerekce.engelle(
        "Sır sızıntısı",
        f"Yazma: {dosya_yolu}",
        f"Yazılmak istenen içerikte {bulunan} var.\n"
        "Kural: Sırlar kaynak kodda durmaz, kasada durur.",
        [
            "Değeri kasaya koy: python scripts/kasa/kasa.py yaz <dosya>",
            "Kodda ortam değişkeni kullan (örnek: os.environ['ANAHTAR']).",
            "Gerçekten sır değilse yer tutucu bir değer yaz.",
        ],
        "Koda gömülen sır depoya, yedeğe ve log'a sızar; geri almak çok zordur.",
    )


def main():
    try:
        girdi = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        print(json.dumps({}))
        return

    if not BETIKLER_HAZIR:
        print(json.dumps({
            "systemMessage": "Kasa koruma kancasi: ortak betikler bulunamadi, kontrol atlandi."
        }))
        return

    arac = girdi.get("tool_name", "")
    girdiler = girdi.get("tool_input", {})

    sonuc = None

    if arac == "Read":
        sonuc = okuma_kontrol(girdiler.get("file_path", ""))
    elif arac == "Bash":
        sonuc = bash_kontrol(girdiler.get("command", ""))
    elif arac in ("Write", "Edit", "MultiEdit"):
        icerik = (girdiler.get("content")
                  or girdiler.get("new_string")
                  or girdiler.get("new_source")
                  or "")
        sonuc = yazma_kontrol(girdiler.get("file_path", ""), icerik)

    print(json.dumps(sonuc if sonuc else {}))


if __name__ == "__main__":
    try:
        main()
    except Exception as hata:
        print(json.dumps({"systemMessage": f"Kasa koruma kancasi hatasi: {hata}"}))
    sys.exit(0)
