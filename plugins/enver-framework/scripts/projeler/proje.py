#!/usr/bin/env python3
"""Proje tanımı - her proje kendini anlatır.

Bir projenin ne olduğu, ne amaçla çalıştığı, nerede durduğu ve hangi
projelere bağlı olduğu kendi klasöründeki tanım dosyasında yazar:

    <proje>/.claude/proje.json

Bu dosya üç işi birden yapar:
  1. Merkezi panoya bilgi verir      (E11)
  2. Görsel sistem şemasını besler   (E4)
  3. Sunucu korumasına dizin ve veritabanı bilgisi sağlar (E3)

Tanımda parola tutulmaz. Gizli bilgi kasada durur; buradaki
"kasa_anahtari" alanı kasadaki kaydı işaret eder.

Komutlar:
    goster     Bu projenin tanımını göster
    olustur    Tanım dosyası oluştur (şablondan)
    guncelle   Tek bir alanı güncelle
    dogrula    Tanım geçerli mi

Geliştirici: Enver KOCAK
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))

import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

TANIM_YOLU = Path(".claude") / "proje.json"

GECERLI_DURUMLAR = ["gelistirmede", "yarim", "canlida", "beklemede", "bitti", "arsiv"]

DURUM_ETIKETLERI = {
    "gelistirmede": "Geliştirmede",
    "yarim": "Yarım kaldı",
    "canlida": "Canlıda",
    "beklemede": "Beklemede",
    "bitti": "Bitti",
    "arsiv": "Arşivde",
}

SABLON = {
    "ad": "",
    "aciklama": "",
    "musteri": "",
    "durum": "gelistirmede",
    "gorev": "",
    "sunucu": None,
    "dizin": None,
    "alan_adi": None,
    "alt_alan_adlari": [],
    "veritabani": None,
    "kasa_anahtari": None,
    "teknolojiler": [],
    "servisler": [],
    "baglantilar": [],
    "tarihler": {},
    "notlar": "",
}


def tanim_yolu(kok=None):
    return Path(kok or yollar.proje_kok()) / TANIM_YOLU


def oku(kok=None):
    """Proje tanımını oku. Yoksa None döndürür."""
    yol = tanim_yolu(kok)
    if not yol.is_file():
        return None
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def yaz(tanim, kok=None):
    yol = tanim_yolu(kok)
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(tanim, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return yol


def olustur(kok=None, **alanlar):
    """Şablondan yeni tanım üret."""
    kok = Path(kok or yollar.proje_kok())

    tanim = dict(SABLON)
    tanim["ad"] = alanlar.get("ad") or kok.name
    tanim["yerel_yol"] = str(kok)

    for anahtar, deger in alanlar.items():
        if deger is not None and anahtar in tanim:
            tanim[anahtar] = deger

    return tanim


def dogrula(tanim):
    """Tanımda eksik ya da hatalı ne var?"""
    sorunlar = []

    if not isinstance(tanim, dict):
        return ["Tanım bir nesne değil."]

    if not tanim.get("ad"):
        sorunlar.append("'ad' alanı boş.")

    durum = tanim.get("durum")
    if durum and durum not in GECERLI_DURUMLAR:
        sorunlar.append(f"'durum' geçersiz: {durum}. Geçerli: {', '.join(GECERLI_DURUMLAR)}")

    if not tanim.get("gorev") and not tanim.get("aciklama"):
        sorunlar.append("Projenin görevi yazılmamış - şemada ne işe yaradığı görünmez.")

    # Gizli bilgi sızmış mı
    ham = json.dumps(tanim, ensure_ascii=False).lower()
    for kelime in ("parola", "password", "sifre", "secret", "api_key", "token"):
        if f'"{kelime}"' in ham:
            sorunlar.append(
                f"Tanımda '{kelime}' alanı var. Gizli bilgi tanımda tutulmaz, "
                "kasada durur; buraya 'kasa_anahtari' yazılır."
            )
            break

    for servis in tanim.get("servisler", []):
        if not servis.get("ad"):
            sorunlar.append("Bir servisin adı yok.")
        if not servis.get("gorev") and not servis.get("aciklama"):
            sorunlar.append(f"'{servis.get('ad', '?')}' servisinin görevi yazılmamış.")

    for bag in tanim.get("baglantilar", []):
        if not bag.get("hedef"):
            sorunlar.append("Bir bağlantının hedefi yok.")

    return sorunlar


def ozet_satiri(tanim):
    """Tek satırlık özet."""
    durum = DURUM_ETIKETLERI.get(tanim.get("durum"), tanim.get("durum", "-"))
    musteri = tanim.get("musteri") or "-"
    return f"{tanim.get('ad', '?')}  [{durum}]  müşteri: {musteri}"


def ayrintili_metin(tanim):
    """Okunabilir tam özet."""
    satirlar = [
        f"# {tanim.get('ad', '?')}",
        "",
    ]

    if tanim.get("aciklama"):
        satirlar += [tanim["aciklama"], ""]

    alanlar = [
        ("Görev", tanim.get("gorev")),
        ("Durum", DURUM_ETIKETLERI.get(tanim.get("durum"), tanim.get("durum"))),
        ("Müşteri", tanim.get("musteri")),
        ("Sunucu", tanim.get("sunucu")),
        ("Dizin", tanim.get("dizin")),
        ("Alan adı", tanim.get("alan_adi")),
        ("Veritabanı", tanim.get("veritabani")),
        ("Yerel yol", tanim.get("yerel_yol")),
    ]

    for etiket, deger in alanlar:
        if deger:
            satirlar.append(f"**{etiket}:** {deger}")

    if tanim.get("alt_alan_adlari"):
        satirlar.append(f"**Alt alan adları:** {', '.join(tanim['alt_alan_adlari'])}")

    if tanim.get("teknolojiler"):
        satirlar.append(f"**Teknolojiler:** {', '.join(tanim['teknolojiler'])}")

    if tanim.get("kasa_anahtari"):
        satirlar.append(f"**Kasa kaydı:** {tanim['kasa_anahtari']}  (erişim için kasa açılmalı)")

    servisler = tanim.get("servisler", [])
    if servisler:
        satirlar += ["", "## Neler çalışıyor", ""]
        for servis in servisler:
            gorev = servis.get("gorev") or servis.get("aciklama") or "-"
            satirlar.append(f"- **{servis.get('ad')}** ({servis.get('tur', 'servis')}) — {gorev}")

    baglantilar = tanim.get("baglantilar", [])
    if baglantilar:
        satirlar += ["", "## Bağlı olduğu projeler", ""]
        for bag in baglantilar:
            aciklama = bag.get("aciklama") or ""
            satirlar.append(f"- **{bag.get('hedef')}** ({bag.get('tur', 'bağlantı')}) — {aciklama}")

    tarihler = tanim.get("tarihler", {})
    if tarihler:
        satirlar += ["", "## Tarihler", ""]
        for ad, deger in tarihler.items():
            satirlar.append(f"- {ad}: {deger}")

    if tanim.get("notlar"):
        satirlar += ["", "## Notlar", "", tanim["notlar"]]

    return "\n".join(satirlar)


# ---------------------------------------------------------------- komutlar

def komut_goster(args):
    tanim = oku()
    if tanim is None:
        print("Bu projede tanım dosyası yok.")
        print(f"Oluşturmak için: python proje.py olustur")
        return 1

    print(ayrintili_metin(tanim))
    return 0


def komut_olustur(args):
    kok = yollar.proje_kok()

    if oku(kok) and not args.uzerine_yaz:
        print("Tanım dosyası zaten var. Üzerine yazmak için --uzerine-yaz kullan.")
        return 1

    tanim = olustur(
        kok,
        ad=args.ad,
        aciklama=args.aciklama,
        gorev=args.gorev,
        musteri=args.musteri,
        durum=args.durum,
    )

    yol = yaz(tanim, kok)
    print(f"Tanım oluşturuldu: {yol}")
    print()
    print("Doldurulması gereken alanlar: `gorev`, `musteri`, `sunucu`, `dizin`, "
          "`servisler`, `baglantilar`")
    return 0


def komut_guncelle(args):
    kok = yollar.proje_kok()
    tanim = oku(kok)

    if tanim is None:
        print("Tanım dosyası yok. Önce: python proje.py olustur")
        return 1

    try:
        deger = json.loads(args.deger)
    except json.JSONDecodeError:
        deger = args.deger

    tanim[args.alan] = deger
    yaz(tanim, kok)
    print(f"Güncellendi: {args.alan} = {deger}")
    return 0


def komut_dogrula(args):
    tanim = oku()
    if tanim is None:
        print("Tanım dosyası yok.")
        return 1

    sorunlar = dogrula(tanim)
    if not sorunlar:
        print("Tanım geçerli.")
        return 0

    print(f"{len(sorunlar)} sorun bulundu:")
    for sorun in sorunlar:
        print(f"  - {sorun}")
    return 1


def main():
    ayristirici = argparse.ArgumentParser(description="Proje tanımı")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("goster", help="Tanımı göster")
    p.set_defaults(islev=komut_goster)

    p = alt.add_parser("olustur", help="Tanım dosyası oluştur")
    p.add_argument("--ad")
    p.add_argument("--aciklama")
    p.add_argument("--gorev")
    p.add_argument("--musteri")
    p.add_argument("--durum", choices=GECERLI_DURUMLAR, default="gelistirmede")
    p.add_argument("--uzerine-yaz", action="store_true", dest="uzerine_yaz")
    p.set_defaults(islev=komut_olustur)

    p = alt.add_parser("guncelle", help="Bir alanı güncelle")
    p.add_argument("alan")
    p.add_argument("deger")
    p.set_defaults(islev=komut_guncelle)

    p = alt.add_parser("dogrula", help="Tanım geçerli mi")
    p.set_defaults(islev=komut_dogrula)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
