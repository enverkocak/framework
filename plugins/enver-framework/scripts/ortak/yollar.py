#!/usr/bin/env python3
"""Yol cozumleme - proje kokunu ve standart dizinleri bulur.

Sabit yol yazilmaz. Her sey proje kokunden turetilir, boylece
farkli bilgisayarlarda farkli disk/dizin yapisi sorun cikarmaz.

Standart dizinler:
    _calisma/   gecici isler (git'e girmez)
    _arsiv/     isi biten her sey, notuyla (git'e girmez)
    gunluk/     oturum kayitlari (git'e girmez)

Gelistirici: Enver KOCAK
"""

import os
from pathlib import Path

# Proje kokunu belli eden isaretler (oncelik sirasiyla)
KOK_ISARETLERI = [".git", "CLAUDE.md", ".claude"]

CALISMA_ADI = "_calisma"
ARSIV_ADI = "_arsiv"
GUNLUK_ADI = "gunluk"


def proje_kok(baslangic=None):
    """Verilen yoldan yukari cikarak proje kokunu bul.

    Bulunamazsa baslangic dizinini dondurur.
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
    """Gecici islerin yapildigi dizin."""
    yol = Path(kok or proje_kok()) / CALISMA_ADI
    if olustur:
        yol.mkdir(parents=True, exist_ok=True)
    return yol


def arsiv_dizini(kok=None, olustur=True):
    """Arsiv dizini. Proje disina cikarilmak istenirse ayarlardan okunur."""
    import ayarlar

    kok = Path(kok or proje_kok())
    ayar = ayarlar.oku(kok).get("arsiv_kok")

    yol = Path(ayar) if ayar else kok / ARSIV_ADI

    if olustur:
        yol.mkdir(parents=True, exist_ok=True)
    return yol


def gunluk_dizini(kok=None, olustur=True):
    """Oturum kayitlarinin tutuldugu dizin."""
    yol = Path(kok or proje_kok()) / GUNLUK_ADI
    if olustur:
        yol.mkdir(parents=True, exist_ok=True)
    return yol


def proje_adi(kok=None):
    """Proje klasorunun adi."""
    return Path(kok or proje_kok()).name


def ana_dizinde_mi(dosya_yolu, kok=None):
    """Bu dosya projenin ANA dizininde mi duruyor?

    Ana dizin temiz kalir kuralinin denetimi icin kullanilir.
    """
    kok = Path(kok or proje_kok()).resolve()
    hedef = Path(dosya_yolu).resolve()
    return hedef.parent == kok


def gecici_mi(dosya_yolu):
    """Bu dosya gecici/test amacli gorunuyor mu?"""
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
