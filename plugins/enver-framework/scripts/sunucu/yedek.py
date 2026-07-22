#!/usr/bin/env python3
"""Yedek alma ve geri dönüş.

Riskli bir işten önce yedek alınır; iş bozarsa tek komutla geri dönülür.

Yedekler `_arşiv/yedekler/` altında, tarihli klasörlerde durur.
Her yedeğin yanında ne için alındığı yazar - altı ay sonra hangi yedeğin
ne olduğu belli olsun diye.

Tasarım kararı: yedek alınırken kaynak DEĞİŞTİRİLMEZ, kopyalanır.
Geri dönüşte de mevcut hâl önce yedeklenir; yani geri dönüşün kendisi de
geri alınabilir. Hiçbir adım tek yönlü değildir.

Komutlar:
    al          Yedek al
    liste       Yedekleri listele
    geri        Bir yedekten geri dön
    temizle     Eski yedekleri arşive taşı (silmez)

Geliştirici: Enver KOCAK
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "hafiza"))

import hafiza  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

YEDEK_DIZINI = "yedekler"
BILGI_DOSYASI = "yedek-bilgisi.json"

# Yedeğe alınmayacak, yeniden üretilebilir içerik
ATLANACAK = {
    "node_modules", "vendor", "__pycache__", ".git", "dist", "build",
    ".venv", "venv", "_arsiv", "_calisma", ".next", ".cache",
}


def yedek_koku(kok=None):
    yol = Path(yollar.arsiv_dizini(kok)) / YEDEK_DIZINI
    yol.mkdir(parents=True, exist_ok=True)
    return yol


def _atla(yol, adlar):
    return [ad for ad in adlar if ad in ATLANACAK]


def _boyut(yol):
    toplam = 0
    for oge in Path(yol).rglob("*"):
        if oge.is_file():
            try:
                toplam += oge.stat().st_size
            except OSError:
                continue
    return toplam


def _okunur_boyut(bayt):
    for birim in ("bayt", "KB", "MB", "GB"):
        if bayt < 1024 or birim == "GB":
            return f"{bayt:.0f} {birim}" if birim == "bayt" else f"{bayt:.1f} {birim}"
        bayt /= 1024
    return f"{bayt:.1f} GB"


def al(kaynak, neden, etiket=None, kok=None):
    """Bir dosya ya da klasörün yedeğini al."""
    kaynak_yolu = Path(kaynak).resolve()
    if not kaynak_yolu.exists():
        raise FileNotFoundError(f"Kaynak bulunamadı: {kaynak}")

    damga = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    ad = etiket or kaynak_yolu.name
    hedef = yedek_koku(kok) / f"{damga}_{ad}"
    hedef.mkdir(parents=True, exist_ok=True)

    icerik_hedefi = hedef / kaynak_yolu.name

    if kaynak_yolu.is_dir():
        shutil.copytree(kaynak_yolu, icerik_hedefi, ignore=_atla)
    else:
        shutil.copy2(kaynak_yolu, icerik_hedefi)

    bilgi = {
        "kaynak": str(kaynak_yolu),
        "tarih": hafiza.zaman_metni(),
        "neden": neden,
        "etiket": ad,
        "boyut": _boyut(icerik_hedefi),
        "tur": "klasor" if kaynak_yolu.is_dir() else "dosya",
    }

    (hedef / BILGI_DOSYASI).write_text(
        json.dumps(bilgi, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return hedef, bilgi


def yedekler(kok=None):
    """Bütün yedekleri, yenisi başta olacak şekilde listele."""
    kok_yolu = yedek_koku(kok)
    sonuc = []

    for klasor in sorted(kok_yolu.iterdir(), reverse=True):
        if not klasor.is_dir():
            continue
        bilgi_yolu = klasor / BILGI_DOSYASI
        bilgi = {}
        if bilgi_yolu.is_file():
            try:
                bilgi = json.loads(bilgi_yolu.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                bilgi = {}
        bilgi["klasor"] = klasor
        sonuc.append(bilgi)

    return sonuc


def yedek_bul(anahtar, kok=None):
    """Ada ya da sıra numarasına göre yedek bul."""
    liste = yedekler(kok)

    if anahtar.isdigit():
        sira = int(anahtar) - 1
        return liste[sira] if 0 <= sira < len(liste) else None

    for bilgi in liste:
        if anahtar in bilgi["klasor"].name:
            return bilgi
    return None


def geri_don(bilgi, hedef=None, kok=None):
    """Yedekten geri dön.

    Geri dönmeden ÖNCE mevcut hâlin yedeği alınır; böylece geri dönüşün
    kendisi de geri alınabilir.
    """
    klasor = bilgi["klasor"]
    kaynak = Path(hedef or bilgi.get("kaynak", ""))

    if not kaynak:
        raise ValueError("Hedef belirlenemedi.")

    # Yedek içindeki asıl içerik
    icerikler = [y for y in klasor.iterdir() if y.name != BILGI_DOSYASI]
    if not icerikler:
        raise ValueError("Yedek boş görünüyor.")

    yedek_icerik = icerikler[0]

    # Mevcut hâli önce yedekle
    onceki = None
    if kaynak.exists():
        onceki, _ = al(kaynak, f"Geri dönüş öncesi otomatik yedek ({klasor.name})",
                       etiket=f"geridonus-oncesi-{kaynak.name}", kok=kok)

    if kaynak.exists():
        if kaynak.is_dir():
            shutil.rmtree(kaynak)
        else:
            kaynak.unlink()

    if yedek_icerik.is_dir():
        shutil.copytree(yedek_icerik, kaynak)
    else:
        kaynak.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(yedek_icerik, kaynak)

    return kaynak, onceki


# ---------------------------------------------------------------- komutlar

def komut_al(args):
    kaynak = args.kaynak or yollar.proje_kok()

    try:
        hedef, bilgi = al(kaynak, args.neden, args.etiket)
    except (OSError, FileNotFoundError) as hata:
        print(f"Yedek alınamadı: {hata}")
        return 1

    print(f"Yedek alındı: {hedef.name}")
    print(f"  kaynak: {bilgi['kaynak']}")
    print(f"  boyut : {_okunur_boyut(bilgi['boyut'])}")
    print(f"  neden : {bilgi['neden']}")
    print()
    print(f"Geri dönmek için: python yedek.py geri {hedef.name}")
    return 0


def komut_liste(args):
    liste = yedekler()

    if not liste:
        print("Henüz yedek yok.")
        return 0

    print(f"YEDEKLER ({len(liste)})")
    print("=" * 74)

    for sira, bilgi in enumerate(liste[: args.sinir], 1):
        print(f"  {sira}. {bilgi['klasor'].name}")
        print(f"     tarih : {bilgi.get('tarih', '-')}")
        print(f"     kaynak: {bilgi.get('kaynak', '-')}")
        print(f"     boyut : {_okunur_boyut(bilgi.get('boyut', 0))}")
        print(f"     neden : {bilgi.get('neden', '-')}")
        print()

    if len(liste) > args.sinir:
        print(f"... ve {len(liste) - args.sinir} yedek daha")

    return 0


def komut_geri(args):
    bilgi = yedek_bul(args.yedek)

    if bilgi is None:
        print(f"Yedek bulunamadı: {args.yedek}")
        print("Listelemek için: python yedek.py liste")
        return 1

    print(f"Geri dönülecek yedek: {bilgi['klasor'].name}")
    print(f"  tarih : {bilgi.get('tarih', '-')}")
    print(f"  neden : {bilgi.get('neden', '-')}")
    print(f"  hedef : {args.hedef or bilgi.get('kaynak', '-')}")
    print()

    if not args.onayla:
        print("Bu işlem hedefteki mevcut içeriğin üzerine yazar.")
        print("Mevcut hâlin yedeği önce otomatik alınır, yani geri dönüş de geri alınabilir.")
        print()
        print("Onaylamak için --onayla ekle.")
        return 1

    try:
        kaynak, onceki = geri_don(bilgi, args.hedef)
    except (OSError, ValueError) as hata:
        print(f"Geri dönüş başarısız: {hata}")
        return 1

    print(f"Geri dönüldü: {kaynak}")
    if onceki:
        print(f"Önceki hâl yedeklendi: {onceki.name}")
        print(f"  Bu geri dönüşü de geri almak için: python yedek.py geri {onceki.name}")
    return 0


def komut_temizle(args):
    liste = yedekler()

    if len(liste) <= args.tut:
        print(f"{len(liste)} yedek var, {args.tut} tanesi tutuluyor. Taşınacak yedek yok.")
        return 0

    import arsiv

    tasinacak = liste[args.tut:]
    print(f"{len(tasinacak)} eski yedek arşive taşınacak (silinmez).")

    if not args.onayla:
        for bilgi in tasinacak[:5]:
            print(f"  {bilgi['klasor'].name}")
        print()
        print("Onaylamak için --onayla ekle.")
        return 1

    for bilgi in tasinacak:
        arsiv.arsivle(bilgi["klasor"], f"Eski yedek: {bilgi['klasor'].name}",
                      f"Yedek sayısı {args.tut} ile sınırlandı. Kaynak: "
                      f"{bilgi.get('kaynak', '-')}")

    print(f"{len(tasinacak)} yedek arşive taşındı.")
    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Yedek alma ve geri dönüş")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("al", help="Yedek al")
    p.add_argument("--kaynak")
    p.add_argument("--neden", required=True)
    p.add_argument("--etiket")
    p.set_defaults(islev=komut_al)

    p = alt.add_parser("liste", help="Yedekleri listele")
    p.add_argument("--sinir", type=int, default=10)
    p.set_defaults(islev=komut_liste)

    p = alt.add_parser("geri", help="Yedekten geri dön")
    p.add_argument("yedek", help="Yedek adı ya da sıra numarası")
    p.add_argument("--hedef")
    p.add_argument("--onayla", action="store_true")
    p.set_defaults(islev=komut_geri)

    p = alt.add_parser("temizle", help="Eski yedekleri arşive taşı")
    p.add_argument("--tut", type=int, default=10)
    p.add_argument("--onayla", action="store_true")
    p.set_defaults(islev=komut_temizle)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
