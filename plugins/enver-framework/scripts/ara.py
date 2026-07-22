#!/usr/bin/env python3
"""Tek arama noktası - her şey tek yerden aranır.

Bilgi dört ayrı yerde birikiyor: notlar, hafıza, proje tanımları ve
klasör içindekiler belgeleri. "Şunu nerede yazmıştık" sorusunun cevabı
için dört yere ayrı ayrı bakmak gerekmesin diye hepsi tek aramadan geçer.

Aranan yerler:
    hafiza/       durum, kararlar, hatalar, oturum özetleri
    bilgi/        statik notlar
    proje tanımları (bu projede ve merkezi yansımada)
    ICINDEKILER.md belgeleri

Kasa ARANMAZ. İçeriği şifrelidir ve parola olmadan okunamaz; arama
yalnızca "bu bilgi kasada olabilir" diye yol gösterir.

Geliştirici: Enver KOCAK
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI / "ortak"))
sys.path.insert(0, str(SCRIPT_DIZINI / "hafiza"))
sys.path.insert(0, str(SCRIPT_DIZINI / "projeler"))

import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

# Aranacak alanlar: (etiket, göreli yol, dosya deseni)
ALANLAR = [
    ("hafıza", "hafiza", "**/*.md"),
    ("proje tanımı", "hafiza/projeler", "*.json"),
    ("bilgi notu", "bilgi", "**/*.md"),
    ("içindekiler", ".", "**/ICINDEKILER.md"),
    ("komut", "plugins/enver-framework/commands", "*.md"),
    ("kural", "plugins/enver-framework/references", "*.md"),
]

TARANMAYAN = ("/_arsiv/", "/_calisma/", "/.git/", "/node_modules/")

# Kasaya yönlendirilecek konular
KASA_KONULARI = re.compile(
    r"(?i)(parola|şifre|sifre|anahtar|token|erişim|erisim|kimlik|giriş bilgisi)"
)


def _turkce_sadelestir(metin):
    """Aramada ö/o, ç/c farkı sorun çıkarmasın."""
    donusum = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return metin.translate(donusum).lower()


def _dosyalari_topla(kok):
    kok = Path(kok)
    dosyalar = []

    for etiket, bagil, desen in ALANLAR:
        dizin = kok / bagil
        if not dizin.is_dir():
            continue

        for yol in dizin.glob(desen):
            if not yol.is_file():
                continue
            duz = yol.as_posix()
            if any(parca in duz for parca in TARANMAYAN):
                continue
            dosyalar.append((etiket, yol))

    return dosyalar


def _json_metni(yol):
    """Proje tanımını aranabilir metne çevir."""
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""

    parcalar = []

    def gez(deger, on=""):
        if isinstance(deger, dict):
            for anahtar, alt in deger.items():
                gez(alt, f"{on}{anahtar}: ")
        elif isinstance(deger, list):
            for alt in deger:
                gez(alt, on)
        elif deger:
            parcalar.append(f"{on}{deger}")

    gez(veri)
    return "\n".join(parcalar)


def ara(sorgu, kok=None, baglam=1):
    """Bütün alanlarda ara, eşleşmeleri döndür."""
    kok = Path(kok or yollar.proje_kok())
    kelimeler = [k for k in _turkce_sadelestir(sorgu).split() if len(k) > 1]

    if not kelimeler:
        return []

    sonuclar = []

    for etiket, yol in _dosyalari_topla(kok):
        if yol.suffix == ".json":
            icerik = _json_metni(yol)
        else:
            try:
                icerik = yol.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue

        if not icerik:
            continue

        satirlar = icerik.splitlines()
        sade_satirlar = [_turkce_sadelestir(s) for s in satirlar]

        for sira, sade in enumerate(sade_satirlar):
            if not all(kelime in sade for kelime in kelimeler):
                continue

            bas = max(0, sira - baglam)
            son = min(len(satirlar), sira + baglam + 1)

            sonuclar.append({
                "alan": etiket,
                "dosya": yol.relative_to(kok).as_posix(),
                "satir": sira + 1,
                "eslesme": satirlar[sira].strip(),
                "baglam": [s.strip() for s in satirlar[bas:son]],
            })

    return sonuclar


def kasa_ipucu(sorgu):
    """Sorgu gizli bilgiyle ilgiliyse kullanıcıyı kasaya yönlendir."""
    return bool(KASA_KONULARI.search(sorgu))


def komut_ara(args):
    sonuclar = ara(args.sorgu, baglam=args.baglam)

    if not sonuclar:
        print(f"'{args.sorgu}' için sonuç bulunamadı.")
        if kasa_ipucu(args.sorgu):
            print()
            print("Bu konu gizli bilgiyle ilgili olabilir. Kasa aranmaz;")
            print("bakmak için: python scripts/kasa/kasa.py ac")
        return 1

    # Alanına göre grupla
    gruplar = {}
    for sonuc in sonuclar:
        gruplar.setdefault(sonuc["alan"], []).append(sonuc)

    print(f"'{args.sorgu}' için {len(sonuclar)} eşleşme")
    print("=" * 62)

    for alan in sorted(gruplar):
        grup = gruplar[alan][: args.sinir]
        print()
        print(f"{alan.upper()} ({len(gruplar[alan])})")
        print("-" * 62)

        for sonuc in grup:
            print(f"  {sonuc['dosya']}:{sonuc['satir']}")
            for satir in sonuc["baglam"]:
                isaret = "→" if satir == sonuc["eslesme"] else " "
                print(f"    {isaret} {satir[:88]}")
            print()

        if len(gruplar[alan]) > args.sinir:
            print(f"  ... ve {len(gruplar[alan]) - args.sinir} eşleşme daha")
            print()

    if kasa_ipucu(args.sorgu):
        print("-" * 62)
        print("Not: Bu konu gizli bilgiyle ilgili görünüyor.")
        print("Kasa aranmaz; içine bakmak için kasayı açman gerekir.")

    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Tek arama noktası")
    ayristirici.add_argument("sorgu")
    ayristirici.add_argument("--sinir", type=int, default=5, help="Alan başına sonuç")
    ayristirici.add_argument("--baglam", type=int, default=1, help="Kaç satır bağlam")
    ayristirici.set_defaults(islev=komut_ara)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
