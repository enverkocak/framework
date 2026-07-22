#!/usr/bin/env python3
"""Sertifika ve alan adı takibi.

Müşteri sitesi bir sabah "güvenli değil" uyarısıyla açılmasın diye,
sertifikaların ne zaman biteceği önceden bilinir.

Alan adları proje tanımlarından okunur; ayrıca elle de sorgulanabilir.

Uyarı eşikleri:
    30 gün ve altı   dikkat
    14 gün ve altı   acil
    süresi geçmiş    kritik

Ağ erişimi yoksa sessizce atlar, hata vermez - bu kontrol çalışmanın
önünü kesmemeli.

Komutlar:
    bak <alan adı>    Tek bir alan adını sorgula
    tara              Bütün projelerin alan adlarını sorgula
    takvim            Yaklaşan bitişleri sırala

Geliştirici: Enver KOCAK
"""

import argparse
import socket
import ssl
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "hafiza"))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "projeler"))

import hafiza  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

ZAMAN_ASIMI = 12

DIKKAT_GUN = 30
ACIL_GUN = 14

DURUM_ETIKETLERI = {
    "gecerli": "geçerli",
    "dikkat": "DİKKAT",
    "acil": "ACİL",
    "kritik": "KRİTİK",
    "ulasilamadi": "ulaşılamadı",
}


def sertifika_bilgisi(alan_adi, port=443):
    """Alan adının sertifikasını sorgula."""
    baglam = ssl.create_default_context()

    try:
        with socket.create_connection((alan_adi, port), timeout=ZAMAN_ASIMI) as ham:
            with baglam.wrap_socket(ham, server_hostname=alan_adi) as guvenli:
                sertifika = guvenli.getpeercert()
    except ssl.SSLCertVerificationError as hata:
        return {"alan_adi": alan_adi, "durum": "kritik",
                "hata": f"Sertifika doğrulanamadı: {hata.verify_message}"}
    except (socket.gaierror, socket.timeout, ConnectionError, OSError) as hata:
        return {"alan_adi": alan_adi, "durum": "ulasilamadi",
                "hata": f"{type(hata).__name__}: {hata}"}

    bitis_metni = sertifika.get("notAfter")
    if not bitis_metni:
        return {"alan_adi": alan_adi, "durum": "ulasilamadi",
                "hata": "Bitiş tarihi okunamadı."}

    try:
        bitis = datetime.strptime(bitis_metni, "%b %d %H:%M:%S %Y %Z")
    except ValueError:
        return {"alan_adi": alan_adi, "durum": "ulasilamadi",
                "hata": f"Tarih çözülemedi: {bitis_metni}"}

    kalan = (bitis - datetime.now()).days

    if kalan < 0:
        durum = "kritik"
    elif kalan <= ACIL_GUN:
        durum = "acil"
    elif kalan <= DIKKAT_GUN:
        durum = "dikkat"
    else:
        durum = "gecerli"

    veren = ""
    for parca in sertifika.get("issuer", ()):
        for anahtar, deger in parca:
            if anahtar == "organizationName":
                veren = deger

    return {
        "alan_adi": alan_adi,
        "durum": durum,
        "bitis": bitis.strftime("%Y-%m-%d"),
        "kalan_gun": kalan,
        "veren": veren,
    }


def proje_alan_adlari():
    """Proje tanımlarından alan adlarını topla."""
    try:
        import kayit
    except ImportError:
        return []

    sonuc = []
    veri = kayit.kayit_oku()

    for ad, kayit_bilgisi in veri.get("projeler", {}).items():
        tanim = kayit.tanim_getir(kayit_bilgisi) or {}

        alan = tanim.get("alan_adi")
        if alan:
            sonuc.append((ad, alan))

        for alt in tanim.get("alt_alan_adlari", []) or []:
            sonuc.append((ad, alt))

    return sonuc


