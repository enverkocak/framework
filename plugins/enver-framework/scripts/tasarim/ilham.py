#!/usr/bin/env python3
"""Tasarım ilham kaynakları.

İki iş yapar:

  1. YAZI TİPİ KATALOĞU
     Sistem yazı tipleriyle sınırlı kalmak tipografi çeşitliliğini öldürüyor.
     Katalogdaki eşleşmeler gerçek yazı tipleridir; anahtar gerekmeden
     yüklenir ve ağ yoksa yedek yığına düşer.

  2. ÖRNEK SİTE ÇÖZÜMLEMESİ
     Müşteri "şu site gibi olsun" dediğinde o siteyi çözümler:
     hangi renkler, hangi tipografi, hangi boşluk ritmi, hangi karakter.

     KOPYALAMAZ. Çıkardığı şey bir yön tarifidir; o yönde ÖZGÜN bir tasarım
     üretilir. Kopya, hem etik değildir hem de zaten aynılaşmaya götürür.

Ağ erişimi olmayan makinede katalog çalışmaya devam eder; yalnız site
çözümlemesi yapılamaz.

Komutlar:
    yazıtipi liste      Katalogdaki eşleşmeler
    yazıtipi seç        Bir karaktere uygun eşleşme öner
    yazıtipi bağlantı   Yükleme adresi üret
    site <adres>        Örnek siteyi çözümle

Geliştirici: Enver KOCAK
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))

import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

KATALOG_YOLU = (SCRIPT_DIZINI.parent.parent / "references" / "yazi-tipi-eslesmeleri.json")

TARAYICI_BASLIGI = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept-Language": "tr,en;q=0.8",
}

ZAMAN_ASIMI = 20


# ---------------------------------------------------------------- katalog

def katalog_oku():
    try:
        return json.loads(KATALOG_YOLU.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"eslesmeler": []}


def eslesmeler():
    return katalog_oku().get("eslesmeler", [])


def karakterler():
    return sorted({e["karakter"] for e in eslesmeler()})


def karaktere_gore(karakter):
    return [e for e in eslesmeler() if e["karakter"] == karakter]


def yukleme_baglantisi(eslesme):
    """Yazı tiplerini yükleyecek adresi üret."""
    temel = katalog_oku().get("kaynak_adresi", "https://fonts.googleapis.com/css2")

    parcalar = []
    for ad_alani, agirlik_alani in (("baslik", "baslik_agirlik"),
                                    ("govde", "govde_agirlik")):
        ad = eslesme.get(ad_alani)
        if not ad:
            continue
        agirliklar = eslesme.get(agirlik_alani, "400")
        aile = ad.replace(" ", "+")
        parcalar.append(f"family={aile}:wght@{agirliklar.replace(',', ';')}")

    return f"{temel}?{'&'.join(parcalar)}&display=swap"


def yigin_uret(eslesme, alan):
    """Yazı tipi yığını: önce gerçek yazı tipi, sonra yedek."""
    ad = eslesme.get(alan)
    yedek = eslesme.get(f"yedek_{alan}", "sans-serif")
    return f"'{ad}', {yedek}" if ad else yedek


# ---------------------------------------------------------- site çözümlemesi

def _getir(adres):
    if not adres.startswith(("http://", "https://")):
        adres = "https://" + adres

    istek = urllib.request.Request(adres, headers=TARAYICI_BASLIGI)
    with urllib.request.urlopen(istek, timeout=ZAMAN_ASIMI) as yanit:
        ham = yanit.read(3_000_000)
        kodlama = yanit.headers.get_content_charset() or "utf-8"
    return ham.decode(kodlama, errors="replace"), adres


def _stil_kaynaklari(html, temel_adres):
    """Sayfadaki stil dosyalarının adreslerini bul."""
    from urllib.parse import urljoin

    adresler = []
    for eslesme in re.finditer(
            r'<link[^>]+rel=["\']?stylesheet["\']?[^>]*>', html, re.IGNORECASE):
        etiket = eslesme.group(0)
        kaynak = re.search(r'href=["\']([^"\']+)["\']', etiket, re.IGNORECASE)
        if kaynak:
            adresler.append(urljoin(temel_adres, kaynak.group(1)))
    return adresler[:6]


def _renkleri_topla(metin):
    renkler = Counter()

    for eslesme in re.finditer(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", metin):
        renk = eslesme.group(1).lower()
        if len(renk) == 3:
            renk = "".join(harf * 2 for harf in renk)
        renkler[f"#{renk}"] += 1

    for eslesme in re.finditer(
            r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})", metin):
        kirmizi, yesil, mavi = (int(eslesme.group(sira)) for sira in (1, 2, 3))
        renkler["#{:02x}{:02x}{:02x}".format(kirmizi, yesil, mavi)] += 1

    # Siyah, beyaz ve gri tonlar karakter taşımaz; ayıklanır
    def renkli_mi(renk):
        kirmizi, yesil, mavi = (int(renk[i:i + 2], 16) for i in (1, 3, 5))
        return max(kirmizi, yesil, mavi) - min(kirmizi, yesil, mavi) > 18

    return [(renk, sayi) for renk, sayi in renkler.most_common(40) if renkli_mi(renk)]


def _yazi_tiplerini_topla(metin):
    aileler = Counter()
    for eslesme in re.finditer(r"font-family\s*:\s*([^;}\n]+)", metin, re.IGNORECASE):
        for parca in eslesme.group(1).split(","):
            ad = parca.strip().strip("'\"")
            if not ad or ad.lower() in (
                    "sans-serif", "serif", "monospace", "cursive", "system-ui",
                    "inherit", "initial", "unset", "-apple-system"):
                continue
            aileler[ad] += 1
    return aileler.most_common(8)


def _sayisal_topla(metin, ozellik):
    degerler = Counter()
    for eslesme in re.finditer(
            rf"{ozellik}\s*:\s*([0-9.]+)(px|rem|em)", metin, re.IGNORECASE):
        degerler[f"{eslesme.group(1)}{eslesme.group(2)}"] += 1
    return degerler.most_common(8)


def _karakter_tahmini(html, stil):
    """Sayfanın düzen karakterini tahmin et."""
    isaretler = []

    if re.search(r"display\s*:\s*grid", stil, re.IGNORECASE):
        isaretler.append("ızgara")
    if re.search(r"display\s*:\s*flex", stil, re.IGNORECASE):
        isaretler.append("esnek yerleşim")
    if re.search(r"border-radius\s*:\s*(0|0px)\b", stil, re.IGNORECASE):
        isaretler.append("keskin köşe")
    if re.search(r"box-shadow\s*:\s*none", stil, re.IGNORECASE):
        isaretler.append("düz yüzey")
    if re.search(r"backdrop-filter|blur\(", stil, re.IGNORECASE):
        isaretler.append("bulanık katman")
    if re.search(r"linear-gradient|radial-gradient", stil, re.IGNORECASE):
        isaretler.append("geçişli renk")
    if re.search(r"text-transform\s*:\s*uppercase", stil, re.IGNORECASE):
        isaretler.append("büyük harf başlık")
    if re.search(r"@media[^{]*max-width", stil, re.IGNORECASE):
        isaretler.append("mobil uyum")

    bolum_sayisi = len(re.findall(r"<section", html, re.IGNORECASE))
    if bolum_sayisi > 6:
        isaretler.append("uzun sayfa")
    elif bolum_sayisi and bolum_sayisi <= 3:
        isaretler.append("kısa sayfa")

    return isaretler


def site_cozumle(adres):
    html, son_adres = _getir(adres)

    stil = ""
    for stil_adresi in _stil_kaynaklari(html, son_adres):
        try:
            icerik, _ = _getir(stil_adresi)
            stil += "\n" + icerik
        except (urllib.error.URLError, OSError, ValueError):
            continue

    # Sayfa içi stiller
    for eslesme in re.finditer(r"<style[^>]*>([\s\S]*?)</style>", html, re.IGNORECASE):
        stil += "\n" + eslesme.group(1)

    tumu = html + "\n" + stil

    baslik = ""
    eslesme = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    if eslesme:
        baslik = eslesme.group(1).strip()

    return {
        "adres": son_adres,
        "baslik": baslik,
        "renkler": _renkleri_topla(tumu),
        "yazi_tipleri": _yazi_tiplerini_topla(tumu),
        "kose": _sayisal_topla(stil, "border-radius"),
        "bosluk": _sayisal_topla(stil, "padding"),
        "karakter": _karakter_tahmini(html, stil),
        "stil_dosyasi": len(_stil_kaynaklari(html, son_adres)),
    }


def cozumleme_metni(sonuc):
    satirlar = [
        "ÖRNEK SİTE ÇÖZÜMLEMESİ",
        "=" * 60,
        f"Adres : {sonuc['adres']}",
    ]
    if sonuc["baslik"]:
        satirlar.append(f"Başlık: {sonuc['baslik'][:70]}")

    satirlar += ["", "Öne çıkan renkler:"]
    if sonuc["renkler"]:
        for renk, sayi in sonuc["renkler"][:8]:
            satirlar.append(f"  {renk}   ({sayi} kez)")
    else:
        satirlar.append("  Belirgin renk bulunamadı (görsel ağırlıklı olabilir).")

    satirlar += ["", "Yazı tipleri:"]
    if sonuc["yazi_tipleri"]:
        for ad, sayi in sonuc["yazi_tipleri"]:
            satirlar.append(f"  {ad}   ({sayi} kez)")
    else:
        satirlar.append("  Bulunamadı.")

    if sonuc["kose"]:
        satirlar += ["", "Köşe yuvarlaklığı: " +
                     ", ".join(f"{deger} ({sayi})" for deger, sayi in sonuc["kose"][:5])]

    if sonuc["bosluk"]:
        satirlar += ["Boşluk değerleri : " +
                     ", ".join(f"{deger} ({sayi})" for deger, sayi in sonuc["bosluk"][:5])]

    if sonuc["karakter"]:
        satirlar += ["", "Düzen işaretleri: " + ", ".join(sonuc["karakter"])]

    satirlar += [
        "",
        "-" * 60,
        "BU BİR KOPYALAMA REÇETESİ DEĞİLDİR.",
        "",
        "Buradan çıkarılacak şey renk kodları değil, YÖN'dür:",
        "  - Renkler sıcak mı soğuk mu, doygun mu sönük mü?",
        "  - Tipografi ciddi mi samimi mi?",
        "  - Yüzeyler keskin mi yumuşak mı?",
        "  - Sayfa yoğun mu ferah mı?",
        "",
        "Bu yön alınır, ÖZGÜN bir kimlik üretilir:",
        "  python kimlik.py uret",
        "",
    ]

    return "\n".join(satirlar)


# ---------------------------------------------------------------- komutlar

def komut_yazitipi_liste(args):
    kayitlar = eslesmeler()

    if args.karakter:
        kayitlar = [e for e in kayitlar if e["karakter"] == args.karakter]

    if not kayitlar:
        print("Eşleşme bulunamadı.")
        print(f"Karakterler: {', '.join(karakterler())}")
        return 1

    print(f"YAZI TİPİ EŞLEŞMELERİ ({len(kayitlar)})")
    print("=" * 74)

    for eslesme in kayitlar:
        print(f"  {eslesme['ad']}  [{eslesme['karakter']}]")
        print(f"     başlık: {eslesme['baslik']}   gövde: {eslesme['govde']}")
        print(f"     his   : {eslesme['his']}")
        print()

    print(f"Karakterler: {', '.join(karakterler())}")
    return 0


def komut_yazitipi_sec(args):
    adaylar = karaktere_gore(args.karakter) if args.karakter else eslesmeler()

    if not adaylar:
        print(f"'{args.karakter}' karakterinde eşleşme yok.")
        print(f"Karakterler: {', '.join(karakterler())}")
        return 1

    # Proje adına göre sabit bir seçim: aynı proje hep aynı sonucu alır
    import hashlib
    ad = args.proje or yollar.proje_adi()
    tohum = int(hashlib.sha256(ad.encode("utf-8")).hexdigest()[:8], 16)
    eslesme = adaylar[tohum % len(adaylar)]

    print(f"Önerilen eşleşme: {eslesme['ad']}  [{eslesme['karakter']}]")
    print(f"  his: {eslesme['his']}")
    print()
    print("CSS:")
    print(f"  --yazi-baslik: {yigin_uret(eslesme, 'baslik')};")
    print(f"  --yazi-govde: {yigin_uret(eslesme, 'govde')};")
    print(f"  ölçek oranı : {eslesme['olcek']}")
    print()
    print("Yükleme:")
    print(f'  <link rel="stylesheet" href="{yukleme_baglantisi(eslesme)}">')
    print()
    print("Ağ yoksa yedek yığın devreye girer, sayfa yine düzgün görünür.")
    return 0


def komut_yazitipi_baglanti(args):
    kayitlar = [e for e in eslesmeler() if e["ad"] == args.ad]
    if not kayitlar:
        print(f"'{args.ad}' adında eşleşme yok.")
        return 1

    print(yukleme_baglantisi(kayitlar[0]))
    return 0


def komut_site(args):
    try:
        sonuc = site_cozumle(args.adres)
    except (urllib.error.URLError, OSError, ValueError) as hata:
        print(f"Site alınamadı: {hata}")
        print()
        print("Ağ erişimi yoksa ya da site erişimi engelliyorsa,")
        print("ekran görüntüsü üzerinden de yön çıkarılabilir.")
        return 1

    print(cozumleme_metni(sonuc))

    if args.hedef:
        hedef = Path(args.hedef)
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(json.dumps(sonuc, ensure_ascii=False, indent=2),
                         encoding="utf-8")
        print(f"Ham çözümleme yazıldı: {hedef}")

    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Tasarım ilham kaynakları")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    yazitipi = alt.add_parser("yazitipi", help="Yazı tipi kataloğu").add_subparsers(
        dest="islem", required=True)

    p = yazitipi.add_parser("liste")
    p.add_argument("--karakter")
    p.set_defaults(islev=komut_yazitipi_liste)

    p = yazitipi.add_parser("sec")
    p.add_argument("--karakter")
    p.add_argument("--proje")
    p.set_defaults(islev=komut_yazitipi_sec)

    p = yazitipi.add_parser("baglanti")
    p.add_argument("ad")
    p.set_defaults(islev=komut_yazitipi_baglanti)

    p = alt.add_parser("site", help="Örnek siteyi çözümle")
    p.add_argument("adres")
    p.add_argument("--hedef")
    p.set_defaults(islev=komut_site)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
