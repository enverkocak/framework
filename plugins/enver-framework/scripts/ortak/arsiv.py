#!/usr/bin/env python3
"""Arsivleme motoru - hicbir veri silinmez, her sey notuyla saklanir.

Kurallar:
  1. Silme yerine arsivleme yapilir.
  2. Her arsiv klasorunde NEDEN.md bulunur: ne, neden, ne zaman, sonuc.
  3. Arsiv INDEX.md ile listelenir, aranabilir kalir.
  4. Ayni gun ayni ada ikinci kayit gelirse numaralanir, ustune yazilmaz.

Kullanim (komut satiri):
    python arsiv.py <kaynak> "<is adi>" "<neden>"

Gelistirici: Enver KOCAK
"""

import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yollar

INDEX_ADI = "INDEX.md"
NOT_ADI = "NEDEN.md"


def _slug(metin):
    """Klasor adina uygun sade metin uret (Turkce harfler sadelestirilir)."""
    donusum = {
        "ç": "c", "Ç": "c", "ğ": "g", "Ğ": "g", "ı": "i", "I": "i",
        "İ": "i", "ö": "o", "Ö": "o", "ş": "s", "Ş": "s", "ü": "u", "Ü": "u",
    }
    for eski, yeni in donusum.items():
        metin = metin.replace(eski, yeni)

    metin = metin.lower()
    metin = re.sub(r"[^a-z0-9]+", "-", metin)
    return metin.strip("-")[:60] or "isimsiz"


def _bugun():
    return datetime.now().strftime("%Y-%m-%d")


def _saat():
    return datetime.now().strftime("%H:%M")


def hedef_klasor(is_adi, arsiv_kok=None):
    """Cakismayan bir arsiv klasoru yolu uret."""
    kok = Path(arsiv_kok or yollar.arsiv_dizini())
    temel = f"{_bugun()}_{_slug(is_adi)}"

    aday = kok / temel
    sayac = 2
    while aday.exists():
        aday = kok / f"{temel}-{sayac}"
        sayac += 1

    return aday


def not_yaz(klasor, is_adi, neden, kaynak, sonuc=None):
    """Arsiv klasorune NEDEN.md yaz."""
    satirlar = [
        "# Arşiv notu",
        "",
        f"**İş:** {is_adi}",
        f"**Tarih:** {_bugun()} {_saat()}",
        f"**Kaynak:** `{kaynak}`",
        "",
        "## Neden arşivlendi",
        neden.strip() or "Belirtilmedi.",
        "",
    ]

    if sonuc:
        satirlar += ["## Sonuç", sonuc.strip(), ""]

    satirlar += [
        "## Kural",
        "Hiçbir veri silinmez. İşi biten her şey notuyla arşivlenir.",
        "Gerektiğinde buradan geri alınabilir.",
        "",
    ]

    (klasor / NOT_ADI).write_text("\n".join(satirlar), encoding="utf-8")


def index_guncelle(arsiv_kok=None):
    """Arsiv kokune INDEX.md yaz - butun arsiv kayitlarini listeler."""
    kok = Path(arsiv_kok or yollar.arsiv_dizini())

    kayitlar = []
    for klasor in sorted(kok.iterdir(), reverse=True):
        if not klasor.is_dir():
            continue

        not_yolu = klasor / NOT_ADI
        is_adi = klasor.name
        neden = "-"

        if not_yolu.is_file():
            icerik = not_yolu.read_text(encoding="utf-8", errors="ignore")

            eslesme = re.search(r"\*\*İş:\*\*\s*(.+)", icerik)
            if eslesme:
                is_adi = eslesme.group(1).strip()

            bolum = re.search(r"## Neden arşivlendi\s*\n(.+)", icerik)
            if bolum:
                neden = bolum.group(1).strip()[:90]

        tarih = klasor.name[:10]
        kayitlar.append((tarih, klasor.name, is_adi, neden))

    satirlar = [
        "# Arşiv dizini",
        "",
        f"Toplam kayıt: **{len(kayitlar)}**  ·  Son güncelleme: {_bugun()} {_saat()}",
        "",
        "| Tarih | Klasör | İş | Neden |",
        "|-------|--------|----|-------|",
    ]

    for tarih, klasor_adi, is_adi, neden in kayitlar:
        satirlar.append(f"| {tarih} | `{klasor_adi}` | {is_adi} | {neden} |")

    satirlar += [
        "",
        "---",
        "",
        "Bu dizin otomatik üretilir. Hiçbir kayıt silinmez.",
        "",
    ]

    (kok / INDEX_ADI).write_text("\n".join(satirlar), encoding="utf-8")
    return len(kayitlar)


def arsivle(kaynak, is_adi, neden, sonuc=None, arsiv_kok=None, tasi=True):
    """Bir dosya veya klasoru arsive al.

    tasi=True  : kaynak tasinir (silme yerine gecer)
    tasi=False : kaynak yerinde kalir, kopyasi arsivlenir
    """
    kaynak_yolu = Path(kaynak)
    if not kaynak_yolu.exists():
        raise FileNotFoundError(f"Kaynak bulunamadı: {kaynak}")

    klasor = hedef_klasor(is_adi, arsiv_kok)
    klasor.mkdir(parents=True, exist_ok=True)

    hedef = klasor / kaynak_yolu.name

    if tasi:
        shutil.move(str(kaynak_yolu), str(hedef))
    elif kaynak_yolu.is_dir():
        shutil.copytree(str(kaynak_yolu), str(hedef))
    else:
        shutil.copy2(str(kaynak_yolu), str(hedef))

    not_yaz(klasor, is_adi, neden, str(kaynak_yolu), sonuc)
    index_guncelle(arsiv_kok)

    return klasor


def main():
    if len(sys.argv) < 4:
        print("Kullanım: python arsiv.py <kaynak> \"<iş adı>\" \"<neden>\"")
        return 1

    kaynak, is_adi, neden = sys.argv[1], sys.argv[2], sys.argv[3]

    try:
        klasor = arsivle(kaynak, is_adi, neden)
    except (OSError, FileNotFoundError) as hata:
        print(f"Hata: {hata}")
        return 1

    print(f"Arşivlendi: {klasor}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