def _satir(proje, sonuc):
    etiket = DURUM_ETIKETLERI.get(sonuc["durum"], sonuc["durum"])

    if sonuc["durum"] == "ulasilamadi":
        return f"  [{etiket:>12}] {sonuc['alan_adi']:<34} {sonuc.get('hata', '')[:34]}"

    if sonuc["durum"] == "kritik" and "hata" in sonuc:
        return f"  [{etiket:>12}] {sonuc['alan_adi']:<34} {sonuc['hata'][:34]}"

    kalan = sonuc.get("kalan_gun", 0)
    kalan_metni = f"{kalan} gün" if kalan >= 0 else f"{-kalan} gün önce bitti"
    return (f"  [{etiket:>12}] {sonuc['alan_adi']:<34} "
            f"{sonuc.get('bitis', '-')}  ({kalan_metni})")


# ---------------------------------------------------------------- komutlar

def komut_bak(args):
    sonuc = sertifika_bilgisi(args.alan_adi)

    print(f"Alan adı : {sonuc['alan_adi']}")
    print(f"Durum    : {DURUM_ETIKETLERI.get(sonuc['durum'], sonuc['durum'])}")

    if "hata" in sonuc:
        print(f"Ayrıntı  : {sonuc['hata']}")
        return 1

    print(f"Bitiş    : {sonuc['bitis']}")
    print(f"Kalan    : {sonuc['kalan_gun']} gün")
    if sonuc.get("veren"):
        print(f"Veren    : {sonuc['veren']}")

    if sonuc["durum"] in ("acil", "kritik"):
        print()
        print("Bu sertifika yenilenmeli.")
        return 1

    return 0


def komut_tara(args):
    alanlar = proje_alan_adlari()

    if not alanlar:
        print("Proje tanımlarında alan adı bulunamadı.")
        print("Tanıma eklemek için: proje.py guncelle alan_adi \"<adres>\"")
        return 0

    print(f"SERTİFİKA TARAMASI - {len(alanlar)} alan adı")
    print("=" * 74)

    sayilar = {}
    sonuclar = []

    for proje, alan in alanlar:
        sonuc = sertifika_bilgisi(alan)
        sonuc["proje"] = proje
        sonuclar.append(sonuc)
        sayilar[sonuc["durum"]] = sayilar.get(sonuc["durum"], 0) + 1
        print(_satir(proje, sonuc))

    print()
    ozet = " · ".join(f"{DURUM_ETIKETLERI.get(d, d)}: {s}"
                      for d, s in sorted(sayilar.items()))
    print(ozet)

    if args.kaydet:
        yol = hafiza.hafiza_dosyasi("sertifika-durumu.json")
        hafiza.json_yaz(yol, {"tarama": hafiza.zaman_metni(), "sonuclar": sonuclar})
        print(f"Kaydedildi: {yol}")

    sorunlu = sayilar.get("acil", 0) + sayilar.get("kritik", 0)
    if sorunlu:
        print()
        print(f"{sorunlu} alan adı acil ilgi bekliyor.")
        return 1

    return 0


def komut_takvim(args):
    yol = hafiza.hafiza_dosyasi("sertifika-durumu.json")
    veri = hafiza.json_oku(yol, {})

    if not veri.get("sonuclar"):
        print("Kayıtlı tarama yok. Önce: python sertifika.py tara --kaydet")
        return 1

    print(f"SERTİFİKA TAKVİMİ (son tarama: {veri.get('tarama', '-')})")
    print("=" * 74)

    gecerliler = [s for s in veri["sonuclar"] if s.get("kalan_gun") is not None]
    gecerliler.sort(key=lambda s: s["kalan_gun"])

    for sonuc in gecerliler[: args.sinir]:
        print(_satir(sonuc.get("proje", "-"), sonuc))

    ulasilamayan = [s for s in veri["sonuclar"] if s.get("kalan_gun") is None]
    if ulasilamayan:
        print()
        print(f"{len(ulasilamayan)} alan adına ulaşılamadı:")
        for sonuc in ulasilamayan[:5]:
            print(f"  {sonuc['alan_adi']}")

    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Sertifika ve alan adı takibi")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("bak", help="Tek alan adı sorgula")
    p.add_argument("alan_adi")
    p.set_defaults(islev=komut_bak)

    p = alt.add_parser("tara", help="Bütün projeleri sorgula")
    p.add_argument("--kaydet", action="store_true")
    p.set_defaults(islev=komut_tara)

    p = alt.add_parser("takvim", help="Yaklaşan bitişler")
    p.add_argument("--sinir", type=int, default=20)
    p.set_defaults(islev=komut_takvim)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
