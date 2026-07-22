#!/usr/bin/env python3
"""Cihaz envanteri - kurulan sistemlerin kaydı.

Kamera, kayıt cihazı, ağ donanımı ve benzeri kurulumlar akılda tutulmaz.
Hangi müşteride ne var, nereye kuruldu, hangi adresle erişiliyor, ne zaman
kuruldu - hepsi burada durur.

ERİŞİM BİLGİSİ BURADA TUTULMAZ. Cihazın kullanıcı adı ve parolası kasada
durur; envanterdeki `kasa_anahtarı` alanı yalnızca kasadaki kaydı işaret eder.
Envanter dosyası paylaşılabilir olmalı, parola içeren bir dosya paylaşılamaz.

Kayıt `hafıza/cihaz-envanteri.json` içinde durur, makineler arasında senkron olur.

Komutlar:
    ekle       Cihaz kaydı ekle
    liste      Cihazları göster
    müşteri    Bir müşterinin bütün cihazları
    güncelle   Bir alanı güncelle
    bakım      Bakım tarihi gelen cihazlar

Geliştirici: Enver KOCAK
"""

import argparse
import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "hafiza"))

import hafiza  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

ENVANTER_DOSYASI = "cihaz-envanteri.json"

TURLER = ["kamera", "kayit-cihazi", "ag-cihazi", "sunucu", "yazici",
          "gecis-sistemi", "alarm", "diger"]

TUR_ETIKETLERI = {
    "kamera": "Kamera", "kayit-cihazi": "Kayıt cihazı", "ag-cihazi": "Ağ cihazı",
    "sunucu": "Sunucu", "yazici": "Yazıcı", "gecis-sistemi": "Geçiş sistemi",
    "alarm": "Alarm", "diger": "Diğer",
}

DURUMLAR = ["calisiyor", "arizali", "bakimda", "sokuldu"]

DURUM_ETIKETLERI = {
    "calisiyor": "Çalışıyor", "arizali": "Arızalı",
    "bakimda": "Bakımda", "sokuldu": "Söküldü",
}

# Envantere yazılmaması gereken alanlar
YASAK_ALANLAR = re.compile(
    r"(?i)^(parola|password|sifre|şifre|secret|kullanici_parolasi)$")

BAKIM_UYARI_GUN = 30


def dosya_yolu(kok=None):
    return hafiza.hafiza_dosyasi(ENVANTER_DOSYASI, kok)


def oku(kok=None):
    veri = hafiza.json_oku(dosya_yolu(kok), {"cihazlar": []})
    veri.setdefault("cihazlar", [])
    return veri


def yaz(veri, kok=None):
    hafiza.json_yaz(dosya_yolu(kok), veri)


def _sonraki_no(veri):
    return max((c.get("no", 0) for c in veri["cihazlar"]), default=0) + 1


def ekle(ad, tur, musteri, konum="", adres="", model="",
         kurulum=None, kasa_anahtari="", not_metni="", kok=None):
    veri = oku(kok)

    cihaz = {
        "no": _sonraki_no(veri),
        "ad": ad.strip(),
        "tur": tur,
        "musteri": musteri.strip(),
        "konum": konum.strip(),
        "adres": adres.strip(),
        "model": model.strip(),
        "kurulum": kurulum or date.today().isoformat(),
        "kasa_anahtari": kasa_anahtari.strip(),
        "not": not_metni.strip(),
        "durum": "calisiyor",
        "son_bakim": None,
        "kayit": hafiza.zaman_metni(),
    }

    veri["cihazlar"].append(cihaz)
    yaz(veri, kok)
    return cihaz


def sir_denetle(kok=None):
    """Envantere parola sızmış mı?"""
    sorunlar = []

    for cihaz in oku(kok)["cihazlar"]:
        for alan, deger in cihaz.items():
            if YASAK_ALANLAR.match(alan):
                sorunlar.append(f"#{cihaz.get('no')} {cihaz.get('ad')}: "
                                f"'{alan}' alanı envanterde durmamalı")
                continue

            if not isinstance(deger, str) or alan == "kasa_anahtari":
                continue

            if re.search(r"(?i)(parola|password|sifre)\s*[:=]\s*\S{4,}", deger):
                sorunlar.append(f"#{cihaz.get('no')} {cihaz.get('ad')}: "
                                f"'{alan}' alanında parola görünümlü içerik var")

    return sorunlar


