#!/usr/bin/env python3
"""Hafızaya test sızıntısı var mı - kapı testlerinin gerileme koruması.

NEDEN VAR
Kapı testleri görev, karar, hata ve cihaz kaydı üretir. Bir dönem bu
kayıtlar gerçek hafızaya yazıldı: açılış brifingi "Kapi testi olayi"
satırlarıyla doldu, gerçek işler o gürültünün altında kaldı.

Testler artık kum havuzuna yazıyor (_kumhavuzu.sh). Bu denetim, yeni
yazılan bir testin havuzu atlamasını yakalar - düzeltmenin kendisi değil,
düzeltmenin bozulmadığının ölçüsüdür.

KESKİNLİK
Aranan şey "kapı testi" ifadesi DEĞİL, testlerin kullandığı kayıt
imzalarıdır. Gerçek bir oturum özeti "kapı testleri geçti" diye yazabilir;
bu ihlal değildir. Sürekli yanlış öten bir denetim okunmaz hale gelir.

Yeni test verisi eklersen imzasını aşağıdaki listelere ekle.

Kullanım:
    python sizinti-kontrol.py [proje_koku]

Çıkış kodu 0 temiz, 1 sızıntı var.

Geliştirici: Enver KOCAK
"""

import json
import sys
from pathlib import Path

# Belge defterlerinde geçmemesi gereken kayıt başlıkları ve gövdeleri
BELGE_IMZALARI = [
    "Kapi testi olayi",
    "Kapi testi karari",
    "Kapi testi hatasi belirtisi",
    "Test amacli kayit.",
]

# Kayıt dosyalarında test verisini belli eden alan değerleri
KAYIT_IMZALARI = {
    "proje": ("kapi-testi",),
    "musteri": ("Kapi Testi Musterisi",),
    "baslik": ("Kapi testi gorevi", "Gecici acil kapi testi"),
    "ad": ("Kapi testi kamerasi", "Bakimi gecmis cihaz", "Sizinti testi"),
}

# proje ve musteri alanlari ON EK ile eslesir: "kapi-testi-siralama",
# "kapi-testi-kesif" gibi turevler tek tek sayilmasin diye.
ON_EK_ALANLARI = ("proje", "musteri")

# Denetlenen alan: paylaşılan hafıza. Günlük makineye özeldir, depoya girmez.
DENETLENEN_DIZIN = "hafiza"


def belge_tara(yol):
    """Markdown defterinde test imzası taşıyan satırları bul."""
    bulunanlar = []
    try:
        satirlar = yol.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return bulunanlar

    for sira, satir in enumerate(satirlar, 1):
        for imza in BELGE_IMZALARI:
            if imza in satir:
                bulunanlar.append((sira, satir.strip()))
                break

    return bulunanlar


def kayit_tara(yol):
    """JSON kaydında test verisi taşıyan girdileri bul."""
    bulunanlar = []
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return bulunanlar

    for girdi in girdileri_gez(veri):
        for alan, degerler in KAYIT_IMZALARI.items():
            deger = str(girdi.get(alan, ""))
            if not deger:
                continue
            if alan in ON_EK_ALANLARI:
                eslesti = deger.startswith(degerler)
            else:
                eslesti = deger in degerler
            if eslesti:
                bulunanlar.append(girdi)
                break

    return bulunanlar


def girdileri_gez(veri):
    """İç içe yapıdaki sözlük kayıtlarını tek tek ver."""
    if isinstance(veri, dict):
        # Kaydın kendisi mi, yoksa liste taşıyan kap mı?
        if any(alan in veri for alan in KAYIT_IMZALARI):
            yield veri
        for deger in veri.values():
            yield from girdileri_gez(deger)
    elif isinstance(veri, list):
        for deger in veri:
            yield from girdileri_gez(deger)


def denetle(kok):
    """Hafızayı tara, bulunan sızıntıları yaz, sayıyı döndür."""
    hafiza_dizini = Path(kok) / DENETLENEN_DIZIN
    if not hafiza_dizini.is_dir():
        print(f"Hafıza dizini yok: {hafiza_dizini}")
        return 0

    toplam = 0

    for yol in sorted(hafiza_dizini.rglob("*.md")):
        bulunanlar = belge_tara(yol)
        if bulunanlar:
            toplam += len(bulunanlar)
            bagil = yol.relative_to(kok)
            print(f"  {bagil}: {len(bulunanlar)} test satırı")
            for sira, satir in bulunanlar[:3]:
                print(f"      satır {sira}: {satir[:70]}")

    for yol in sorted(hafiza_dizini.rglob("*.json")):
        bulunanlar = kayit_tara(yol)
        if bulunanlar:
            toplam += len(bulunanlar)
            bagil = yol.relative_to(kok)
            print(f"  {bagil}: {len(bulunanlar)} test kaydı")
            for girdi in bulunanlar[:3]:
                etiket = girdi.get("baslik") or girdi.get("ad") or girdi
                print(f"      {str(etiket)[:70]}")

    return toplam


def main():
    kok = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

    print("HAFIZAYA TEST SIZINTISI DENETİMİ")
    print("-" * 40)

    toplam = denetle(kok)

    print("-" * 40)
    if toplam:
        print(f"SIZINTI VAR: {toplam} test kaydı gerçek hafızada.")
        print("Kapı testleri kum havuzuna yazmalı: _kumhavuzu.sh")
        return 1

    print("Temiz: gerçek hafızada test kaydı yok.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
