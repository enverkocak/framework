#!/usr/bin/env python3
"""Karar defteri ve hata kütüphanesi.

Karar defteri (T21)
    Verilen kararlar kalıcı yazılır: "bu projede şu kütüphane kullanılmayacak",
    "müşteri şu tasarımı istemedi". Aynı tartışma iki kez yapılmaz.

Hata kütüphanesi (T23)
    Çözülen her hata, belirtisi ve çözümüyle birikir. Aynı hata tekrar
    çıktığında çözüm hazır gelir; sıfırdan uğraşılmaz.

Her iki defter de hafizaya yazılır, yani makineler arasında senkron olur.

Komutlar:
    karar ekle / karar liste
    hata ekle  / hata liste / hata ara

Geliştirici: Enver KOCAK
"""

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "senkron"))

import hafiza  # noqa: E402
import makine  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")


def _sadelestir(metin):
    """Aramada Türkçe karakter farkı sorun çıkarmasın: ö/o, ç/c, ş/s."""
    donusum = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return metin.translate(donusum).lower()


def _bolumleri_ayikla(icerik):
    """Belgeyi ## başlıklarına göre parçalara ayır."""
    if not icerik.strip():
        return []

    parcalar = re.split(r"\n## ", "\n" + icerik)
    sonuc = []

    for parca in parcalar:
        parca = parca.strip()
        if not parca or parca.startswith("# "):
            continue
        satirlar = parca.splitlines()
        sonuc.append({
            "baslik": satirlar[0].lstrip("# ").strip(),
            "govde": "\n".join(satirlar[1:]).strip(),
        })

    return sonuc


# ---------------------------------------------------------------- karar

def karar_ekle(baslik, gerekce, kok=None):
    kok = kok or yollar.proje_kok()
    yol = hafiza.hafiza_dosyasi(hafiza.KARARLAR_DOSYASI, kok)

    hafiza.baslik_yoksa_yaz(
        yol, f"{yollar.proje_adi(kok)} - karar defteri",
        "Verilen kararlar burada durur. Bir daha tartışılmaz, unutulmaz.\n"
        "En üstteki kayıt en günceldir.",
    )

    govde = (
        f"**Tarih:** {hafiza.zaman_metni()}  \n"
        f"**Makine:** {makine.kimlik()}\n\n"
        f"{gerekce.strip()}\n"
    )

    hafiza.bolum_ekle(yol, baslik.strip(), govde)
    return yol


def karar_liste(sinir=None, kok=None):
    yol = hafiza.hafiza_dosyasi(hafiza.KARARLAR_DOSYASI, kok)
    bolumler = _bolumleri_ayikla(hafiza.metin_oku(yol))
    return bolumler[:sinir] if sinir else bolumler


# ---------------------------------------------------------------- hata

def hata_ekle(belirti, cozum, baglam=None, kok=None):
    kok = kok or yollar.proje_kok()
    yol = hafiza.hafiza_dosyasi(hafiza.HATALAR_DOSYASI, kok)

    hafiza.baslik_yoksa_yaz(
        yol, f"{yollar.proje_adi(kok)} - hata ve çözüm kütüphanesi",
        "Çözülen hatalar burada birikir. Aynı hata tekrar çıkarsa çözümü hazırdır.",
    )

    govde = [f"**Tarih:** {hafiza.zaman_metni()}\n"]

    if baglam:
        govde.append(f"**Nerede:** {baglam.strip()}\n")

    govde.append(f"**Çözüm:**\n\n{hafiza.gizle(cozum.strip())}\n")

    hafiza.bolum_ekle(yol, hafiza.gizle(belirti.strip()), "\n".join(govde))
    return yol


def hata_ara(sorgu, kok=None):
    """Belirtiye göre çözülmüş hata ara."""
    yol = hafiza.hafiza_dosyasi(hafiza.HATALAR_DOSYASI, kok)
    bolumler = _bolumleri_ayikla(hafiza.metin_oku(yol))

    if not sorgu:
        return bolumler

    kelimeler = [k for k in re.split(r"\W+", sorgu.lower()) if len(k) > 2]
    if not kelimeler:
        return []

    # Butun kelimeler gecmeli. Once herhangi biri yeterliydi ve bu yuzden
    # "boyle-bir-sey-yok" gibi bir sorgu, icinde yalnizca "yok" gecen bir
    # kayitla eslesiyordu.
    eslesenler = []
    for bolum in bolumler:
        tam_metin = _sadelestir(bolum["baslik"] + " " + bolum["govde"])
        if all(_sadelestir(kelime) in tam_metin for kelime in kelimeler):
            eslesenler.append(bolum)

    return eslesenler


# ---------------------------------------------------------------- komutlar

def _yazdir(bolumler, bos_mesaj, sinir=10):
    if not bolumler:
        print(bos_mesaj)
        return

    for bolum in bolumler[:sinir]:
        print(f"- {bolum['baslik']}")
        for satir in bolum["govde"].splitlines():
            if satir.strip():
                print(f"    {satir}")
        print()

    if len(bolumler) > sinir:
        print(f"... ve {len(bolumler) - sinir} kayıt daha")


def komut_karar_ekle(args):
    yol = karar_ekle(args.baslik, args.gerekce)
    print(f"Karar kaydedildi: {yol}")
    return 0


def komut_karar_liste(args):
    _yazdir(karar_liste(), "Henüz karar kaydı yok.", args.sinir)
    return 0


def komut_hata_ekle(args):
    yol = hata_ekle(args.belirti, args.cozum, args.nerede)
    print(f"Hata ve çözümü kaydedildi: {yol}")
    return 0


def komut_hata_liste(args):
    _yazdir(hata_ara(None), "Henüz çözülmüş hata kaydı yok.", args.sinir)
    return 0


def komut_hata_ara(args):
    sonuc = hata_ara(args.sorgu)
    if not sonuc:
        print(f"'{args.sorgu}' ile eşleşen çözülmüş hata bulunamadı.")
        return 1

    print(f"'{args.sorgu}' için {len(sonuc)} eşleşme:\n")
    _yazdir(sonuc, "", args.sinir)
    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Karar defteri ve hata kütüphanesi")
    alt = ayristirici.add_subparsers(dest="defter", required=True)

    karar = alt.add_parser("karar", help="Karar defteri").add_subparsers(
        dest="islem", required=True)

    p = karar.add_parser("ekle")
    p.add_argument("baslik")
    p.add_argument("gerekce")
    p.set_defaults(islev=komut_karar_ekle)

    p = karar.add_parser("liste")
    p.add_argument("--sinir", type=int, default=10)
    p.set_defaults(islev=komut_karar_liste)

    hata = alt.add_parser("hata", help="Hata kütüphanesi").add_subparsers(
        dest="islem", required=True)

    p = hata.add_parser("ekle")
    p.add_argument("belirti")
    p.add_argument("cozum")
    p.add_argument("--nerede")
    p.set_defaults(islev=komut_hata_ekle)

    p = hata.add_parser("liste")
    p.add_argument("--sinir", type=int, default=10)
    p.set_defaults(islev=komut_hata_liste)

    p = hata.add_parser("ara")
    p.add_argument("sorgu")
    p.add_argument("--sinir", type=int, default=5)
    p.set_defaults(islev=komut_hata_ara)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
