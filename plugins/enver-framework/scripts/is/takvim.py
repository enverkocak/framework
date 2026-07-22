#!/usr/bin/env python3
"""Hizmet takvimi - yenileme ve bakım tarihleri.

Bir müşterinin hosting'i sessizce biterse site kapanır ve bunu ilk fark eden
müşteri olur. Bu takvim, o tarihlerin önceden bilinmesi içindir.

Kayıtlar iki yerden gelir:
    1. Elle eklenen hizmetler (hosting, alan adı, bakım, lisans)
    2. Sertifika taramasının bulduğu bitiş tarihleri

Uyarı eşikleri:
    60 gün ve altı   yaklaşıyor
    30 gün ve altı   dikkat
    7 gün ve altı    acil
    geçmiş           kritik

Komutlar:
    ekle       Hizmet kaydı ekle
    liste      Yaklaşan bitişler
    yenile     Bir kaydın tarihini ilerlet
    sil        Kaydı arşivle (kaldırır ama iz bırakır)

Geliştirici: Enver KOCAK
"""

import argparse
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "hafiza"))

import hafiza  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

TAKVIM_DOSYASI = "hizmet-takvimi.json"

TURLER = ["hosting", "alan-adi", "sertifika", "bakim", "lisans", "sozlesme", "diger"]

TUR_ETIKETLERI = {
    "hosting": "Hosting", "alan-adi": "Alan adı", "sertifika": "Sertifika",
    "bakim": "Bakım", "lisans": "Lisans", "sozlesme": "Sözleşme", "diger": "Diğer",
}

YAKLASIYOR_GUN = 60
DIKKAT_GUN = 30
ACIL_GUN = 7

DURUM_ETIKETLERI = {
    "gecerli": "geçerli", "yaklasiyor": "yaklaşıyor",
    "dikkat": "DİKKAT", "acil": "ACİL", "kritik": "KRİTİK",
}

DURUM_SIRASI = {"kritik": 0, "acil": 1, "dikkat": 2, "yaklasiyor": 3, "gecerli": 4}


def dosya_yolu(kok=None):
    return hafiza.hafiza_dosyasi(TAKVIM_DOSYASI, kok)


def oku(kok=None):
    veri = hafiza.json_oku(dosya_yolu(kok), {"kayitlar": []})
    veri.setdefault("kayitlar", [])
    return veri


def yaz(veri, kok=None):
    hafiza.json_yaz(dosya_yolu(kok), veri)


