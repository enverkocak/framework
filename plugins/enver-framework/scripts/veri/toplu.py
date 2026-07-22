#!/usr/bin/env python3
"""Toplu dosya işlemleri.

Yüzlerce dosyada aynı işi elle yapmak hem uzun sürer hem hata üretir.

Tasarım kararı: her işlem önce **deneme** olarak çalışır. Ne yapılacağı
gösterilir, onaylanırsa uygulanır. Yüz dosyayı yanlış adlandırmak, yüz
dosyayı doğru adlandırmaktan çok daha kolaydır.

Kaynak dosyalar değiştirilmeden önce yedeklenir; hiçbir işlem tek yönlü değildir.

İşlemler:
    adlandır    Dosya adlarını düzenle (Türkçe karakter, boşluk, büyük harf)
    taşı        Uzantıya göre klasörlere ayır
    listele     Klasördeki dosyaları türlerine göre say

Geliştirici: Enver KOCAK
"""

import argparse
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "sunucu"))

import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

TURKCE_DONUSUM = str.maketrans({
    "ç": "c", "Ç": "C", "ğ": "g", "Ğ": "G", "ı": "i", "İ": "I",
    "ö": "o", "Ö": "O", "ş": "s", "Ş": "S", "ü": "u", "Ü": "U",
})

TUR_KLASORLERI = {
    "gorsel": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico"},
    "belge": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".md"},
    "video": {".mp4", ".webm", ".avi", ".mov", ".mkv"},
    "ses": {".mp3", ".wav", ".ogg", ".m4a"},
    "arsiv": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "kod": {".js", ".ts", ".py", ".php", ".css", ".html", ".json", ".xml"},
}


def sade_ad(ad, kucuk=True, tire=True):
    """Dosya adını sunucuda ve adres çubuğunda sorun çıkarmayacak hâle getir."""
    kok = Path(ad).stem
    uzanti = Path(ad).suffix.lower()

    kok = kok.translate(TURKCE_DONUSUM)

    if kucuk:
        kok = kok.lower()

    if tire:
        kok = re.sub(r"[\s_]+", "-", kok)

    kok = re.sub(r"[^A-Za-z0-9\-.]", "", kok)
    kok = re.sub(r"-{2,}", "-", kok).strip("-.")

    return f"{kok or 'dosya'}{uzanti}"


def _dosyalar(hedef, desen="*", ic_ice=False):
    hedef = Path(hedef)
    if not hedef.is_dir():
        return []

    ogeler = hedef.rglob(desen) if ic_ice else hedef.glob(desen)
    return sorted(y for y in ogeler if y.is_file())


def adlandirma_plani(hedef, desen="*", ic_ice=False, kucuk=True, tire=True):
    """Hangi dosya nasıl adlandırılacak - henüz uygulamadan."""
    plan = []
    hedefler = set()

    for yol in _dosyalar(hedef, desen, ic_ice):
        yeni = sade_ad(yol.name, kucuk, tire)

        if yeni == yol.name:
            continue

        # Aynı ada iki dosya düşerse ayır
        aday = yol.parent / yeni
        sayac = 2
        while aday in hedefler or (aday.exists() and aday != yol):
            kok = Path(yeni).stem
            uzanti = Path(yeni).suffix
            aday = yol.parent / f"{kok}-{sayac}{uzanti}"
            sayac += 1

        hedefler.add(aday)
        plan.append((yol, aday))

    return plan


def tasima_plani(hedef, ic_ice=False):
    """Hangi dosya hangi tür klasörüne taşınacak."""
    hedef = Path(hedef)
    plan = []

    for yol in _dosyalar(hedef, "*", ic_ice):
        uzanti = yol.suffix.lower()

        tur = "diger"
        for ad, uzantilar in TUR_KLASORLERI.items():
            if uzanti in uzantilar:
                tur = ad
                break

        yeni = hedef / tur / yol.name
        if yeni != yol:
            plan.append((yol, yeni))

    return plan


def uygula(plan, yedek_al=True, neden=""):
    """Planı uygula. Önce yedek alınır."""
    if not plan:
        return 0, None

    yedek_yolu = None
    if yedek_al:
        import yedek as yedek_modulu
        kaynak = plan[0][0].parent
        yedek_yolu, _ = yedek_modulu.al(
            kaynak, neden or "Toplu dosya işlemi öncesi yedek",
            etiket=f"toplu-{kaynak.name}")

    uygulanan = 0
    for eski, yeni in plan:
        try:
            yeni.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(eski), str(yeni))
            uygulanan += 1
        except OSError:
            continue

    return uygulanan, yedek_yolu


def _plan_yazdir(plan, hedef, sinir):
    for eski, yeni in plan[:sinir]:
        try:
            eski_ad = eski.relative_to(hedef)
            yeni_ad = yeni.relative_to(hedef)
        except ValueError:
            eski_ad, yeni_ad = eski.name, yeni.name
        print(f"  {eski_ad}")
        print(f"    → {yeni_ad}")

    if len(plan) > sinir:
        print(f"  ... ve {len(plan) - sinir} dosya daha")


# ---------------------------------------------------------------- komutlar

