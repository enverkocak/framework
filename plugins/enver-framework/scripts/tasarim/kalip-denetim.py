#!/usr/bin/env python3
"""Kalıp denetimi - "bu otomatik üretilmiş" dedirten işaretleri yakalar.

Sorun şu: üretilen arayüzler birbirine benziyor. Bakan kişi kodu görmeden,
sadece sayfaya bakarak "bu şablon" diyor. Sebep tek tek küçük alışkanlıklar:
hep aynı mor-mavi geçiş, hep üç kart, hep ortalanmış başlık ve iki düğme,
hep aynı yazı tipi, hep aynı köşe yuvarlaklığı.

Bu betik o işaretleri arar ve ağırlığına göre raporlar.

Ağırlıklar:
    yüksek   Tek başına bile "şablon" dedirtir
    orta     Birkaçı bir arada olursa belli eder
    düşük    Tek başına sorun değil, yığılırsa dikkat çeker

Amaç kuralcılık değil: her bulgunun yanında NE YAPILACAĞI yazar.

Komutlar:
    tara <yol>     Bir dosyayı ya da klasörü tara
    kurallar       Aranan kalıpları listele

Geliştirici: Enver KOCAK
"""

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))

import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

TARANACAK_UZANTILAR = {".html", ".htm", ".css", ".scss", ".jsx", ".tsx", ".vue", ".svelte"}

TARANMAYAN_DIZINLER = ("/node_modules/", "/.git/", "/vendor/", "/dist/",
                       "/build/", "/_arsiv/", "/_calisma/")

# (kod, ağırlık, açıklama, desen, ne yapılmalı)
KURALLAR = [
    ("mor-mavi-gecis", "yuksek",
     "Herkesin kullandığı mor-mavi geçiş",
     re.compile(r"#66[67]eea|#764ba2|#7f7fd5|#86a8e7|#a777e3", re.IGNORECASE),
     "Projenin kendi renginden bir geçiş üret ya da geçişi tümden bırak."),

    ("gecis-yigini", "orta",
     "Sayfa geçişli renklerle dolu",
     re.compile(r"linear-gradient|radial-gradient", re.IGNORECASE),
     "Geçişi tek bir yerde vurgu olarak kullan, her yüzeye yayma."),

    ("uc-kart", "orta",
     "Klasik üç kartlık özellik bölümü",
     re.compile(r"(grid-template-columns\s*:\s*repeat\(\s*3\s*,)|"
                r"(<div[^>]*class=[\"'][^\"']*\bcol-md-4\b)", re.IGNORECASE),
     "Kart sayısını içerik belirlesin. İki, dört ya da asimetrik bir düzen dene."),

    ("ortali-hero", "orta",
     "Ortalanmış başlık ve iki düğme kalıbı",
     re.compile(r"class=[\"'][^\"']*\bhero\b[^\"']*[\"'][\s\S]{0,400}?"
                r"text-align\s*:\s*center", re.IGNORECASE),
     "Başlığı sola yasla, tek bir eyleme odaklan ya da görsel dengeyi kaydır."),

    ("varsayilan-yazitipi", "yuksek",
     "Her yerde aynı varsayılan yazı tipi",
     re.compile(r"font-family\s*:\s*['\"]?(Inter|Roboto|Open Sans|Lato|Poppins)['\"]?\s*[,;]"
                r"(?![\s\S]{0,2000}font-family)", re.IGNORECASE),
     "Başlık ve gövde için farklı karakterde bir eşleşme seç: ilham.py yazitipi sec"),

    ("cerceve-varsayilani", "yuksek",
     "Çerçevenin hazır bileşenleri hiç değiştirilmemiş",
     re.compile(r"\bclass=[\"'][^\"']*\b(btn btn-primary|card-body|navbar-expand-lg|"
                r"jumbotron|container-fluid)\b", re.IGNORECASE),
     "Hazır bileşen kullanılabilir ama görünümü projenin kimliğine uydurulmalı."),

    ("emoji-ikon", "orta",
     "İkon yerine emoji kullanılmış",
     re.compile(r"<(?:div|span|i)[^>]*class=[\"'][^\"']*icon[^\"']*[\"'][^>]*>\s*"
                r"[\U0001F300-\U0001FAFF☀-➿]"),
     "Emoji hızlı çözümdür ama şablon hissi verir. Basit bir vektör ikon seti kullan."),

    ("lorem", "yuksek",
     "Yer tutucu metin kalmış",
     re.compile(r"\blorem ipsum\b|\bdolor sit amet\b", re.IGNORECASE),
     "Gerçek içerik yaz. Yoksa Türkçe örnek içerik üret, Latince bırakma."),

    ("ingilizce-arayuz", "yuksek",
     "Arayüzde İngilizce metin",
     re.compile(r">\s*(Get Started|Learn More|Read More|Sign Up|Contact Us|"
                r"Our Services|About Us|Coming Soon|Subscribe)\s*<", re.IGNORECASE),
     "Arayüz Türkçe olacak: Başla, Daha fazla, Kaydol, İletişim, Hizmetlerimiz..."),

    ("tek-kose-degeri", "dusuk",
     "Bütün köşelerde tek bir yuvarlaklık değeri",
     re.compile(r"border-radius\s*:\s*8px(?![\s\S]{0,3000}border-radius\s*:\s*(?!8px))",
                re.IGNORECASE),
     "Küçük, orta ve büyük yüzeyler için farklı değerler kullan."),

    ("golge-tekrari", "dusuk",
     "Her yerde aynı gölge",
     re.compile(r"(box-shadow\s*:\s*0\s+4px\s+6px[^;]*;)[\s\S]*?\1", re.IGNORECASE),
     "Derinliği katmanla: küçük yüzey az, öne çıkan yüzey çok gölge alsın."),

    ("hazir-sablon-yorumu", "yuksek",
     "Şablondan kalma yorum ya da imza",
     re.compile(r"<!--\s*(Template|Theme|Generated|Created with|Powered by)", re.IGNORECASE),
     "Bu yorumları kaldır. Kodda dışarıdan gelmiş iz kalmamalı."),

    ("uretici-etiketi", "yuksek",
     "Sayfa kendini üreten aracı bildiriyor",
     re.compile(r'<meta[^>]+name=["\']generator["\']', re.IGNORECASE),
     "Üretici etiketini kaldır."),

    ("bos-baglanti", "orta",
     "Çalışmayan bağlantılar",
     re.compile(r'href=["\'](#|javascript:void\(0\))["\']'),
     "Bağlantıları gerçek hedeflere bağla; boş bağlantı yarım iş izlenimi verir."),

    ("sabit-yil", "dusuk",
     "Alt bilgide elle yazılmış yıl",
     re.compile(r"©\s*20[12]\d(?!\s*-)"),
     "Yılı koddan üret, her yıl elle güncellenmesin."),
]

