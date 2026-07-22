#!/usr/bin/env python3
"""Framework ayarlari - okuma ve yazma.

Ayarlar iki katmanda tutulur:
  1. Kullanici katmani : ~/.claude/enver/ayarlar.json  (butun projeler icin gecerli)
  2. Proje katmani     : <proje>/.claude/enver-ayarlar.json  (o projeye ozel, ustun gelir)

Gelistirici: Enver KOCAK
"""

import os
import json
from pathlib import Path

VARSAYILAN_AYARLAR = {
    "dil": "tr",
    "calisma_modu": "dikkatli",
    "tam_yetki": False,
    "arsiv_kok": None,
    "makine_adi": None,
}

KULLANICI_AYAR_YOLU = Path.home() / ".claude" / "enver" / "ayarlar.json"
PROJE_AYAR_ADI = "enver-ayarlar.json"


def _guvenli_oku(yol):
    """JSON dosyasini oku, okunamazsa bos sozluk dondur."""
    try:
        with open(yol, "r", encoding="utf-8") as dosya:
            veri = json.load(dosya)
        return veri if isinstance(veri, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def proje_ayar_yolu(proje_kok):
    """Proje katmanindaki ayar dosyasinin yolu."""
    return Path(proje_kok) / ".claude" / PROJE_AYAR_ADI


def oku(proje_kok=None):
    """Butun katmanlari birlestirip etkin ayarlari dondur.

    Oncelik: varsayilan < kullanici < proje
    """
    ayarlar = dict(VARSAYILAN_AYARLAR)
    ayarlar.update(_guvenli_oku(KULLANICI_AYAR_YOLU))

    if proje_kok:
        ayarlar.update(_guvenli_oku(proje_ayar_yolu(proje_kok)))

    return ayarlar


def yaz(yeni_degerler, proje_kok=None):
    """Ayarlari kaydet.

    proje_kok verilirse proje katmanina, verilmezse kullanici katmanina yazar.
    """
    if proje_kok:
        hedef = proje_ayar_yolu(proje_kok)
    else:
        hedef = KULLANICI_AYAR_YOLU

    hedef.parent.mkdir(parents=True, exist_ok=True)

    mevcut = _guvenli_oku(hedef)
    mevcut.update(yeni_degerler)

    with open(hedef, "w", encoding="utf-8") as dosya:
        json.dump(mevcut, dosya, ensure_ascii=False, indent=2)
        dosya.write("\n")

    return hedef


VARSAYILAN_KIMLIK = {
    "gelistirici": "",
    "site": "",
    "eposta": "",
    "telefon": "",
    "sirket": "",
}


def kimlik(proje_kok=None):
    """Gelistirici kimligi.

    Koda gomulmez; kurulum sirasinda kaydedilir. Boylece framework'u
    baskasi kullandiginda kendi bilgisi gorunur.
    """
    kayit = dict(VARSAYILAN_KIMLIK)
    kayit.update(oku(proje_kok).get("kimlik", {}) or {})
    return kayit


def kimlik_satiri(proje_kok=None):
    """Belgelerde kullanilacak tek satirlik kimlik."""
    k = kimlik(proje_kok)
    parcalar = [k.get("gelistirici"), k.get("site"), k.get("eposta")]
    dolu = [p for p in parcalar if p]
    return " | ".join(dolu) if dolu else "(kimlik tanimli degil)"


def dil_kodu(proje_kok=None):
    """Etkin dil kodunu dondur."""
    return oku(proje_kok).get("dil", "tr")


if __name__ == "__main__":
    import sys

    kok = sys.argv[1] if len(sys.argv) > 1 else None
    print(json.dumps(oku(kok), ensure_ascii=False, indent=2))
