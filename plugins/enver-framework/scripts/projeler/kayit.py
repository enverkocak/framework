#!/usr/bin/env python3
"""Merkezi proje kaydı - bütün projeler tek yerden görünür.

Enver birden çok projede çalışıyor ve biri bitmeden diğerine geçebiliyor.
Bu kayıt, hepsinin nerede durduğunu tek ekranda gösterir:
hangisi yarım, hangisi canlıda, hangisi bekliyor.

Kayıt kullanıcı düzeyinde tutulur (bütün projeler için ortak):

    ~/.claude/enver/projeler.json

Her projenin ayrıntısı kendi klasöründeki tanım dosyasından okunur;
burada yalnızca "hangi proje nerede" bilgisi durur. Böylece bir proje
taşınsa bile ayrıntısı yanında gelir.

Komutlar:
    tara      Proje köklerini gez, bulduklarını kaydet
    liste     Bütün projeler
    göster    Bir projenin ayrıntısı
    sor       Projeye geçmeden bilgi al
    kök       Taranacak kök klasörleri yönet

Geliştirici: Enver KOCAK
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "hafiza"))

import proje  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

KAYIT_YOLU = Path.home() / ".claude" / "enver" / "projeler.json"

# Bir klasörün proje olduğunu gösteren işaretler
PROJE_ISARETLERI = [".claude/proje.json", "CLAUDE.md", ".git"]

TARANMAYAN = {
    "node_modules", "vendor", "__pycache__", ".git", "dist", "build",
    "_arsiv", "_calisma", ".venv", "venv", "AppData", "Windows",
}

DURUM_SIRASI = {"yarim": 0, "gelistirmede": 1, "canlida": 2,
                "beklemede": 3, "bitti": 4, "arsiv": 5}


def kayit_oku():
    try:
        return json.loads(KAYIT_YOLU.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"kokler": [], "projeler": {}}


def kayit_yaz(veri):
    KAYIT_YOLU.parent.mkdir(parents=True, exist_ok=True)
    KAYIT_YOLU.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")


def kokler():
    """Taranacak kök klasörler. Tanımlı değilse mevcut projenin üstü kullanılır."""
    veri = kayit_oku()
    if veri.get("kokler"):
        return veri["kokler"]
    return [str(Path(yollar.proje_kok()).parent)]


def proje_mu(dizin):
    return any((dizin / isaret).exists() for isaret in PROJE_ISARETLERI)


def tara(derinlik=2):
    """Kök klasörleri gez, proje görünümlü klasörleri bul."""
    bulunanlar = {}

    def gez(dizin, kalan):
        if kalan < 0:
            return
        try:
            ogeler = sorted(dizin.iterdir())
        except OSError:
            return

        for oge in ogeler:
            if not oge.is_dir() or oge.name in TARANMAYAN or oge.name.startswith("."):
                continue

            if proje_mu(oge):
                tanim = proje.oku(oge)
                ad = (tanim or {}).get("ad") or oge.name
                bulunanlar[ad] = {
                    "ad": ad,
                    "yol": str(oge),
                    "tanimli": tanim is not None,
                }
                continue

            gez(oge, kalan - 1)

    for kok in kokler():
        kok_yolu = Path(kok)
        if kok_yolu.is_dir():
            gez(kok_yolu, derinlik)

    return bulunanlar


def kaydet(bulunanlar):
    veri = kayit_oku()
    veri.setdefault("projeler", {})
    veri["projeler"].update(bulunanlar)
    kayit_yaz(veri)
    return veri


def proje_bul(ad):
    """Ada göre projeyi bul. Tam eşleşme yoksa yaklaşık arar."""
    projeler = kayit_oku().get("projeler", {})

    if ad in projeler:
        return projeler[ad]

    kucuk = ad.lower()
    adaylar = [k for k in projeler if kucuk in k.lower()]

    if len(adaylar) == 1:
        return projeler[adaylar[0]]
    if len(adaylar) > 1:
        return {"belirsiz": adaylar}
    return None


# Tanımlar iki yerde tutulur:
#
#   1. Projenin kendi klasöründe  - asıl kayıt, projeyle birlikte taşınır
#   2. Framework hafızasında       - yansıma; proje taşınsa, silinse ya da
#                                    o disk bağlı olmasa bile bilgi kalır
#
# Asıl kayıt her zaman üstündür. Yansıma, tarama sırasında tazelenir.
MERKEZI_DIZIN = Path("hafiza") / "projeler"


def merkezi_dizin(framework_kok=None):
    kok = Path(framework_kok or yollar.proje_kok())
    return kok / MERKEZI_DIZIN


def _guvenli_ad(ad):
    """Dosya adı olarak kullanılabilir hale getir."""
    temiz = "".join(harf if harf.isalnum() or harf in "-_" else "-" for harf in ad)
    return temiz.strip("-").lower() or "isimsiz"


def merkezi_yaz(ad, tanim, framework_kok=None):
    dizin = merkezi_dizin(framework_kok)
    dizin.mkdir(parents=True, exist_ok=True)
    yol = dizin / f"{_guvenli_ad(ad)}.json"
    yol.write_text(json.dumps(tanim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return yol


def merkezi_oku(ad, framework_kok=None):
    yol = merkezi_dizin(framework_kok) / f"{_guvenli_ad(ad)}.json"
    if not yol.is_file():
        return None
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def tanim_getir(kayit):
    """Projenin tam tanımını oku.

    Önce projenin kendi klasörüne bakılır. Orada yoksa (proje taşınmış,
    silinmiş ya da o disk bağlı değilse) merkezi yansımaya düşülür.
    """
    if not kayit:
        return None

    yol = kayit.get("yol")
    if yol:
        tanim = proje.oku(Path(yol))
        if tanim is not None:
            return tanim

    return merkezi_oku(kayit.get("ad", ""))


def yansit(framework_kok=None):
    """Bütün projelerin tanımını merkezi hafızaya kopyala."""
    veri = kayit_oku()
    yansiyan = 0

    for ad, kayit_bilgisi in veri.get("projeler", {}).items():
        yol = kayit_bilgisi.get("yol")
        if not yol:
            continue

        tanim = proje.oku(Path(yol))
        if tanim is None:
            continue

        merkezi_yaz(ad, tanim, framework_kok)
        yansiyan += 1

    return yansiyan


# ---------------------------------------------------------------- komutlar

def komut_tara(args):
    bulunanlar = tara(args.derinlik)

    if not bulunanlar:
        print("Proje bulunamadı.")
        print(f"Taranan kökler: {', '.join(kokler())}")
        return 1

    kaydet(bulunanlar)

    tanimli = sum(1 for p in bulunanlar.values() if p["tanimli"])
    print(f"{len(bulunanlar)} proje bulundu, {tanimli} tanesi tanımlı.")
    print()

    for ad, kayit in sorted(bulunanlar.items()):
        isaret = " " if kayit["tanimli"] else "!"
        print(f" {isaret} {ad:32} {kayit['yol']}")

    tanimsiz = len(bulunanlar) - tanimli
    if tanimsiz:
        print()
        print(f"{tanimsiz} projenin tanımı yok (! işaretli).")
        print("Tanım olmadan şemada ve panoda ayrıntı görünmez.")
        print("Tanım eklemek için o projede: python proje.py olustur")

    return 0


def komut_liste(args):
    veri = kayit_oku()
    projeler = veri.get("projeler", {})

    if not projeler:
        print("Kayıtlı proje yok. Önce: python kayit.py tara")
        return 1

    satirlar = []
    for ad, kayit in projeler.items():
        tanim = tanim_getir(kayit)

        # Tanımlı olup olmadığı KAYITTAN değil, o anki durumdan okunur.
        # Kayıttaki bayrak tarama anından kalmadır; sonradan tanım eklenince
        # eskir ve "tanım yok" diye yanlış bilgi gösterir.
        tanimli = tanim is not None
        tanim = tanim or {}

        satirlar.append({
            "ad": ad,
            "durum": tanim.get("durum", "-"),
            "musteri": tanim.get("musteri") or "-",
            "gorev": tanim.get("gorev") or tanim.get("aciklama") or "-",
            "yol": kayit.get("yol", "-"),
            "tanimli": tanimli,
        })

    if args.durum:
        satirlar = [s for s in satirlar if s["durum"] == args.durum]

    satirlar.sort(key=lambda s: (DURUM_SIRASI.get(s["durum"], 9), s["ad"]))

    print(f"PROJELER ({len(satirlar)})")
    print("=" * 78)
    print()

    simdiki = Path(yollar.proje_kok()).resolve()

    for satir in satirlar:
        burada = ""
        try:
            if Path(satir["yol"]).resolve() == simdiki:
                burada = "  <- şu an buradasın"
        except OSError:
            pass

        durum = proje.DURUM_ETIKETLERI.get(satir["durum"], satir["durum"])
        print(f"  {satir['ad']}{burada}")
        print(f"     durum   : {durum}")
        if satir["musteri"] != "-":
            print(f"     müşteri : {satir['musteri']}")
        if satir["gorev"] != "-":
            print(f"     görev   : {satir['gorev'][:60]}")
        if not satir["tanimli"]:
            print(f"     (tanım dosyası yok)")
        print(f"     yol     : {satir['yol']}")
        print()

    return 0


def komut_goster(args):
    kayit = proje_bul(args.ad)

    if kayit is None:
        print(f"'{args.ad}' adında proje bulunamadı.")
        print("Kayıtlı projeler için: python kayit.py liste")
        return 1

    if "belirsiz" in kayit:
        print(f"'{args.ad}' birden çok projeyle eşleşiyor:")
        for ad in kayit["belirsiz"]:
            print(f"  - {ad}")
        return 1

    tanim = tanim_getir(kayit)
    if tanim is None:
        print(f"{kayit['ad']}")
        print(f"Yol: {kayit['yol']}")
        print()
        print("Bu projenin tanım dosyası yok, ayrıntı gösterilemiyor.")
        return 1

    print(proje.ayrintili_metin(tanim))
    return 0


def komut_sor(args):
    """Projeye geçmeden bilgi al."""
    kayit = proje_bul(args.ad)

    if kayit is None or "belirsiz" in kayit:
        return komut_goster(args)

    tanim = tanim_getir(kayit) or {}
    sorgu = args.sorgu.lower()

    # Sorguya göre ilgili alanı bul
    eslesmeler = []

    alan_adlari = {
        "veritabani": ["veritaban", "database", "db", "sql"],
        "dizin": ["dizin", "klasor", "klasör", "yol", "path", "nerede"],
        "alan_adi": ["alan adi", "alan adı", "domain", "site", "adres", "url"],
        "sunucu": ["sunucu", "server", "makine"],
        "musteri": ["musteri", "müşteri", "kim"],
        "durum": ["durum", "ne durumda", "bitti mi"],
        "gorev": ["gorev", "görev", "ne yapiyor", "ne yapıyor", "ne ise", "ne işe"],
        "teknolojiler": ["teknoloji", "dil", "framework", "ne ile"],
        "kasa_anahtari": ["sifre", "şifre", "parola", "erisim", "erişim"],
    }

    for alan, kelimeler in alan_adlari.items():
        if any(kelime in sorgu for kelime in kelimeler):
            deger = tanim.get(alan)
            if deger:
                eslesmeler.append((alan, deger))

    print(f"{tanim.get('ad', kayit['ad'])}")
    print("-" * 52)

    if eslesmeler:
        for alan, deger in eslesmeler:
            if isinstance(deger, list):
                deger = ", ".join(str(d) for d in deger)
            print(f"{alan}: {deger}")

        if any(alan == "kasa_anahtari" for alan, _ in eslesmeler):
            print()
            print("Gizli bilgi kasada. Okumak için kasayı açman gerekiyor.")
    else:
        print("Sorguya karşılık gelen alan bulunamadı, tam tanım:")
        print()
        print(proje.ayrintili_metin(tanim))

    return 0


def komut_kok(args):
    veri = kayit_oku()
    veri.setdefault("kokler", [])

    if args.ekle:
        yol = str(Path(args.ekle).resolve())
        if yol not in veri["kokler"]:
            veri["kokler"].append(yol)
            kayit_yaz(veri)
            print(f"Kök eklendi: {yol}")
        else:
            print("Bu kök zaten kayıtlı.")
        return 0

    mevcut = veri["kokler"] or kokler()
    print("Taranacak kök klasörler:")
    for yol in mevcut:
        print(f"  {yol}")

    if not veri["kokler"]:
        print()
        print("(Tanımlı kök yok, mevcut projenin üstü kullanılıyor.)")
        print("Eklemek için: python kayit.py kok --ekle <yol>")

    return 0


def komut_yansit(args):
    sayi = yansit()
    dizin = merkezi_dizin()

    if not sayi:
        print("Yansıtılacak tanım bulunamadı.")
        return 1

    print(f"{sayi} projenin tanımı merkezi hafızaya kopyalandı.")
    print(f"Konum: {dizin}")
    print()
    print("Asıl kayıt her zaman projenin kendi klasöründedir; buradaki kopya,")
    print("proje taşınsa ya da o disk bağlı olmasa bile bilginin kalmasını sağlar.")
    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Merkezi proje kaydı")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("tara", help="Projeleri bul ve kaydet")
    p.add_argument("--derinlik", type=int, default=2)
    p.set_defaults(islev=komut_tara)

    p = alt.add_parser("liste", help="Bütün projeler")
    p.add_argument("--durum", choices=proje.GECERLI_DURUMLAR)
    p.set_defaults(islev=komut_liste)

    p = alt.add_parser("goster", help="Bir projenin ayrıntısı")
    p.add_argument("ad")
    p.set_defaults(islev=komut_goster)

    p = alt.add_parser("sor", help="Projeye geçmeden bilgi al")
    p.add_argument("ad")
    p.add_argument("sorgu")
    p.set_defaults(islev=komut_sor)

    p = alt.add_parser("kok", help="Taranacak kök klasörler")
    p.add_argument("--ekle")
    p.set_defaults(islev=komut_kok)

    p = alt.add_parser("yansit", help="Tanımları merkezi hafızaya kopyala")
    p.set_defaults(islev=komut_yansit)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