def _tarih_coz(metin):
    try:
        return datetime.strptime(metin, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def durum_hesapla(bitis_metni):
    bitis = _tarih_coz(bitis_metni)
    if bitis is None:
        return "gecerli", None

    kalan = (bitis - date.today()).days

    if kalan < 0:
        return "kritik", kalan
    if kalan <= ACIL_GUN:
        return "acil", kalan
    if kalan <= DIKKAT_GUN:
        return "dikkat", kalan
    if kalan <= YAKLASIYOR_GUN:
        return "yaklasiyor", kalan
    return "gecerli", kalan


def _sonraki_no(veri):
    return max((k.get("no", 0) for k in veri["kayitlar"]), default=0) + 1


def ekle(ad, tur, bitis, proje=None, musteri=None, tutar=None, not_metni="", kok=None):
    veri = oku(kok)

    kayit = {
        "no": _sonraki_no(veri),
        "ad": ad.strip(),
        "tur": tur,
        "bitis": bitis,
        "proje": proje or yollar.proje_adi(kok),
        "musteri": musteri or "",
        "tutar": tutar or "",
        "not": not_metni.strip(),
        "olusturma": hafiza.zaman_metni(),
    }

    veri["kayitlar"].append(kayit)
    yaz(veri, kok)
    return kayit


def kayitlar(kok=None):
    """Bütün kayıtları durumuyla birlikte, aciliyet sırasında döndür."""
    sonuc = []

    for kayit in oku(kok)["kayitlar"]:
        durum, kalan = durum_hesapla(kayit.get("bitis"))
        zengin = dict(kayit)
        zengin["durum"] = durum
        zengin["kalan_gun"] = kalan
        sonuc.append(zengin)

    sonuc.sort(key=lambda k: (DURUM_SIRASI.get(k["durum"], 9),
                              k["kalan_gun"] if k["kalan_gun"] is not None else 9999))
    return sonuc


def sertifikadan_al(kok=None):
    """Sertifika taramasının sonuçlarını takvime ekle."""
    veri = hafiza.json_oku(hafiza.hafiza_dosyasi("sertifika-durumu.json", kok), {})

    eklenen = 0
    takvim = oku(kok)
    mevcut = {(k.get("ad"), k.get("tur")) for k in takvim["kayitlar"]}

    for sonuc in veri.get("sonuclar", []):
        if not sonuc.get("bitis"):
            continue

        anahtar = (sonuc["alan_adi"], "sertifika")
        if anahtar in mevcut:
            continue

        takvim["kayitlar"].append({
            "no": _sonraki_no(takvim),
            "ad": sonuc["alan_adi"],
            "tur": "sertifika",
            "bitis": sonuc["bitis"],
            "proje": sonuc.get("proje", ""),
            "musteri": "",
            "tutar": "",
            "not": "Sertifika taramasından alındı.",
            "olusturma": hafiza.zaman_metni(),
        })
        eklenen += 1

    if eklenen:
        yaz(takvim, kok)

    return eklenen


def _satir(kayit):
    durum = DURUM_ETIKETLERI.get(kayit["durum"], kayit["durum"])
    tur = TUR_ETIKETLERI.get(kayit.get("tur"), kayit.get("tur", "-"))

    kalan = kayit.get("kalan_gun")
    if kalan is None:
        kalan_metni = "tarih yok"
    elif kalan < 0:
        kalan_metni = f"{-kalan} gün önce bitti"
    else:
        kalan_metni = f"{kalan} gün"

    return (f"  [{durum:>10}] {kayit['ad'][:28]:<30} {tur:<11} "
            f"{kayit.get('bitis', '-'):<12} {kalan_metni}")


# ---------------------------------------------------------------- komutlar

def komut_ekle(args):
    if _tarih_coz(args.bitis) is None:
        print(f"Tarih anlaşılmadı: {args.bitis}")
        print("Biçim: YYYY-AA-GG  (örnek: 2027-03-15)")
        return 1

    kayit = ekle(args.ad, args.tur, args.bitis, args.proje,
                 args.musteri, args.tutar, args.not_metni or "")

    durum, kalan = durum_hesapla(kayit["bitis"])

    print(f"Kayıt eklendi: #{kayit['no']}")
    print(f"  {kayit['ad']} ({TUR_ETIKETLERI[kayit['tur']]})")
    print(f"  bitiş: {kayit['bitis']} · kalan: {kalan} gün · "
          f"durum: {DURUM_ETIKETLERI[durum]}")
    return 0


def komut_liste(args):
    if args.sertifikalari_al:
        eklenen = sertifikadan_al()
        if eklenen:
            print(f"Sertifika taramasından {eklenen} kayıt eklendi.")
            print()

    liste = kayitlar()

    if args.tur:
        liste = [k for k in liste if k.get("tur") == args.tur]
    if args.proje:
        liste = [k for k in liste if k.get("proje") == args.proje]
    if args.sadece_yaklasan:
        liste = [k for k in liste if k["durum"] != "gecerli"]

    print("HİZMET TAKVİMİ")
    print("=" * 82)

    if not liste:
        print()
        print("Kayıt yok.")
        print("Eklemek için: python takvim.py ekle \"<ad>\" <tur> <YYYY-AA-GG>")
        return 0

    print(f"  {'durum':>12}  {'ad':<30} {'tür':<11} {'bitiş':<12} kalan")
    print("  " + "-" * 78)

    for kayit in liste[: args.sinir]:
        print(_satir(kayit))

    if len(liste) > args.sinir:
        print(f"  ... ve {len(liste) - args.sinir} kayıt daha")

    sorunlu = [k for k in liste if k["durum"] in ("acil", "kritik")]
    yaklasan = [k for k in liste if k["durum"] == "dikkat"]

    print()
    if sorunlu:
        print(f"{len(sorunlu)} kayıt ACİL ilgi bekliyor.")
    if yaklasan:
        print(f"{len(yaklasan)} kayıt bir ay içinde bitiyor.")
    if not sorunlu and not yaklasan:
        print("Yakın zamanda biten bir şey yok.")

    return 1 if sorunlu else 0


def komut_yenile(args):
    veri = oku()

    for kayit in veri["kayitlar"]:
        if kayit.get("no") != args.no:
            continue

        eski = kayit.get("bitis")

        if args.tarih:
            if _tarih_coz(args.tarih) is None:
                print(f"Tarih anlaşılmadı: {args.tarih}")
                return 1
            kayit["bitis"] = args.tarih
        else:
            mevcut = _tarih_coz(eski) or date.today()
            kayit["bitis"] = (mevcut + timedelta(days=365 * args.yil)).isoformat()

        kayit["son_yenileme"] = hafiza.zaman_metni()
        yaz(veri)

        durum, kalan = durum_hesapla(kayit["bitis"])
        print(f"#{kayit['no']} yenilendi: {kayit['ad']}")
        print(f"  {eski}  →  {kayit['bitis']}  ({kalan} gün)")
        return 0

    print(f"#{args.no} numaralı kayıt bulunamadı.")
    return 1


def komut_sil(args):
    veri = oku()

    for sira, kayit in enumerate(veri["kayitlar"]):
        if kayit.get("no") != args.no:
            continue

        veri["kayitlar"].pop(sira)
        yaz(veri)

        # Kayit silinmez, hafizaya not dusulur
        hafiza.bolum_ekle(
            hafiza.hafiza_dosyasi("takvim-kaldirilanlar.md"),
            f"{hafiza.zaman_metni()} - {kayit.get('ad')}",
            f"Tür: {TUR_ETIKETLERI.get(kayit.get('tur'), '-')}  \n"
            f"Bitiş: {kayit.get('bitis')}  \n"
            f"Proje: {kayit.get('proje')}  \n"
            f"Sebep: {args.sebep or 'belirtilmedi'}",
        )

        print(f"#{args.no} takvimden kaldırıldı: {kayit.get('ad')}")
        print("Kayıt silinmedi, hafızaya not düşüldü.")
        return 0

    print(f"#{args.no} numaralı kayıt bulunamadı.")
    return 1


def main():
    ayristirici = argparse.ArgumentParser(description="Hizmet takvimi")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("ekle", help="Hizmet kaydı ekle")
    p.add_argument("ad")
    p.add_argument("tur", choices=TURLER)
    p.add_argument("bitis", help="YYYY-AA-GG")
    p.add_argument("--proje")
    p.add_argument("--musteri")
    p.add_argument("--tutar")
    p.add_argument("--not", dest="not_metni")
    p.set_defaults(islev=komut_ekle)

    p = alt.add_parser("liste", help="Yaklaşan bitişler")
    p.add_argument("--tur", choices=TURLER)
    p.add_argument("--proje")
    p.add_argument("--sadece-yaklasan", action="store_true", dest="sadece_yaklasan")
    p.add_argument("--sertifikalari-al", action="store_true", dest="sertifikalari_al")
    p.add_argument("--sinir", type=int, default=25)
    p.set_defaults(islev=komut_liste)

    p = alt.add_parser("yenile", help="Tarihi ilerlet")
    p.add_argument("no", type=int)
    p.add_argument("--tarih", help="Yeni tarih (YYYY-AA-GG)")
    p.add_argument("--yil", type=int, default=1)
    p.set_defaults(islev=komut_yenile)

    p = alt.add_parser("sil", help="Takvimden kaldır")
    p.add_argument("no", type=int)
    p.add_argument("--sebep")
    p.set_defaults(islev=komut_sil)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
