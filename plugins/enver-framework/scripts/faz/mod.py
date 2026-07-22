#!/usr/bin/env python3
"""Çalışma modu profilleri.

Dört mod var. Her biri, sistemin ne kadar soru sorup ne kadar kendi
karar vereceğini belirler:

    dikkatli    Varsayılan. Riskli işlemlerde onay ister.
    hızlı       Rutin işlerde soru azaltılır, riskli olanlar yine sorulur.
    sunucuda    En temkinli. Müşteri sunucusunda çalışırken kullanılır;
                her dış etkili işlem onay ister.
    tam-yetki   Faz bitene kadar soru sorulmaz.

Tam yetki modunda bile şunlar durur: kasa parolası, silme, uzak sunucu,
canlıya çıkış, depo ayarı, geri alınamaz veritabanı işlemleri.

Mod ayarı kullanıcı düzeyinde tutulur ve bütün projelerde geçerlidir.

Geliştirici: Enver KOCAK
"""

import argparse
import sys
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "hafiza"))

import ayarlar  # noqa: E402
import faz  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

MODLAR = {
    "dikkatli": {
        "tam_yetki": False,
        "aciklama": "Riskli işlemlerde onay ister. Varsayılan mod.",
    },
    "hizli": {
        "tam_yetki": False,
        "aciklama": "Rutin işlerde soru azaltılır, riskli olanlar yine sorulur.",
    },
    "sunucuda": {
        "tam_yetki": False,
        "aciklama": "En temkinli mod. Müşteri sunucusunda çalışırken kullanılır.",
    },
    "tam-yetki": {
        "tam_yetki": True,
        "aciklama": "Faz bitene kadar soru sorulmaz.",
    },
}

ISTISNA_LISTESI = [
    "Kasa parolası istenmesi",
    "Silme girişimi",
    "Uzak sunucuya erişim",
    "Canlıya çıkış ve yayınlama",
    "Depo görünürlüğü ayarı",
    "Geri alınamaz veritabanı işlemleri",
    "Ödeme işlemleri",
]


def mod_oku(kok=None):
    return ayarlar.oku(kok).get("calisma_modu", "dikkatli")


def mod_ayarla(ad, kok=None):
    if ad not in MODLAR:
        return False

    ayarlar.yaz({
        "calisma_modu": ad,
        "tam_yetki": MODLAR[ad]["tam_yetki"],
    })
    return True


def komut_durum(args):
    kok = yollar.proje_kok()
    ad = mod_oku(kok)
    tanim = MODLAR.get(ad, {})

    print(f"Çalışma modu: {ad}")
    print(f"  {tanim.get('aciklama', '-')}")
    print()

    if tanim.get("tam_yetki"):
        aktif = faz.aktif_faz(kok)
        if aktif:
            print(f"Aktif faz: {aktif['no']} - {aktif['ad']}")
            print("Faz bitene kadar izin sorulmayacak.")
        else:
            print("DİKKAT: Tam yetki açık ama aktif faz yok.")
            print("Nerede duracağı belli değil. Bir faz tanımla ya da modu değiştir.")
        print()
        print("Bu modda bile duran işlemler:")
        for madde in ISTISNA_LISTESI:
            print(f"  - {madde}")

    print()
    print("Modlar:")
    for mod_adi, mod_tanim in MODLAR.items():
        isaret = "→" if mod_adi == ad else " "
        print(f" {isaret} {mod_adi:12} {mod_tanim['aciklama']}")

    return 0


def komut_ayarla(args):
    kok = yollar.proje_kok()

    if not mod_ayarla(args.ad, kok):
        print(f"Bilinmeyen mod: {args.ad}")
        print(f"Geçerli modlar: {', '.join(MODLAR)}")
        return 1

    tanim = MODLAR[args.ad]
    print(f"Çalışma modu: {args.ad}")
    print(f"  {tanim['aciklama']}")

    if tanim["tam_yetki"]:
        aktif = faz.aktif_faz(kok)
        print()
        if aktif:
            print(f"Aktif faz: {aktif['no']} - {aktif['ad']}")
            print("Faz bitene kadar izin sorulmayacak.")
            if aktif.get("kapi_komutu"):
                print(f"Kapı kontrolü: {aktif['kapi_komutu']}")
            else:
                print("UYARI: Bu fazın kapı kontrolü tanımlı değil.")
                print("Bitişin nasıl ölçüleceği belli olmalı.")
        else:
            print("UYARI: Aktif faz yok. Tam yetkinin nerede duracağı belli değil.")
            print("Önce bir faz tanımla: python faz.py ekle <no> \"<ad>\" --kapi \"<komut>\"")

        print()
        print("Bu modda bile duran işlemler:")
        for madde in ISTISNA_LISTESI:
            print(f"  - {madde}")
        print()
        print("Kapatmak için: python mod.py dikkatli")

    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Çalışma modu")
    ayristirici.add_argument("ad", nargs="?", choices=list(MODLAR),
                             help="Ayarlanacak mod (boş bırakılırsa durum gösterilir)")

    args = ayristirici.parse_args()

    if args.ad:
        return komut_ayarla(args)
    return komut_durum(args)


if __name__ == "__main__":
    sys.exit(main())
