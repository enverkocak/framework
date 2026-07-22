#!/usr/bin/env python3
"""Yol çözümleme - proje kökünü ve standart dizinleri bulur.

Sabit yol yazılmaz. Her şey proje kökünden türetilir, böylece
farklı bilgisayarlarda farklı disk/dizin yapısı sorun çıkarmaz.

Standart dizinler:
    _çalışma/   geçici işler (git'e girmez)
    _arşiv/     işi biten her şey, notuyla (git'e girmez)
    günlük/     oturum kayıtları (git'e girmez)

Geliştirici: Enver KOCAK
"""

import os
from pathlib import Path

# Proje kökünü belli eden işaretler (öncelik sırasıyla)
KOK_ISARETLERI = [".git", "CLAUDE.md", ".claude"]

CALISMA_ADI = "_calisma"
ARSIV_ADI = "_arsiv"
GUNLUK_ADI = "gunluk"


def proje_kok(baslangic=None):
    """Verilen yoldan yukarı çıkarak proje kökünü bul.

    Bulunamazsa başlangıç dizinini döndürür.
    """
    if baslangic is None:
        baslangic = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    dizin = Path(baslangic).resolve()
    if dizin.is_file():
        dizin = dizin.parent

    ilk = dizin

    while True:
        for isaret in KOK_ISARETLERI:
            if (dizin / isaret).exists():
                return dizin

        ust = dizin.parent
        if ust == dizin:
            return ilk
        dizin = ust


def calisma_dizini(kok=None, olustur=True):
    """Geçici işlerin yapıldığı dizin."""
    yol = Path(kok or proje_kok()) / CALISMA_ADI
    if olustur:
        yol.mkdir(parents=True, exist_ok=True)
    return yol


def arsiv_dizini(kok=None, olustur=True):
    """Arşiv dizini. Proje dışına çıkarılmak istenirse ayarlardan okunur."""
    import ayarlar

    kok = Path(kok or proje_kok())
    ayar = ayarlar.oku(kok).get("arsiv_kok")

    yol = Path(ayar) if ayar else kok / ARSIV_ADI

    if olustur:
        yol.mkdir(parents=True, exist_ok=True)
    return yol


def gunluk_dizini(kok=None, olustur=True):
    """Oturum kayıtlarının tutulduğu dizin."""
    yol = Path(kok or proje_kok()) / GUNLUK_ADI
    if olustur:
        yol.mkdir(parents=True, exist_ok=True)
    return yol


def proje_adi(kok=None):
    """Proje klasörünün adı."""
    return Path(kok or proje_kok()).name


def ana_dizinde_mi(dosya_yolu, kok=None):
    """Bu dosya projenin ANA dizininde mi duruyor?

    Ana dizin temiz kalır kuralının denetimi için kullanılır.
    """
    kok = Path(kok or proje_kok()).resolve()
    hedef = Path(dosya_yolu).resolve()
    return hedef.parent == kok


def gecici_mi(dosya_yolu):
    """Bu dosya geçici/test amaçlı görünüyor mu?"""
    ad = Path(dosya_yolu).name.lower()

    gecici_ekler = (".tmp", ".temp", ".bak", ".log", ".swp")
    gecici_basliklar = ("test-", "deneme-", "gecici-", "tmp-", "_test")
    gecici_icerenler = ("-test.", "-deneme.", "-yedek.", "-kopya.")

    if ad.endswith(gecici_ekler):
        return True
    if ad.startswith(gecici_basliklar):
        return True
    if any(parca in ad for parca in gecici_icerenler):
        return True

    return False


if __name__ == "__main__":
    import sys

    kok = proje_kok(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"Proje koku    : {kok}")
    print(f"Proje adi     : {proje_adi(kok)}")
    print(f"Calisma dizini: {calisma_dizini(kok, olustur=False)}")
    print(f"Arsiv dizini  : {arsiv_dizini(kok, olustur=False)}")
    print(f"Gunluk dizini : {gunluk_dizini(kok, olustur=False)}")