def bakim_gerekenler(kok=None, gun=BAKIM_UYARI_GUN):
    """Bakımı gecikmiş ya da yaklaşan cihazlar."""
    sonuc = []
    bugun = date.today()

    for cihaz in oku(kok)["cihazlar"]:
        if cihaz.get("durum") == "sokuldu":
            continue

        son = cihaz.get("son_bakim") or cihaz.get("kurulum")
        try:
            son_tarih = datetime.strptime(son, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue

        gecen = (bugun - son_tarih).days
        if gecen >= 365 - gun:
            zengin = dict(cihaz)
            zengin["gecen_gun"] = gecen
            zengin["gecikme"] = gecen - 365
            sonuc.append(zengin)

    return sorted(sonuc, key=lambda c: -c["gecen_gun"])


def _satir(cihaz):
    durum = DURUM_ETIKETLERI.get(cihaz.get("durum"), cihaz.get("durum", "-"))
    tur = TUR_ETIKETLERI.get(cihaz.get("tur"), cihaz.get("tur", "-"))

    satirlar = [f"  #{cihaz['no']:<4} {cihaz['ad'][:30]:<32} {tur:<14} {durum}"]

    ayrinti = []
    if cihaz.get("musteri"):
        ayrinti.append(f"müşteri: {cihaz['musteri']}")
    if cihaz.get("konum"):
        ayrinti.append(f"konum: {cihaz['konum']}")
    if cihaz.get("adres"):
        ayrinti.append(f"adres: {cihaz['adres']}")

    if ayrinti:
        satirlar.append("        " + " · ".join(ayrinti))

    alt = []
    if cihaz.get("model"):
        alt.append(f"model: {cihaz['model']}")
    if cihaz.get("kurulum"):
        alt.append(f"kurulum: {cihaz['kurulum']}")
    if cihaz.get("kasa_anahtari"):
        alt.append("erişim: kasada")

    if alt:
        satirlar.append("        " + " · ".join(alt))

    return "\n".join(satirlar)


# ---------------------------------------------------------------- komutlar

def komut_ekle(args):
    cihaz = ekle(args.ad, args.tur, args.musteri, args.konum or "",
                 args.adres or "", args.model or "", args.kurulum,
                 args.kasa_anahtari or "", args.not_metni or "")

    print(f"Cihaz kaydedildi: #{cihaz['no']}")
    print(f"  {cihaz['ad']} ({TUR_ETIKETLERI[cihaz['tur']]})")
    print(f"  müşteri: {cihaz['musteri']}")
    if cihaz["konum"]:
        print(f"  konum: {cihaz['konum']}")
    if cihaz["adres"]:
        print(f"  adres: {cihaz['adres']}")

    if not cihaz["kasa_anahtari"]:
        print()
        print("Erişim bilgisi kaydı yok. Cihazın kullanıcı adı ve parolası")
        print("kasaya konmalı, buraya kasadaki kaydın adı yazılmalı:")
        print("  --kasa-anahtari \"<kasadaki dosya>\"")

    return 0


def komut_liste(args):
    cihazlar = oku()["cihazlar"]

    if args.tur:
        cihazlar = [c for c in cihazlar if c.get("tur") == args.tur]
    if args.musteri:
        cihazlar = [c for c in cihazlar
                    if args.musteri.lower() in (c.get("musteri") or "").lower()]
    if args.durum:
        cihazlar = [c for c in cihazlar if c.get("durum") == args.durum]
    if not args.sokulenler_dahil:
        cihazlar = [c for c in cihazlar if c.get("durum") != "sokuldu"]

    print(f"CİHAZ ENVANTERİ ({len(cihazlar)})")
    print("=" * 74)

    if not cihazlar:
        print()
        print("Kayıtlı cihaz yok.")
        print("Eklemek için: python envanter.py ekle \"<ad>\" <tur> \"<müşteri>\"")
        return 0

    print()
    for cihaz in cihazlar[: args.sinir]:
        print(_satir(cihaz))
        print()

    if len(cihazlar) > args.sinir:
        print(f"... ve {len(cihazlar) - args.sinir} cihaz daha")

    sorunlar = sir_denetle()
    if sorunlar:
        print()
        print("DİKKAT - envanterde olmaması gereken bilgi var:")
        for sorun in sorunlar[:5]:
            print(f"  {sorun}")

    return 0


def komut_musteri(args):
    cihazlar = [c for c in oku()["cihazlar"]
                if args.musteri.lower() in (c.get("musteri") or "").lower()]

    if not cihazlar:
        print(f"'{args.musteri}' için kayıtlı cihaz yok.")
        return 1

    musteriler = sorted({c["musteri"] for c in cihazlar})

    for musteri in musteriler:
        kendi = [c for c in cihazlar if c["musteri"] == musteri]
        print(f"{musteri.upper()} ({len(kendi)} cihaz)")
        print("=" * 74)

        turler = {}
        for cihaz in kendi:
            turler.setdefault(cihaz.get("tur", "diger"), []).append(cihaz)

        for tur, grup in sorted(turler.items()):
            print(f"\n  {TUR_ETIKETLERI.get(tur, tur)} ({len(grup)})")
            print("  " + "-" * 70)
            for cihaz in grup:
                print(_satir(cihaz))

        print()

    return 0


def komut_guncelle(args):
    veri = oku()

    for cihaz in veri["cihazlar"]:
        if cihaz.get("no") != args.no:
            continue

        if YASAK_ALANLAR.match(args.alan):
            print(f"'{args.alan}' alanı envantere yazılamaz.")
            print("Parola ve erişim bilgisi kasada durur.")
            print("Buraya kasadaki kaydın adı yazılır: --alan kasa_anahtari")
            return 1

        eski = cihaz.get(args.alan)
        cihaz[args.alan] = args.deger
        yaz(veri)

        print(f"#{args.no} güncellendi: {args.alan}")
        print(f"  {eski}  →  {args.deger}")
        return 0

    print(f"#{args.no} numaralı cihaz bulunamadı.")
    return 1


def komut_bakim(args):
    gerekenler = bakim_gerekenler(gun=args.gun)

    print("BAKIM DURUMU")
    print("=" * 74)

    if not gerekenler:
        print()
        print("Bakımı yaklaşan cihaz yok.")
        return 0

    print()
    for cihaz in gerekenler[: args.sinir]:
        gecikme = cihaz["gecikme"]
        if gecikme > 0:
            durum = f"{gecikme} gün GECİKMİŞ"
        else:
            durum = f"{-gecikme} gün kaldı"

        print(f"  #{cihaz['no']:<4} {cihaz['ad'][:30]:<32} {durum}")
        print(f"        müşteri: {cihaz.get('musteri', '-')} · "
              f"son bakım: {cihaz.get('son_bakim') or cihaz.get('kurulum')}")
        print()

    gecikmis = sum(1 for c in gerekenler if c["gecikme"] > 0)
    if gecikmis:
        print(f"{gecikmis} cihazın bakımı gecikmiş.")
        return 1

    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Cihaz envanteri")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("ekle", help="Cihaz kaydı ekle")
    p.add_argument("ad")
    p.add_argument("tur", choices=TURLER)
    p.add_argument("musteri")
    p.add_argument("--konum")
    p.add_argument("--adres", help="Erişim adresi (IP ya da alan adı)")
    p.add_argument("--model")
    p.add_argument("--kurulum", help="YYYY-AA-GG")
    p.add_argument("--kasa-anahtari", dest="kasa_anahtari")
    p.add_argument("--not", dest="not_metni")
    p.set_defaults(islev=komut_ekle)

    p = alt.add_parser("liste", help="Cihazları göster")
    p.add_argument("--tur", choices=TURLER)
    p.add_argument("--musteri")
    p.add_argument("--durum", choices=DURUMLAR)
    p.add_argument("--sokulenler-dahil", action="store_true", dest="sokulenler_dahil")
    p.add_argument("--sinir", type=int, default=20)
    p.set_defaults(islev=komut_liste)

    p = alt.add_parser("musteri", help="Bir müşterinin cihazları")
    p.add_argument("musteri")
    p.set_defaults(islev=komut_musteri)

    p = alt.add_parser("guncelle", help="Bir alanı güncelle")
    p.add_argument("no", type=int)
    p.add_argument("alan")
    p.add_argument("deger")
    p.set_defaults(islev=komut_guncelle)

    p = alt.add_parser("bakim", help="Bakımı yaklaşan cihazlar")
    p.add_argument("--gun", type=int, default=BAKIM_UYARI_GUN)
    p.add_argument("--sinir", type=int, default=20)
    p.set_defaults(islev=komut_bakim)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
