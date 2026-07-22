#!/usr/bin/env python3
"""Dil katmanı - kullanıcıya görünen bütün metinler buradan geçer.

Kullanım:
    from metin import al
    print(al("korumalar.engellendi"))

Kural: Hiçbir kullanıcı metni koda gömülmez. Hepsi diller/<kod>.json içinde durur.
Böylece yeni dil eklemek sadece bir dosya kopyalayıp çevirmek olur.

Geliştirici: Enver KOCAK
"""

import json
from pathlib import Path

import ayarlar

DILLER_DIZINI = Path(__file__).resolve().parent.parent.parent / "diller"
YEDEK_DIL = "tr"

_onbellek = {}


def _dil_yukle(kod):
    """Dil dosyasını yükle ve önbelleğe al."""
    if kod in _onbellek:
        return _onbellek[kod]

    yol = DILLER_DIZINI / f"{kod}.json"

    try:
        with open(yol, "r", encoding="utf-8") as dosya:
            veri = json.load(dosya)
    except (OSError, json.JSONDecodeError):
        if kod == YEDEK_DIL:
            veri = {}
        else:
            veri = _dil_yukle(YEDEK_DIL)

    _onbellek[kod] = veri
    return veri


def al(anahtar, proje_kok=None, **degerler):
    """Anahtara karşılık gelen metni döndür.

    anahtar : "korumalar.engellendi" gibi noktalı yol
    değerler: metindeki {yer_tutucu} alanlarını doldurur

    Metin bulunamazsa önce yedek dile bakılır, o da yoksa anahtar aynen döner.
    """
    kod = ayarlar.dil_kodu(proje_kok)

    metin = _derinden_al(_dil_yukle(kod), anahtar)

    if metin is None and kod != YEDEK_DIL:
        metin = _derinden_al(_dil_yukle(YEDEK_DIL), anahtar)

    if metin is None:
        return anahtar

    if degerler:
        try:
            return metin.format(**degerler)
        except (KeyError, IndexError):
            return metin

    return metin


def _derinden_al(sozluk, anahtar):
    """Noktalı yolla iç içe sözlükten değer çek."""
    parca = sozluk
    for ad in anahtar.split("."):
        if not isinstance(parca, dict) or ad not in parca:
            return None
        parca = parca[ad]
    return parca if isinstance(parca, str) else None


def mevcut_diller():
    """Kurulu dillerin listesini döndür."""
    if not DILLER_DIZINI.is_dir():
        return []

    sonuc = []
    for yol in sorted(DILLER_DIZINI.glob("*.json")):
        veri = _dil_yukle(yol.stem)
        sonuc.append({
            "kod": yol.stem,
            "ad": veri.get("dil_adi", yol.stem),
        })
    return sonuc


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        print(al(sys.argv[1]))
    else:
        print("Kurulu diller:")
        for dil in mevcut_diller():
            print(f"  {dil['kod']} - {dil['ad']}")
