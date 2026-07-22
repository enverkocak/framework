#!/usr/bin/env python3
"""Sunucu ve proje haritası - okuma ve sorgulama.

Sunucu koruması artık sabit kodlanmış IP ve dizin kullanmaz;
bütün bilgi references/sunucu-haritası.json içinden gelir.

Kullanım (komut satırı):
    python sunucu_harita.py                 haritayı özetle
    python sunucu_harita.py <dizin>         bu dizin hangi projeye ait

Geliştirici: Enver KOCAK
"""

import json
import sys
from pathlib import Path

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

VARSAYILAN_YOL = (
    Path(__file__).resolve().parent.parent.parent / "references" / "sunucu-haritasi.json"
)

_onbellek = {}


def yukle(yol=None):
    """Haritayı oku. Dosya yoksa boş harita döndür."""
    yol = Path(yol or VARSAYILAN_YOL)
    anahtar = str(yol)

    if anahtar in _onbellek:
        return _onbellek[anahtar]

    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        veri = {"sunucular": [], "korunan_kok_dizinler": []}

    _onbellek[anahtar] = veri
    return veri


def sunucu_bul(adres, yol=None):
    """Adrese göre sunucu kaydını döndür."""
    for sunucu in yukle(yol).get("sunucular", []):
        if sunucu.get("adres") == adres:
            return sunucu
    return None


def adresler(yol=None):
    return [s.get("adres") for s in yukle(yol).get("sunucular", []) if s.get("adres")]


def izinli_dizinler(sunucu):
    """Bir sunucuda çalışılmasına izin verilen bütün dizinler."""
    sonuc = list(sunucu.get("ortak_izinli_dizinler", []))
    for proje in sunucu.get("projeler", []):
        if proje.get("dizin"):
            sonuc.append(proje["dizin"])
    return sonuc


def korunan_kokler(yol=None):
    return yukle(yol).get("korunan_kok_dizinler", [])


def proje_bul(dizin, sunucu=None, yol=None):
    """Verilen dizin hangi projeye ait?"""
    sunucular = [sunucu] if sunucu else yukle(yol).get("sunucular", [])

    for s in sunucular:
        for proje in s.get("projeler", []):
            proje_dizini = proje.get("dizin")
            if proje_dizini and dizin.startswith(proje_dizini):
                return s, proje
    return None, None


def ozet(yol=None):
    harita = yukle(yol)
    satirlar = ["Sunucu haritası", ""]

    sunucular = harita.get("sunucular", [])
    if not sunucular:
        satirlar.append("  Kayıtlı sunucu yok.")
        return "\n".join(satirlar)

    for sunucu in sunucular:
        satirlar.append(f"  {sunucu.get('ad')}  ({sunucu.get('adres')})")
        if sunucu.get("aciklama"):
            satirlar.append(f"    {sunucu['aciklama']}")

        projeler = sunucu.get("projeler", [])
        satirlar.append(f"    Projeler ({len(projeler)}):")
        for proje in projeler:
            satirlar.append(f"      - {proje.get('ad')}  →  {proje.get('dizin')}")
            if proje.get("alan_adi"):
                satirlar.append(f"        alan adı  : {proje['alan_adi']}")
            if proje.get("veritabani"):
                satirlar.append(f"        veritabanı: {proje['veritabani']}")
            if proje.get("musteri") and proje["musteri"] != "-":
                satirlar.append(f"        müşteri   : {proje['musteri']}")

        ortak = sunucu.get("ortak_izinli_dizinler", [])
        if ortak:
            satirlar.append(f"    Ortak izinli dizinler: {', '.join(ortak)}")
        satirlar.append("")

    satirlar.append(f"  Korunan kök dizinler: {', '.join(korunan_kokler(yol))}")
    return "\n".join(satirlar)


def main():
    if len(sys.argv) > 1:
        dizin = sys.argv[1]
        sunucu, proje = proje_bul(dizin)
        if proje:
            print(f"Dizin  : {dizin}")
            print(f"Sunucu : {sunucu.get('ad')} ({sunucu.get('adres')})")
            print(f"Proje  : {proje.get('ad')}")
            print(f"Alan adı: {proje.get('alan_adi') or '-'}")
            print(f"Veritabanı: {proje.get('veritabani') or '-'}")
        else:
            print(f"Bu dizin haritada kayıtlı değil: {dizin}")
            return 1
        return 0

    print(ozet())
    return 0


if __name__ == "__main__":
    sys.exit(main())
