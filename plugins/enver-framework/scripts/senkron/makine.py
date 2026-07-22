#!/usr/bin/env python3
"""Makine kimliği - hangi bilgisayarda çalışıldığını bilir.

Enver birden çok bilgisayar kullanıyor. Sistemin "buradayım" diyebilmesi,
yolların makineye göre çözülebilmesi ve "en son hangi makinede ne yapıldı"
sorusunun cevaplanabilmesi için her makine tanınır.

Kayıt iki yerde tutulur:
  hafiza/makineler.json   Tanınan bütün makineler (depoya girer, senkron olur)
  Ortam                   O anki makinenin kimliği çalışma anında hesaplanır

Yollar makine kaydından çözülür; hiçbir yere sabit disk yolu yazılmaz.

Komutlar:
    durum      Bu makine tanınıyor mu
    tanit      Bu makineyi kaydet
    liste      Tanınan bütün makineler

Geliştirici: Enver KOCAK
"""

import argparse
import getpass
import platform
import socket
import sys
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "hafiza"))

import hafiza  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")


def kimlik():
    """Bu makinenin değişmeyen kimliği."""
    try:
        bilgisayar = socket.gethostname()
    except OSError:
        bilgisayar = "bilinmeyen"

    try:
        kullanici = getpass.getuser()
    except (OSError, KeyError):
        kullanici = "bilinmeyen"

    return f"{bilgisayar}/{kullanici}".lower()


def bilgi():
    """Bu makine hakkında toplanan bilgiler."""
    return {
        "kimlik": kimlik(),
        "isletim_sistemi": platform.system(),
        "surum": platform.release(),
        "proje_yolu": str(yollar.proje_kok()),
    }


def _kayit_yolu(kok=None):
    return hafiza.hafiza_dosyasi(hafiza.MAKINELER_DOSYASI, kok)


def makineler(kok=None):
    veri = hafiza.json_oku(_kayit_yolu(kok), {"makineler": {}})
    return veri.get("makineler", {})


def taniniyor_mu(kok=None):
    return kimlik() in makineler(kok)


def bu_makine(kok=None):
    """Bu makinenin kayıtlı bilgisi (yoksa None)."""
    return makineler(kok).get(kimlik())


def tanit(ad=None, kok=None):
    """Bu makineyi kaydet veya kaydını tazele."""
    yol = _kayit_yolu(kok)
    veri = hafiza.json_oku(yol, {"makineler": {}})
    veri.setdefault("makineler", {})

    kim = kimlik()
    mevcut = veri["makineler"].get(kim, {})

    kayit = dict(bilgi())
    kayit["ad"] = ad or mevcut.get("ad") or kim.split("/")[0]
    kayit["ilk_gorulme"] = mevcut.get("ilk_gorulme") or hafiza.zaman_metni()
    kayit["son_gorulme"] = hafiza.zaman_metni()

    veri["makineler"][kim] = kayit
    hafiza.json_yaz(yol, veri)

    return kayit


def son_calisan(kok=None):
    """En son hangi makinede çalışılmış?"""
    kayitlar = makineler(kok)
    if not kayitlar:
        return None

    return max(kayitlar.values(), key=lambda k: k.get("son_gorulme", ""))


def baska_makinede_mi(kok=None):
    """Son çalışma başka bir makinede mi yapılmış?

    Doğruysa, yerel bilgi eski olabilir; önce senkron alınmalı.
    """
    son = son_calisan(kok)
    if not son:
        return False
    return son.get("kimlik") != kimlik()


# ---------------------------------------------------------------- komutlar

def komut_durum(args):
    kok = yollar.proje_kok()
    kayit = bu_makine(kok)

    print(f"Bu makine : {kimlik()}")
    print(f"İşletim   : {platform.system()} {platform.release()}")
    print(f"Proje yolu: {yollar.proje_kok()}")
    print()

    if not kayit:
        print("Durum: TANINMIYOR")
        print()
        print("Bu bilgisayar daha önce kullanılmamış. Kaydetmek için:")
        print("  python makine.py tanit --ad \"<bu bilgisayarın adı>\"")
        return 1

    print(f"Durum: TANINIYOR  ({kayit.get('ad')})")
    print(f"İlk görülme: {kayit.get('ilk_gorulme')}")
    print(f"Son görülme: {kayit.get('son_gorulme')}")

    son = son_calisan(kok)
    if son and son.get("kimlik") != kimlik():
        print()
        print(f"DİKKAT: En son çalışma başka makinede yapılmış:")
        print(f"  {son.get('ad')} ({son.get('kimlik')}) - {son.get('son_gorulme')}")
        print("  Önce senkron alman iyi olur: python senkron.py cek")

    return 0


def komut_tanit(args):
    kayit = tanit(args.ad)
    print(f"Makine kaydedildi: {kayit['ad']}  ({kayit['kimlik']})")
    print(f"Proje yolu: {kayit['proje_yolu']}")
    return 0


def komut_liste(args):
    kayitlar = makineler()

    if not kayitlar:
        print("Kayıtlı makine yok.")
        return 0

    simdiki = kimlik()
    print(f"Tanınan makineler ({len(kayitlar)}):")
    print()

    for kim, kayit in sorted(kayitlar.items(),
                             key=lambda ikili: ikili[1].get("son_gorulme", ""),
                             reverse=True):
        isaret = "→" if kim == simdiki else " "
        print(f" {isaret} {kayit.get('ad', kim)}")
        print(f"     kimlik    : {kim}")
        print(f"     işletim   : {kayit.get('isletim_sistemi')} {kayit.get('surum')}")
        print(f"     proje yolu: {kayit.get('proje_yolu')}")
        print(f"     son görülme: {kayit.get('son_gorulme')}")
        print()

    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Makine kimliği")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("durum", help="Bu makine tanınıyor mu")
    p.set_defaults(islev=komut_durum)

    p = alt.add_parser("tanit", help="Bu makineyi kaydet")
    p.add_argument("--ad", help="Bu bilgisayara verilecek ad")
    p.set_defaults(islev=komut_tanit)

    p = alt.add_parser("liste", help="Tanınan bütün makineler")
    p.set_defaults(islev=komut_liste)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
