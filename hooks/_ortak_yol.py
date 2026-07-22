#!/usr/bin/env python3
"""Kancalarin ortak betik katmanini bulmasini saglar.

Kancalar hem depo duzeninde hem kurulu duzende calisir; ikisinde de
betikler ../plugins/enver-framework/scripts/ altindadir. Ortam degiskeni
verilmisse once ona bakilir.

Gelistirici: Enver KOCAK
"""

import os
import sys
from pathlib import Path

KANCA_DIZINI = Path(__file__).resolve().parent


def _adaylar():
    eklenti_koku = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if eklenti_koku:
        yield Path(eklenti_koku) / "scripts"

    yield KANCA_DIZINI.parent / "plugins" / "enver-framework" / "scripts"
    yield KANCA_DIZINI.parent / "scripts"


def betik_dizini():
    """Betik katmaninin yolunu dondur, bulunamazsa None."""
    for aday in _adaylar():
        if (aday / "ortak" / "metin.py").is_file():
            return aday
    return None


def hazirla():
    """Ortak betikleri iceri aktarilabilir hale getir.

    Basarili olursa True doner. Betikler bulunamazsa kanca yine de
    calismali - o yuzden False donup sessizce gecilir.
    """
    dizin = betik_dizini()
    if dizin is None:
        return False

    ortak = str(dizin / "ortak")
    if ortak not in sys.path:
        sys.path.insert(0, ortak)
    return True
