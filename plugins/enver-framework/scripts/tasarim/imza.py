#!/usr/bin/env python3
"""İz kimliği - projeye gömülen geliştirici ve şirket bilgisi.

Enver'in kuralı:
  - İz kimliği HER PROJEDE FARKLI olabilir.
  - Detaylı olacak ama ÖN PLANDA GÖRÜNMEYECEK.
  - Şirket bilgileri de projeye göre değişebilir.

Bu yüzden imza tek tip değildir. Her projeye kendi imza biçimi seçilir ve
seçilen biçim kaydedilir; iki proje aynı imzayı taşımaz.

Beş imza biçimi vardır, hepsi göze batmayan yerlere yerleşir:

    kaynak-yorumu   Sayfa kaynağında yorum bloğu
    üstveri         Meta etiketleri
    insanlar-txt    humans.txt dosyası
    yapısal-veri    Yapısal veri bloğu
    altbilgi-ince   Alt bilgide tek satır, soluk

Şirket bilgisi projeye göre değişebildiği için kimlik dosyasından okunur;
tanımlı değilse varsayılan kullanılır.

Komutlar:
    ayarla     Bu projenin imza bilgisini ve biçimini belirle
    göster     Mevcut imza ayarını göster
    üret       İmza içeriğini üret
    yerleştir  İmzayı bir dosyaya yerleştir
    denetle    İmza ön planda mı, göze batıyor mu

Geliştirici: Enver KOCAK
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "hafiza"))

import ayarlar  # noqa: E402
import hafiza  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

IMZA_DOSYASI = "imza.json"
KAYIT_DOSYASI = "imza-kayitlari.json"

# Kimlik koda gömülmez; kurulumda kaydedilir ve ayardan okunur.
# Böylece framework'u başkası kullandığında kendi bilgisi görünür.
def varsayilan_kimlik():
    kayit = ayarlar.kimlik()
    return {
        "gelistirici": kayit.get("gelistirici", ""),
        "site": kayit.get("site", ""),
        "eposta": kayit.get("eposta", ""),
        "sirket": kayit.get("sirket", ""),
        "sirket_sitesi": "",
    }

BICIMLER = ["kaynak-yorumu", "ustveri", "insanlar-txt", "yapisal-veri", "altbilgi-ince"]

BICIM_ACIKLAMALARI = {
    "kaynak-yorumu": "Sayfa kaynağında yorum bloğu - kaynağa bakan görür",
    "ustveri": "Meta etiketleri - arama motorları ve araçlar okur",
    "insanlar-txt": "humans.txt dosyası - meraklısı bilir, aranır",
    "yapisal-veri": "Yapısal veri bloğu - arama motorları için",
    "altbilgi-ince": "Alt bilgide tek satır, soluk ve küçük",
}


def imza_yolu(kok=None):
    return Path(kok or yollar.proje_kok()) / ".claude" / IMZA_DOSYASI


def imza_oku(kok=None):
    yol = imza_yolu(kok)
    if not yol.is_file():
        return None
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def imza_yaz(veri, kok=None):
    yol = imza_yolu(kok)
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return yol


def kayitlar():
    return hafiza.json_oku(hafiza.hafiza_dosyasi(KAYIT_DOSYASI),
                           {"projeler": {}}).get("projeler", {})


def kayit_ekle(proje_adi, bicim):
    yol = hafiza.hafiza_dosyasi(KAYIT_DOSYASI)
    veri = hafiza.json_oku(yol, {"projeler": {}})
    veri.setdefault("projeler", {})
    veri["projeler"][proje_adi] = {"bicim": bicim, "tarih": hafiza.zaman_metni()}
    hafiza.json_yaz(yol, veri)


def bicim_sec(proje_adi):
    """Bu projeye, başkalarında az kullanılmış bir biçim seç."""
    kullanim = {bicim: 0 for bicim in BICIMLER}
    for kayit in kayitlar().values():
        if kayit.get("bicim") in kullanim:
            kullanim[kayit["bicim"]] += 1

    en_az = min(kullanim.values())
    adaylar = [bicim for bicim, sayi in kullanim.items() if sayi == en_az]

    tohum = int(hashlib.sha256(proje_adi.encode("utf-8")).hexdigest()[:8], 16)
    return adaylar[tohum % len(adaylar)]


def kimlik_birlestir(imza):
    kimlik = varsayilan_kimlik()
    kimlik.update({a: d for a, d in (imza or {}).get("kimlik", {}).items() if d})
    return kimlik


# ---------------------------------------------------------------- üretim

def _kaynak_yorumu(kimlik, proje):
    satirlar = [f"  {proje}"]
    if kimlik.get("sirket"):
        satirlar.append(f"  {kimlik['sirket']}")
    satirlar.append(f"  Geliştirme: {kimlik['gelistirici']}")
    if kimlik.get("site"):
        satirlar.append(f"  {kimlik['site']}")
    if kimlik.get("eposta"):
        satirlar.append(f"  {kimlik['eposta']}")

    govde = "\n".join(satirlar)
    return f"<!--\n{govde}\n-->"


def _ustveri(kimlik, proje):
    satirlar = [f'<meta name="author" content="{kimlik["gelistirici"]}">']
    if kimlik.get("sirket"):
        satirlar.append(f'<meta name="copyright" content="{kimlik["sirket"]}">')
    if kimlik.get("site"):
        satirlar.append(f'<link rel="author" href="https://{kimlik["site"]}">')
    return "\n".join(satirlar)


def _insanlar_txt(kimlik, proje):
    satirlar = ["/* GELİŞTİRME */", f"  Geliştirici: {kimlik['gelistirici']}"]
    if kimlik.get("site"):
        satirlar.append(f"  Site: {kimlik['site']}")
    if kimlik.get("eposta"):
        satirlar.append(f"  İletişim: {kimlik['eposta']}")
    satirlar += ["", "/* PROJE */", f"  Ad: {proje}"]
    if kimlik.get("sirket"):
        satirlar.append(f"  Kurum: {kimlik['sirket']}")
    return "\n".join(satirlar) + "\n"


def _yapisal_veri(kimlik, proje):
    veri = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": proje,
        "author": {"@type": "Person", "name": kimlik["gelistirici"]},
    }
    if kimlik.get("site"):
        veri["author"]["url"] = f"https://{kimlik['site']}"
    if kimlik.get("sirket"):
        veri["publisher"] = {"@type": "Organization", "name": kimlik["sirket"]}

    govde = json.dumps(veri, ensure_ascii=False, indent=2)
    return f'<script type="application/ld+json">\n{govde}\n</script>'


def _altbilgi_ince(kimlik, proje):
    kim = kimlik.get("sirket") or kimlik["gelistirici"]
    adres = kimlik.get("sirket_sitesi") or kimlik.get("site")

    if adres:
        ic = f'<a href="https://{adres}" rel="author">{kim}</a>'
    else:
        ic = kim

    return (f'<p class="gelistirme-notu" '
            f'style="font-size:.72rem;opacity:.45;margin-top:2rem">{ic}</p>')


URETICILER = {
    "kaynak-yorumu": _kaynak_yorumu,
    "ustveri": _ustveri,
    "insanlar-txt": _insanlar_txt,
    "yapisal-veri": _yapisal_veri,
    "altbilgi-ince": _altbilgi_ince,
}


def uret(imza, proje):
    bicim = imza.get("bicim", "kaynak-yorumu")
    kimlik = kimlik_birlestir(imza)
    return URETICILER[bicim](kimlik, proje)


# ---------------------------------------------------------------- denetim

# İmzanın ön planda olduğunu gösteren işaretler
ON_PLAN_ISARETLERI = [
    (re.compile(r"font-size\s*:\s*(1[.\d]*|[2-9])(rem|em)", re.IGNORECASE),
     "yazı boyutu büyük"),
    (re.compile(r"opacity\s*:\s*(0\.[7-9]|1)\b", re.IGNORECASE),
     "solukluk yetersiz"),
    (re.compile(r"<h[12]\b", re.IGNORECASE), "başlık etiketiyle yazılmış"),
    (re.compile(r"position\s*:\s*fixed", re.IGNORECASE), "sabit konumlanmış"),
    (re.compile(r"font-weight\s*:\s*(700|800|900|bold)", re.IGNORECASE), "kalın yazılmış"),
]


def denetle(icerik):
    """İmza göze batıyor mu?"""
    sorunlar = []
    for desen, aciklama in ON_PLAN_ISARETLERI:
        if desen.search(icerik):
            sorunlar.append(aciklama)
    return sorunlar


# ---------------------------------------------------------------- komutlar

def komut_ayarla(args):
    kok = yollar.proje_kok()
    proje = yollar.proje_adi(kok)

    mevcut = imza_oku(kok) or {}
    kimlik = dict(mevcut.get("kimlik", {}))

    for alan in ("gelistirici", "site", "eposta", "sirket", "sirket_sitesi"):
        deger = getattr(args, alan, None)
        if deger is not None:
            kimlik[alan] = deger

    bicim = args.bicim or mevcut.get("bicim") or bicim_sec(proje)

    veri = {"proje": proje, "bicim": bicim, "kimlik": kimlik,
            "guncelleme": hafiza.zaman_metni()}

    yol = imza_yaz(veri, kok)
    kayit_ekle(proje, bicim)

    print(f"İmza ayarlandı: {yol}")
    print(f"Biçim: {bicim} - {BICIM_ACIKLAMALARI[bicim]}")
    print()

    tam = kimlik_birlestir(veri)
    for alan, deger in tam.items():
        if deger:
            print(f"  {alan}: {deger}")

    if not tam.get("sirket"):
        print()
        print("Şirket bilgisi tanımlı değil. Projeye göre değişebileceği için")
        print("her projede ayrı verilebilir: --sirket \"<ad>\"")

    return 0


def komut_goster(args):
    imza = imza_oku()
    if imza is None:
        print("Bu projenin imza ayarı yok.")
        print("Oluşturmak için: python imza.py ayarla")
        return 1

    print(f"Proje : {imza.get('proje')}")
    print(f"Biçim : {imza.get('bicim')} - {BICIM_ACIKLAMALARI.get(imza.get('bicim'), '-')}")
    print()
    for alan, deger in kimlik_birlestir(imza).items():
        if deger:
            print(f"  {alan}: {deger}")
    return 0


def komut_uret(args):
    kok = yollar.proje_kok()
    imza = imza_oku(kok)

    if imza is None:
        proje = yollar.proje_adi(kok)
        imza = {"proje": proje, "bicim": bicim_sec(proje), "kimlik": {}}

    icerik = uret(imza, imza.get("proje") or yollar.proje_adi(kok))

    if args.hedef:
        hedef = Path(args.hedef)
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(icerik + "\n", encoding="utf-8")
        print(f"Yazıldı: {hedef}")
        return 0

    print(icerik)
    return 0


def komut_denetle(args):
    kok = yollar.proje_kok()
    imza = imza_oku(kok)

    if imza is None:
        print("İmza ayarı yok.")
        return 1

    icerik = uret(imza, imza.get("proje"))
    sorunlar = denetle(icerik)

    if not sorunlar:
        print("İmza ön planda değil - kural karşılanıyor.")
        return 0

    print("İmza göze batıyor:")
    for sorun in sorunlar:
        print(f"  - {sorun}")
    print()
    print("Kural: iz kimliği detaylı olacak ama ön planda görünmeyecek.")
    return 1


def komut_liste(args):
    kayit = kayitlar()

    if not kayit:
        print("Kayıtlı imza yok.")
        return 0

    print(f"PROJE İMZALARI ({len(kayit)})")
    print("=" * 62)
    for proje, bilgi in sorted(kayit.items()):
        print(f"  {proje:<32} {bilgi['bicim']}")

    sayilar = {}
    for bilgi in kayit.values():
        sayilar[bilgi["bicim"]] = sayilar.get(bilgi["bicim"], 0) + 1

    print()
    print("Biçim dağılımı:")
    for bicim in BICIMLER:
        print(f"  {bicim:<16} {sayilar.get(bicim, 0)}")

    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="İz kimliği")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("ayarla", help="İmza bilgisini belirle")
    p.add_argument("--bicim", choices=BICIMLER)
    p.add_argument("--gelistirici")
    p.add_argument("--site")
    p.add_argument("--eposta")
    p.add_argument("--sirket")
    p.add_argument("--sirket-sitesi", dest="sirket_sitesi")
    p.set_defaults(islev=komut_ayarla)

    p = alt.add_parser("goster", help="İmza ayarını göster")
    p.set_defaults(islev=komut_goster)

    p = alt.add_parser("uret", help="İmza içeriğini üret")
    p.add_argument("--hedef")
    p.set_defaults(islev=komut_uret)

    p = alt.add_parser("denetle", help="İmza ön planda mı")
    p.set_defaults(islev=komut_denetle)

    p = alt.add_parser("liste", help="Bütün proje imzaları")
    p.set_defaults(islev=komut_liste)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