AGIRLIK_SIRASI = {"yuksek": 0, "orta": 1, "dusuk": 2}
AGIRLIK_ETIKETLERI = {"yuksek": "YÜKSEK", "orta": "orta", "dusuk": "düşük"}


def _dosyalari_topla(hedef):
    hedef = Path(hedef)

    if hedef.is_file():
        return [hedef]

    dosyalar = []
    for yol in hedef.rglob("*"):
        if not yol.is_file() or yol.suffix.lower() not in TARANACAK_UZANTILAR:
            continue
        if any(parca in yol.as_posix() for parca in TARANMAYAN_DIZINLER):
            continue
        dosyalar.append(yol)
    return dosyalar


def dosya_tara(yol):
    try:
        icerik = yol.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return []

    bulgular = []
    for kod, agirlik, aciklama, desen, oneri in KURALLAR:
        eslesme = desen.search(icerik)
        if not eslesme:
            continue

        satir_no = icerik[:eslesme.start()].count("\n") + 1
        parca = " ".join(eslesme.group(0).split())[:70]

        bulgular.append({
            "kod": kod, "agirlik": agirlik, "aciklama": aciklama,
            "oneri": oneri, "satir": satir_no, "parca": parca,
        })

    return bulgular


def tara(hedef):
    sonuclar = []
    for yol in _dosyalari_topla(hedef):
        for bulgu in dosya_tara(yol):
            bulgu["dosya"] = yol
            sonuclar.append(bulgu)

    sonuclar.sort(key=lambda b: (AGIRLIK_SIRASI[b["agirlik"]], b["kod"]))
    return sonuclar


def komut_tara(args):
    hedef = Path(args.yol) if args.yol else Path(yollar.proje_kok())

    if not hedef.exists():
        print(f"Bulunamadı: {hedef}")
        return 1

    dosyalar = _dosyalari_topla(hedef)
    if not dosyalar:
        print(f"Taranacak arayüz dosyası bulunamadı: {hedef}")
        print(f"Aranan uzantılar: {', '.join(sorted(TARANACAK_UZANTILAR))}")
        return 0

    bulgular = tara(hedef)

    print(f"KALIP DENETİMİ - {len(dosyalar)} dosya tarandı")
    print("=" * 66)

    if not bulgular:
        print()
        print("Kalıp işareti bulunamadı.")
        print("Tasarım şablon hissi vermiyor.")
        return 0

    sayilar = {"yuksek": 0, "orta": 0, "dusuk": 0}
    for bulgu in bulgular:
        sayilar[bulgu["agirlik"]] += 1

    print(f"{sayilar['yuksek']} yüksek · {sayilar['orta']} orta · {sayilar['dusuk']} düşük")
    print()

    for bulgu in bulgular:
        if args.sadece_yuksek and bulgu["agirlik"] != "yuksek":
            continue

        try:
            gosterilecek = bulgu["dosya"].relative_to(hedef if hedef.is_dir() else hedef.parent)
        except ValueError:
            gosterilecek = bulgu["dosya"]

        print(f"[{AGIRLIK_ETIKETLERI[bulgu['agirlik']]}] {bulgu['aciklama']}")
        print(f"    {gosterilecek}:{bulgu['satir']}")
        print(f"    bulunan : {bulgu['parca']}")
        print(f"    yapılacak: {bulgu['oneri']}")
        print()

    if sayilar["yuksek"]:
        print("-" * 66)
        print("Yüksek ağırlıklı bulgular tek başına bile şablon hissi verir.")
        print("Teslimden önce bunların giderilmesi gerekir.")

    return 1 if sayilar["yuksek"] else 0


def komut_kurallar(args):
    print(f"ARANAN KALIPLAR ({len(KURALLAR)})")
    print("=" * 66)

    for agirlik in ("yuksek", "orta", "dusuk"):
        grup = [k for k in KURALLAR if k[1] == agirlik]
        if not grup:
            continue

        print()
        print(f"{AGIRLIK_ETIKETLERI[agirlik]} ağırlık ({len(grup)})")
        print("-" * 66)
        for kod, _, aciklama, _, oneri in grup:
            print(f"  {kod}")
            print(f"    {aciklama}")
            print(f"    yapılacak: {oneri}")
            print()

    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Kalıp denetimi")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("tara", help="Dosya ya da klasör tara")
    p.add_argument("yol", nargs="?")
    p.add_argument("--sadece-yuksek", action="store_true", dest="sadece_yuksek")
    p.set_defaults(islev=komut_tara)

    p = alt.add_parser("kurallar", help="Aranan kalıpları listele")
    p.set_defaults(islev=komut_kurallar)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
