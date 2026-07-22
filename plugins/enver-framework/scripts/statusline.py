#!/usr/bin/env python3
"""Durum satırı - ekranın altında sabit duran özet.

Gösterilenler:
    proje · makine · aktif faz · kasa durumu · maliyet

Makine adının görünmesi bilinçli: birden çok bilgisayarda çalışılıyor,
"hangi makinedeyim" sorusu her an cevaplı olmalı.

Girdi olarak oturum bilgisi bekler (standart girdiden JSON).
Bilgi gelmezse eksik alanlar sessizce atlanır - durum satırı asla hata vermez.

Geliştirici: Enver KOCAK
"""

import json
import os
import re
import sys
import time
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI / "ortak"))
sys.path.insert(0, str(SCRIPT_DIZINI / "hafiza"))
sys.path.insert(0, str(SCRIPT_DIZINI / "senkron"))

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

AYIRAC = "  ·  "


def _oturum_bilgisi():
    """Standart girdiden oturum bilgisini oku."""
    if sys.stdin.isatty():
        return {}
    try:
        return json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        return {}


def _proje_koku(bilgi):
    calisma = (bilgi.get("workspace") or {}).get("project_dir")
    return calisma or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _proje_adi(kok):
    try:
        import yollar
        return yollar.proje_adi(yollar.proje_kok(kok))
    except Exception:
        return Path(kok).name


def _makine_adi(kok):
    try:
        import makine
        kayit = makine.bu_makine(kok)
        if kayit:
            return kayit.get("ad")
        return makine.kimlik().split("/")[0]
    except Exception:
        return None


def _aktif_faz(kok):
    """Geliştirme notlarından sıradaki fazı oku."""
    aday = Path(kok) / "gelistirme-arastirmasi" / "00-DEVAM-BURADAN.md"
    if not aday.is_file():
        return None

    try:
        icerik = aday.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None

    eslesme = re.search(r"###\s*Siradaki:\s*(.+)", icerik)
    if eslesme:
        return eslesme.group(1).strip()[:34]
    return None


def _kasa_durumu():
    """Kasa açık mı kilitli mi, kalan süre ne kadar."""
    oturum_yolu = Path.home() / ".claude" / "enver" / "kasa-oturum.json"
    if not oturum_yolu.is_file():
        return "kasa kilitli"

    try:
        veri = json.loads(oturum_yolu.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "kasa kilitli"

    kalan = veri.get("bitis", 0) - time.time()
    if kalan <= 0:
        return "kasa kilitli"

    return f"kasa AÇIK ({int(kalan / 60)} dk)"


def _maliyet(bilgi):
    tutar = (bilgi.get("cost") or {}).get("total_cost_usd")
    if tutar is None:
        return None
    return f"${tutar:.2f}"


def _tam_yetki_acik_mi(kok):
    try:
        import ayarlar
        return bool(ayarlar.oku(kok).get("tam_yetki"))
    except Exception:
        return False


def main():
    bilgi = _oturum_bilgisi()
    kok = _proje_koku(bilgi)

    parcalar = [_proje_adi(kok)]

    makine_adi = _makine_adi(kok)
    if makine_adi:
        parcalar.append(makine_adi)

    faz = _aktif_faz(kok)
    if faz:
        parcalar.append(faz)

    parcalar.append(_kasa_durumu())

    if _tam_yetki_acik_mi(kok):
        parcalar.append("TAM YETKİ")

    tutar = _maliyet(bilgi)
    if tutar:
        parcalar.append(tutar)

    print(AYIRAC.join(p for p in parcalar if p))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Durum satırı hiçbir koşulda akışı bozmamalı
        print("Enver Framework")
        sys.exit(0)
