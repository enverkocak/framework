#!/usr/bin/env python3
"""Sürüm yükseltme - tek komutla altı yeri birden günceller.

Sürüm numarası altı dosyada geçiyordu: plugin.json, marketplace.json,
ikisinin .ornek kopyası ve iki README. Elle değiştirince biri unutulur;
faz0 testi de o tutarsızlığı yakalayıp kapıyı kapatırdı. Bu araç hepsini
aynı anda yükseltir ve DEGISIKLIKLER.md'ye tarihli bir başlık açar.

Anlamsal sürümleme (BÜYÜK.ORTA.KÜÇÜK):
    kucuk   Hata düzeltme, küçük ekleme        2.13.0 -> 2.13.1
    orta    Yeni özellik, geriye uyumlu        2.13.0 -> 2.14.0
    buyuk   Kırıcı değişim, büyük yeniden yapı  2.13.0 -> 3.0.0

Kullanım:
    python surum.py                 # şu anki sürüm
    python surum.py yukselt kucuk   # (orta / buyuk)

Yükseltme SADECE dosyaları hazırlar; commit ve push senin kararın.
DEGISIKLIKLER'e açılan başlığı doldurmadan yayınlama - "neden" olmadan
geçmiş öğretici değildir.

Geliştirici: Enver KOCAK
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

for _akis in (sys.stdout, sys.stderr):
    if hasattr(_akis, "reconfigure"):
        _akis.reconfigure(encoding="utf-8", errors="replace")

# scripts/surum.py -> parents[2] = plugins, parents[3] = depo kökü
KOK = Path(__file__).resolve().parents[3]

# Sürümün geçtiği dosyalar ve nasıl değiştirileceği.
# Tür: "json" -> "version" alanı, "baslik" -> ilk satırdaki vX.Y.Z
SURUM_YERLERI = [
    (KOK / "plugins" / ".claude-plugin" / "plugin.json", "json"),
    (KOK / "plugins" / ".claude-plugin" / "marketplace.json", "json"),
    (KOK / "plugins" / ".claude-plugin" / "plugin.ornek.json", "json"),
    (KOK / "plugins" / ".claude-plugin" / "marketplace.ornek.json", "json"),
    (KOK / "plugins" / "enver-framework" / ".claude-plugin" / "plugin.json", "json"),
    (KOK / ".claude-plugin" / "marketplace.json", "json"),
    (KOK / "README.md", "readme"),
    (KOK / "README.ornek.md", "readme"),
    (KOK / "README.en.md", "readme"),
]

DEGISIKLIKLER = KOK / "DEGISIKLIKLER.md"

# Tek grup = tam sürüm ("2.14.0"). Başında \b YOK: başlıkta "v2.14.0" diye
# geçiyor, 'v' de rakam da kelime karakteri olduğundan \b\d eşleşmezdi.
SURUM_DESENI = re.compile(r"(\d+\.\d+\.\d+)")


def su_anki_surum():
    """plugin.json'daki sürümü döndür - tek doğruluk kaynağı."""
    plugin = KOK / "plugins" / ".claude-plugin" / "plugin.json"
    m = re.search(r'"version"\s*:\s*"(\d+\.\d+\.\d+)"',
                  plugin.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def sonraki_surum(mevcut, tur):
    buyuk, orta, kucuk = (int(p) for p in mevcut.split("."))
    if tur == "buyuk":
        return f"{buyuk + 1}.0.0"
    if tur == "orta":
        return f"{buyuk}.{orta + 1}.0"
    if tur == "kucuk":
        return f"{buyuk}.{orta}.{kucuk + 1}"
    raise ValueError(tur)


def _json_degistir(metin, yeni):
    """JSON dosyasındaki "version" alanlarını yeni sürüme çeker.

    Değeri değiştirir, biçimi bozmaz (yeniden serialize etmez).
    """
    return re.sub(r'("version"\s*:\s*")\d+\.\d+\.\d+(")',
                  rf"\g<1>{yeni}\g<2>", metin)


def _readme_degistir(metin, yeni):
    """README'deki bütün X.Y.Z sürümlerini yeniye çeker.

    Sürüm README'de iki yerde geçebiliyor: başlıkta (vX.Y.Z) ve rozet
    URL'inde (sürüm-X.Y.Z). İkisini de aynı anda güncellemek için hepsini
    değiştiririz. README'de üç parçalı başka bir sürüm numarası yok
    (Python "3.9" iki parçalı, desene uymaz), o yüzden güvenli."""
    return SURUM_DESENI.sub(yeni, metin)


def dosyalari_yukselt(yeni):
    degisen = []
    atlanan = []
    for yol, tur in SURUM_YERLERI:
        if not yol.is_file():
            atlanan.append(yol.name)
            continue
        metin = yol.read_text(encoding="utf-8")
        yeni_metin = (_json_degistir if tur == "json" else _readme_degistir)(metin, yeni)
        if yeni_metin != metin:
            yol.write_text(yeni_metin, encoding="utf-8", newline="\n")
            degisen.append(yol.name)
    return degisen, atlanan


def degisiklik_basligi_ac(yeni):
    """DEGISIKLIKLER.md'nin başına tarihli boş bir sürüm başlığı ekler."""
    if not DEGISIKLIKLER.is_file():
        return False
    metin = DEGISIKLIKLER.read_text(encoding="utf-8")

    bugun = datetime.now().strftime("%Y-%m-%d")
    yeni_bolum = (
        f"## {yeni} — <başlığı yaz>\n\n"
        f"<{bugun}> Ne değişti ve NEDEN değişti - burayı doldur.\n"
        f"\"Ne\" olmadan geçmiş anlamsız, \"neden\" olmadan öğretici değil.\n\n"
    )

    # İlk "## " başlığından hemen önce ekle (en yeni sürüm en üstte durur).
    imza = "\n## "
    yer = metin.find(imza)
    if yer == -1:
        yeni_metin = metin.rstrip() + "\n\n" + yeni_bolum
    else:
        yeni_metin = metin[:yer + 1] + yeni_bolum + metin[yer + 1:]

    DEGISIKLIKLER.write_text(yeni_metin, encoding="utf-8", newline="\n")
    return True


def tutarli_mi():
    """Altı yerdeki sürüm aynı mı? Yayın öncesi güvenlik ağı."""
    bulunan = {}
    for yol, tur in SURUM_YERLERI:
        if not yol.is_file():
            continue
        metin = yol.read_text(encoding="utf-8")
        if tur == "json":
            m = re.search(r'"version"\s*:\s*"(\d+\.\d+\.\d+)"', metin)
        else:
            # README'de sürüm ilk satırda değil (orada dil geçişi var);
            # rozette ya da başlıkta. Tüm dosyada ilk X.Y.Z'yi al.
            m = SURUM_DESENI.search(metin)
        bulunan[yol.name] = m.group(1) if m else "YOK"
    benzersiz = set(bulunan.values())
    return len(benzersiz) == 1, bulunan


def komut_durum():
    mevcut = su_anki_surum()
    print(f"Şu anki sürüm: {mevcut}")
    tutarli, bulunan = tutarli_mi()
    if tutarli:
        print("Bütün dosyalar tutarlı.")
        return 0
    print("UYARI: Sürümler tutarsız:")
    for ad, s in bulunan.items():
        print(f"  {s:10} {ad}")
    return 1


def komut_yukselt(tur):
    mevcut = su_anki_surum()
    if not mevcut:
        print("Şu anki sürüm okunamadı (plugin.json).")
        return 1

    yeni = sonraki_surum(mevcut, tur)
    print(f"Sürüm: {mevcut} -> {yeni}  ({tur})")
    print()

    degisen, atlanan = dosyalari_yukselt(yeni)
    print(f"{len(degisen)} dosya güncellendi:")
    for ad in degisen:
        print(f"  {ad}")
    if atlanan:
        print(f"Bulunamayan (atlandı): {', '.join(atlanan)}")

    if degisiklik_basligi_ac(yeni):
        print()
        print("DEGISIKLIKLER.md'ye taslak başlık eklendi - DOLDUR.")

    tutarli, bulunan = tutarli_mi()
    print()
    if tutarli:
        print(f"Tutarlılık: TAMAM (hepsi {yeni})")
    else:
        print("UYARI: hâlâ tutarsız:")
        for ad, s in bulunan.items():
            print(f"  {s:10} {ad}")
        return 1

    print()
    print("Sırada (sen yaparsın):")
    print("  1. DEGISIKLIKLER.md başlığını doldur")
    print("  2. Testi çalıştır: tumunu-calistir.sh")
    print("  3. commit + push")
    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Sürüm yükseltme")
    alt = ayristirici.add_subparsers(dest="komut")
    yuk = alt.add_parser("yukselt", help="Sürümü yükselt")
    yuk.add_argument("tur", choices=["kucuk", "orta", "buyuk"])
    alt.add_parser("durum", help="Şu anki sürüm ve tutarlılık")

    args = ayristirici.parse_args()

    if args.komut == "yukselt":
        return komut_yukselt(args.tur)
    return komut_durum()


if __name__ == "__main__":
    sys.exit(main())
