#!/usr/bin/env python3
"""Kancaların ortak betik katmanını bulmasını sağlar.

Kancalar hem depo düzeninde hem kurulu düzende çalışır; ikisinde de
betikler ../plugins/enver-framework/scripts/ altındadır. Ortam değişkeni
verilmişse önce ona bakılır.

Geliştirici: Enver KOCAK
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
    """Betik katmanının yolunu döndür, bulunamazsa None."""
    for aday in _adaylar():
        if (aday / "ortak" / "metin.py").is_file():
            return aday
    return None


def hazirla():
    """Ortak betikleri içeri aktarılabilir hale getir.

    Başarılı olursa True döner. Betikler bulunamazsa kanca yine de
    çalışmalı - o yüzden False dönüp sessizce geçilir.
    """
    dizin = betik_dizini()
    if dizin is None:
        return False

    ortak = str(dizin / "ortak")
    if ortak not in sys.path:
        sys.path.insert(0, ortak)
    return True
