#!/usr/bin/env python3
"""Framework ayarları - okuma ve yazma.

Ayarlar iki katmanda tutulur:
  1. Kullanıcı katmanı : ~/.claude/enver/ayarlar.json  (bütün projeler için geçerli)
  2. Proje katmanı     : <proje>/.claude/enver-ayarlar.json  (o projeye özel, üstün gelir)

Geliştirici: Enver KOCAK
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
    """JSON dosyasını oku, okunamazsa boş sözlük döndür."""
    try:
        with open(yol, "r", encoding="utf-8") as dosya:
            veri = json.load(dosya)
        return veri if isinstance(veri, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def proje_ayar_yolu(proje_kok):
    """Proje katmanındaki ayar dosyasının yolu."""
    return Path(proje_kok) / ".claude" / PROJE_AYAR_ADI


def oku(proje_kok=None):
    """Bütün katmanları birleştirip etkin ayarları döndür.

    Öncelik: varsayılan < kullanıcı < proje
    """
    ayarlar = dict(VARSAYILAN_AYARLAR)
    ayarlar.update(_guvenli_oku(KULLANICI_AYAR_YOLU))

    if proje_kok:
        ayarlar.update(_guvenli_oku(proje_ayar_yolu(proje_kok)))

    return ayarlar


def yaz(yeni_degerler, proje_kok=None):
    """Ayarları kaydet.

    proje_kök verilirse proje katmanına, verilmezse kullanıcı katmanına yazar.
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
    """Geliştirici kimliği.

    Koda gömülmez; kurulum sırasında kaydedilir. Böylece framework'u
    başkası kullandığında kendi bilgisi görünür.
    """
    kayit = dict(VARSAYILAN_KIMLIK)
    kayit.update(oku(proje_kok).get("kimlik", {}) or {})
    return kayit


def kimlik_satiri(proje_kok=None):
    """Belgelerde kullanılacak tek satırlık kimlik."""
    k = kimlik(proje_kok)
    parcalar = [k.get("gelistirici"), k.get("site"), k.get("eposta")]
    dolu = [p for p in parcalar if p]
    return " | ".join(dolu) if dolu else "(kimlik tanimli degil)"


def dil_kodu(proje_kok=None):
    """Etkin dil kodunu döndür."""
    return oku(proje_kok).get("dil", "tr")


if __name__ == "__main__":
    import sys

    kok = sys.argv[1] if len(sys.argv) > 1 else None
    print(json.dumps(oku(kok), ensure_ascii=False, indent=2))