def komut_adlandir(args):
    hedef = Path(args.klasor)

    if not hedef.is_dir():
        print(f"Klasör bulunamadı: {hedef}")
        return 1

    plan = adlandirma_plani(hedef, args.desen, args.ic_ice,
                            not args.buyuk_kalsin, not args.alt_cizgi)

    print(f"TOPLU ADLANDIRMA - {hedef}")
    print("=" * 66)
    print()

    if not plan:
        print("Değiştirilecek dosya adı yok. Hepsi zaten uygun.")
        return 0

    print(f"{len(plan)} dosya adı değişecek:")
    print()
    _plan_yazdir(plan, hedef, args.sinir)

    if not args.onayla:
        print()
        print("Bu bir DENEME. Uygulanmadı.")
        print("Uygulamak için --onayla ekle.")
        return 0

    uygulanan, yedek_yolu = uygula(plan, not args.yedegi_atla,
                                   f"Toplu adlandırma: {hedef.name}")

    print()
    print(f"{uygulanan} dosya adlandırıldı.")
    if yedek_yolu:
        print(f"Yedek: {yedek_yolu.name}")
        print(f"Geri dönmek için: python yedek.py geri {yedek_yolu.name} --onayla")

    return 0


def komut_tasi(args):
    hedef = Path(args.klasor)

    if not hedef.is_dir():
        print(f"Klasör bulunamadı: {hedef}")
        return 1

    plan = tasima_plani(hedef, args.ic_ice)

    print(f"TÜRE GÖRE AYIRMA - {hedef}")
    print("=" * 66)
    print()

    if not plan:
        print("Taşınacak dosya yok.")
        return 0

    sayilar = Counter(yeni.parent.name for _, yeni in plan)
    print("Oluşacak klasörler:")
    for klasor, sayi in sorted(sayilar.items()):
        print(f"  {klasor:<12} {sayi} dosya")

    print()
    _plan_yazdir(plan, hedef, args.sinir)

    if not args.onayla:
        print()
        print("Bu bir DENEME. Uygulanmadı.")
        print("Uygulamak için --onayla ekle.")
        return 0

    uygulanan, yedek_yolu = uygula(plan, not args.yedegi_atla,
                                   f"Türe göre ayırma: {hedef.name}")

    print()
    print(f"{uygulanan} dosya taşındı.")
    if yedek_yolu:
        print(f"Yedek: {yedek_yolu.name}")

    return 0


def komut_listele(args):
    hedef = Path(args.klasor)

    if not hedef.is_dir():
        print(f"Klasör bulunamadı: {hedef}")
        return 1

    dosyalar = _dosyalar(hedef, "*", args.ic_ice)

    if not dosyalar:
        print("Klasörde dosya yok.")
        return 0

    turler = Counter()
    boyutlar = Counter()
    sorunlu_adlar = []

    for yol in dosyalar:
        uzanti = yol.suffix.lower() or "(uzantısız)"
        turler[uzanti] += 1
        try:
            boyutlar[uzanti] += yol.stat().st_size
        except OSError:
            pass

        if sade_ad(yol.name) != yol.name:
            sorunlu_adlar.append(yol.name)

    print(f"KLASÖR ÖZETİ - {hedef}")
    print("=" * 66)
    print(f"{len(dosyalar)} dosya")
    print()
    print(f"  {'uzantı':<14} {'adet':>6}  {'boyut':>10}")
    print("  " + "-" * 34)

    for uzanti, sayi in turler.most_common(15):
        boyut = boyutlar[uzanti] / 1024
        birim = "KB"
        if boyut > 1024:
            boyut /= 1024
            birim = "MB"
        print(f"  {uzanti:<14} {sayi:>6}  {boyut:>7.1f} {birim}")

    if sorunlu_adlar:
        print()
        print(f"{len(sorunlu_adlar)} dosya adı sorun çıkarabilir "
              f"(Türkçe karakter, boşluk ya da büyük harf):")
        for ad in sorunlu_adlar[:8]:
            print(f"  {ad}  →  {sade_ad(ad)}")
        print()
        print("Düzeltmek için: python toplu.py adlandir <klasör>")

    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Toplu dosya işlemleri")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("adlandir", help="Dosya adlarını düzenle")
    p.add_argument("klasor")
    p.add_argument("--desen", default="*")
    p.add_argument("--ic-ice", action="store_true", dest="ic_ice")
    p.add_argument("--buyuk-kalsin", action="store_true", dest="buyuk_kalsin")
    p.add_argument("--alt-cizgi", action="store_true", dest="alt_cizgi")
    p.add_argument("--onayla", action="store_true")
    p.add_argument("--yedegi-atla", action="store_true", dest="yedegi_atla")
    p.add_argument("--sinir", type=int, default=15)
    p.set_defaults(islev=komut_adlandir)

    p = alt.add_parser("tasi", help="Türe göre klasörlere ayır")
    p.add_argument("klasor")
    p.add_argument("--ic-ice", action="store_true", dest="ic_ice")
    p.add_argument("--onayla", action="store_true")
    p.add_argument("--yedegi-atla", action="store_true", dest="yedegi_atla")
    p.add_argument("--sinir", type=int, default=15)
    p.set_defaults(islev=komut_tasi)

    p = alt.add_parser("listele", help="Klasör özeti")
    p.add_argument("klasor")
    p.add_argument("--ic-ice", action="store_true", dest="ic_ice")
    p.set_defaults(islev=komut_listele)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
