#!/usr/bin/env python3
"""Arşivleme motoru - hiçbir veri silinmez, her şey notuyla saklanır.

Kurallar:
  1. Silme yerine arşivleme yapılır.
  2. Her arşiv klasöründe NEDEN.md bulunur: ne, neden, ne zaman, sonuç.
  3. Arşiv INDEX.md ile listelenir, aranabilir kalır.
  4. Aynı gün aynı ada ikinci kayıt gelirse numaralanır, üstüne yazılmaz.

Kullanım (komut satırı):
    python arşiv.py <kaynak> "<iş adı>" "<neden>"

Geliştirici: Enver KOCAK
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
    """Klasör adına uygun sade metin üret (Türkçe harfler sadeleştirilir)."""
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
    """Çakışmayan bir arşiv klasörü yolu üret."""
    kok = Path(arsiv_kok or yollar.arsiv_dizini())
    temel = f"{_bugun()}_{_slug(is_adi)}"

    aday = kok / temel
    sayac = 2
    while aday.exists():
        aday = kok / f"{temel}-{sayac}"
        sayac += 1

    return aday


def not_yaz(klasor, is_adi, neden, kaynak, sonuc=None):
    """Arşiv klasörüne NEDEN.md yaz."""
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
    """Arşiv köküne INDEX.md yaz - bütün arşiv kayıtlarını listeler."""
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
    """Bir dosya veya klasörü arşive al.

    taşı=True  : kaynak taşınır (silme yerine geçer)
    taşı=False : kaynak yerinde kalır, kopyası arşivlenir
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
