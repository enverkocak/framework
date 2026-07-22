#!/usr/bin/env python3
"""Cihaza göre tasarım katmanı.

Tek bir düzeni küçültüp büyütmek yeterli değildir. Telefonda tek elle
kullanılan bir arayüzle, masaüstünde iki yana yayılan bir arayüz aynı
düzenin farklı boyları değil, farklı düzenlerdir.

Beş cihaz sınıfı:

    mobil       tek sütun, büyük dokunma hedefi, alt gezinme
    büyük-mobil tek sütun ama daha rahat, yan yana ikili öğeler
    tablet      iki sütun, yan panel açılabilir, hem dokunma hem imleç
    web         çok sütun, üst gezinme, imleç odaklı
    masaüstü    geniş ekran, kenarlar sınırlanır, okuma genişliği korunur

Ayrıca cihazın kendisi de tanınır: dokunmatik mi, ince imleç mi, hareket
azaltma isteniyor mu, ekran yoğunluğu ne.

Komutlar:
    liste      Cihaz sınıfları ve eşikleri
    css        Cihaz katmanı CSS'i üret
    iskelet    Bir düzen için cihaz iskeleti üret
    denetle    Bir projenin cihaz uyumunu ölç

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

# (anahtar, ad, alt sınır px, üst sınır px, açıklama)
CIHAZ_SINIFLARI = [
    ("mobil", "Mobil", 0, 479,
     "Tek sütun · tek elle kullanım · alt gezinme · büyük dokunma hedefi"),
    ("buyuk-mobil", "Büyük mobil", 480, 767,
     "Tek sütun ama rahat · yan yana ikili öğeler · alt gezinme"),
    ("tablet", "Tablet", 768, 1023,
     "İki sütun · açılır yan panel · hem dokunma hem imleç"),
    ("web", "Web", 1024, 1439,
     "Çok sütun · üst gezinme · imleç odaklı · üzerine gelme etkileri"),
    ("masaustu", "Masaüstü", 1440, None,
     "Geniş ekran · kenarlar sınırlanır · okuma genişliği korunur"),
]

# Dokunma hedefi en az bu kadar olmalı (WCAG ve platform kılavuzları)
EN_KUCUK_DOKUNMA = 44

# Okuma genişliği: satır başına karakter
OKUMA_GENISLIGI = "68ch"

# Cihaz uyumunu bozan kalıplar
DENETIMLER = [
    ("goruntu-alani-yok", "yuksek",
     "Görüntü alanı etiketi yok",
     re.compile(r"<head\b(?![\s\S]{0,3000}?name=[\"']viewport)", re.IGNORECASE),
     'Mobilde sayfa masaüstü genişliğinde açılır. Ekle: '
     '<meta name="viewport" content="width=device-width, initial-scale=1">',
     {".html", ".htm"}),

    ("olcek-kilitli", "yuksek",
     "Yakınlaştırma kapatılmış",
     re.compile(r"user-scalable\s*=\s*no|maximum-scale\s*=\s*1", re.IGNORECASE),
     "Görme güçlüğü olan kullanıcı yakınlaştıramaz. Bu sınırı kaldır.",
     {".html", ".htm"}),

    ("sabit-genislik", "yuksek",
     "Sabit piksel genişliği",
     # min-width ve max-width HARİÇ: onlar kesme noktası ve üst sınır belirtir,
     # sorun olan sabit 'width' değeridir.
     re.compile(r"(?<![-a-z])width\s*:\s*(?!auto|100%|inherit)\d{3,}px",
                re.IGNORECASE),
     "Sabit genişlik küçük ekranda yatay kaydırma üretir. "
     "max-width ve yüzde kullan.",
     {".css", ".scss", ".html", ".htm"}),

    ("kesme-noktasi-yok", "yuksek",
     "Hiç kesme noktası yok",
     re.compile(r"^(?![\s\S]*@media[^{]*(min-width|max-width))[\s\S]*$",
                re.IGNORECASE),
     "Tek düzen bütün cihazlara sunulmuş. Cihaz sınıflarına ayır.",
     {".css", ".scss"}),

    ("kucuk-dokunma", "orta",
     "Dokunma hedefi küçük olabilir",
     re.compile(r"(height|min-height)\s*:\s*([0-2]?\d|3[0-9])px", re.IGNORECASE),
     f"Dokunma hedefi en az {EN_KUCUK_DOKUNMA}px olmalı; parmak imleç kadar ince değil.",
     {".css", ".scss"}),

    ("yatay-tasma", "orta",
     "Yatay taşma riski",
     re.compile(r"overflow-x\s*:\s*(scroll|auto)\s*;?\s*}?\s*$", re.IGNORECASE | re.MULTILINE),
     "Sayfa gövdesi yatay kaymamalı. Taşan öğeyi kendi kabına al.",
     {".css", ".scss"}),

    ("ustune-gelme-bagimli", "orta",
     "Yalnız üzerine gelmeyle açılan içerik",
     re.compile(r":hover\s*\{[^}]*\b(display\s*:\s*block|visibility\s*:\s*visible)",
                re.IGNORECASE),
     "Dokunmatik ekranda üzerine gelme yoktur. Tıklamayla da açılmalı.",
     {".css", ".scss"}),

    ("sabit-yazi-boyutu", "dusuk",
     "Piksel cinsinden yazı boyutu",
     re.compile(r"font-size\s*:\s*\d+px", re.IGNORECASE),
     "rem kullan; kullanıcının yazı boyutu tercihi geçerli olsun.",
     {".css", ".scss"}),

    ("hareket-sinirlanmamis", "dusuk",
     "Hareket azaltma isteği karşılanmamış",
     re.compile(r"^(?![\s\S]*prefers-reduced-motion)[\s\S]*\b(animation|transition)\s*:",
                re.IGNORECASE),
     "Hareket rahatsızlığı olan kullanıcılar için "
     "@media (prefers-reduced-motion: reduce) ekle.",
     {".css", ".scss"}),
]

AGIRLIK_ETIKETLERI = {"yuksek": "YÜKSEK", "orta": "orta", "dusuk": "düşük"}
AGIRLIK_SIRASI = {"yuksek": 0, "orta": 1, "dusuk": 2}

TARANMAYAN = ("/node_modules/", "/.git/", "/vendor/", "/dist/", "/build/",
              "/_arsiv/", "/_calisma/")


def sinif_bul(genislik):
    for anahtar, ad, alt, ust, _ in CIHAZ_SINIFLARI:
        if genislik >= alt and (ust is None or genislik <= ust):
            return anahtar, ad
    return "masaustu", "Masaüstü"


def css_uret():
    """Cihaz katmanı CSS'i - kimlik CSS'inin üstüne gelir."""
    satirlar = [
        "/* Cihaz katmanı",
        "",
        "   Beş cihaz sınıfı. Her biri ayrı bir düzen; aynı düzenin",
        "   büyütülmüş hâli değil.",
        "",
        "   Sıra küçükten büyüğe: önce mobil yazılır, üstüne eklenir.",
        "   Böylece en kısıtlı cihaz eksik kalmaz. */",
        "",
        ":root {",
        f"  --okuma-genisligi: {OKUMA_GENISLIGI};",
        f"  --dokunma-hedefi: {EN_KUCUK_DOKUNMA}px;",
        "  --kenar-bosluk: var(--aralik-4, 16px);",
        "  --sutun: 1;",
        "}",
        "",
        "/* Yatay kayma hiçbir cihazda olmamalı */",
        "html, body { max-width: 100%; overflow-x: hidden; }",
        "img, video, canvas, svg, table { max-width: 100%; height: auto; }",
        "",
        "/* Dokunma hedefleri parmak ölçüsünde */",
        "button, a[role=\"button\"], input[type=\"submit\"], .dokunulabilir {",
        "  min-height: var(--dokunma-hedefi);",
        "  min-width: var(--dokunma-hedefi);",
        "}",
        "",
        "/* Okuma genişliği: uzun satır okunmaz */",
        "p, li, blockquote { max-width: var(--okuma-genisligi); }",
        "",
    ]

    for anahtar, ad, alt, ust, aciklama in CIHAZ_SINIFLARI:
        satirlar += [f"/* {ad} — {aciklama} */"]

        if alt == 0:
            satirlar.append(f".sinif-{anahtar} {{ display: block; }}")
            satirlar += [
                ":root {",
                "  --sutun: 1;",
                "  --kenar-bosluk: var(--aralik-4, 16px);",
                "}",
                "",
                "/* Gezinme altta: başparmak oraya ulaşır */",
                ".gezinme { position: fixed; bottom: 0; left: 0; right: 0; }",
                "",
            ]
            continue

        satirlar.append(f"@media (min-width: {alt}px) {{")
        satirlar.append("  :root {")

        if anahtar == "buyuk-mobil":
            satirlar += ["    --sutun: 1;",
                         "    --kenar-bosluk: var(--aralik-5, 24px);"]
        elif anahtar == "tablet":
            satirlar += ["    --sutun: 2;",
                         "    --kenar-bosluk: var(--aralik-6, 32px);"]
        elif anahtar == "web":
            satirlar += ["    --sutun: 3;",
                         "    --kenar-bosluk: var(--aralik-7, 48px);"]
        else:
            satirlar += ["    --sutun: 4;",
                         "    --kenar-bosluk: var(--aralik-8, 64px);"]

        satirlar.append("  }")

        if anahtar == "tablet":
            satirlar += [
                "",
                "  /* Gezinme üste taşınır, yan panel açılabilir */",
                "  .gezinme { position: static; }",
                "  .yan-panel { display: block; }",
            ]
        elif anahtar == "masaustu":
            satirlar += [
                "",
                "  /* Geniş ekranda içerik kenarlara yapışmaz */",
                "  .kapsayici { max-width: 1320px; margin-inline: auto; }",
            ]

        satirlar += ["}", ""]

    satirlar += [
        "/* Izgara, sütun sayısını cihazdan alır */",
        ".izgara {",
        "  display: grid;",
        "  grid-template-columns: repeat(var(--sutun), minmax(0, 1fr));",
        "  gap: var(--aralik-4, 16px);",
        "}",
        "",
        "/* CİHAZIN KENDİSİ",
        "   Ekran genişliği tek başına yetmez: 1024px'lik bir dokunmatik",
        "   ekran, aynı genişlikteki bir dizüstünden farklı davranmalı. */",
        "",
        "/* Dokunmatik: hedefler büyür, üzerine gelme etkileri kapanır */",
        "@media (hover: none) and (pointer: coarse) {",
        "  :root { --dokunma-hedefi: 48px; }",
        "  .ustune-gelince { display: none; }",
        "  .dokununca { display: block; }",
        "}",
        "",
        "/* İnce imleç: üzerine gelme etkileri açılır */",
        "@media (hover: hover) and (pointer: fine) {",
        "  .ustune-gelince { display: block; }",
        "}",
        "",
        "/* Yatay tutulan telefon: yükseklik kısıtlı */",
        "@media (max-height: 480px) and (orientation: landscape) {",
        "  .gezinme { position: static; }",
        "  .tam-ekran { min-height: auto; }",
        "}",
        "",
        "/* Hareket azaltma isteği: saygı gösterilir */",
        "@media (prefers-reduced-motion: reduce) {",
        "  *, *::before, *::after {",
        "    animation-duration: 0.01ms !important;",
        "    animation-iteration-count: 1 !important;",
        "    transition-duration: 0.01ms !important;",
        "    scroll-behavior: auto !important;",
        "  }",
        "}",
        "",
        "/* Yoğun ekran: ince çizgiler kaybolmasın */",
        "@media (min-resolution: 2dppx) {",
        "  .ince-cizgi { border-width: 0.5px; }",
        "}",
        "",
        "/* Yazdırma: gezinme ve süs çıkar */",
        "@media print {",
        "  .gezinme, .yan-panel, .sus { display: none; }",
        "  body { max-width: none; }",
        "}",
        "",
    ]

    return "\n".join(satirlar)


def iskelet_uret(baslik="Sayfa"):
    """Cihaz sınıflarına göre çalışan bir sayfa iskeleti."""
    return f"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{baslik}</title>
<link rel="stylesheet" href="kimlik.css">
<link rel="stylesheet" href="cihaz.css">
</head>
<body>

<header class="ust">
  <a class="marka" href="/">{baslik}</a>
</header>

<main class="kapsayici">
  <section class="giris">
    <h1>Başlık</h1>
    <p>Bu metin okuma genişliğiyle sınırlanır; uzun satır okunmaz.</p>
  </section>

  <section class="izgara">
    <article>Birinci</article>
    <article>İkinci</article>
    <article>Üçüncü</article>
  </section>
</main>

<nav class="gezinme">
  <a href="/">Ana sayfa</a>
  <a href="/iletisim">İletişim</a>
</nav>

</body>
</html>
"""


def _dosyalar(hedef):
    hedef = Path(hedef)
    if hedef.is_file():
        return [hedef]

    uzantilar = set()
    for denetim in DENETIMLER:
        uzantilar |= denetim[-1]

    return [y for y in hedef.rglob("*")
            if y.is_file() and y.suffix.lower() in uzantilar
            and not any(p in y.as_posix() for p in TARANMAYAN)]


def denetle(hedef):
    bulgular = []

    for yol in _dosyalar(hedef):
        uzanti = yol.suffix.lower()
        try:
            icerik = yol.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for kod, agirlik, aciklama, desen, oneri, uzantilar in DENETIMLER:
            if uzanti not in uzantilar:
                continue

            eslesme = desen.search(icerik)
            if not eslesme:
                continue

            bulgular.append({
                "kod": kod, "agirlik": agirlik, "aciklama": aciklama,
                "oneri": oneri, "dosya": yol,
                "satir": icerik[:eslesme.start()].count("\n") + 1,
            })

    return sorted(bulgular, key=lambda b: (AGIRLIK_SIRASI[b["agirlik"]], b["kod"]))


# ---------------------------------------------------------------- komutlar

def komut_liste(args):
    print("CİHAZ SINIFLARI")
    print("=" * 74)
    print()

    for anahtar, ad, alt, ust, aciklama in CIHAZ_SINIFLARI:
        aralik = f"{alt}px+" if ust is None else f"{alt}-{ust}px"
        print(f"  {ad:<14} {aralik:<14} {aciklama}")

    print()
    print("EKRAN GENİŞLİĞİ TEK BAŞINA YETMEZ")
    print("-" * 74)
    print("  Ayrıca bakılır:")
    print("    dokunmatik mı, ince imleç mi   (hover / pointer)")
    print("    yatay mı dikey mi              (orientation)")
    print("    hareket azaltma isteniyor mu   (prefers-reduced-motion)")
    print("    ekran yoğunluğu                (min-resolution)")
    print()
    print(f"  Dokunma hedefi en az: {EN_KUCUK_DOKUNMA}px (dokunmatikte 48px)")
    print(f"  Okuma genişliği     : {OKUMA_GENISLIGI}")

    if args.genislik:
        anahtar, ad = sinif_bul(args.genislik)
        print()
        print(f"{args.genislik}px → {ad} ({anahtar})")

    return 0


def komut_css(args):
    icerik = css_uret()

    if args.hedef:
        yol = Path(args.hedef)
        yol.parent.mkdir(parents=True, exist_ok=True)
        yol.write_text(icerik, encoding="utf-8")
        print(f"Yazıldı: {yol}")
        return 0

    print(icerik)
    return 0


def komut_iskelet(args):
    icerik = iskelet_uret(args.baslik or "Sayfa")

    if args.hedef:
        yol = Path(args.hedef)
        yol.parent.mkdir(parents=True, exist_ok=True)
        yol.write_text(icerik, encoding="utf-8")
        print(f"Yazıldı: {yol}")
        return 0

    print(icerik)
    return 0


def komut_denetle(args):
    hedef = Path(args.yol) if args.yol else Path(yollar.proje_kok())

    if not hedef.exists():
        print(f"Bulunamadı: {hedef}")
        return 1

    dosyalar = _dosyalar(hedef)

    print(f"CİHAZ UYUMU DENETİMİ - {hedef.name}")
    print("=" * 70)

    if not dosyalar:
        print()
        print("Taranacak sayfa ya da stil dosyası bulunamadı.")
        print("Bu, 'uyumlu' demek DEĞİLDİR - bakılamadı demektir.")
        return 0

    print(f"{len(dosyalar)} dosya tarandı")
    print()

    bulgular = denetle(hedef)

    if not bulgular:
        print("Cihaz uyumu sorunu bulunamadı.")
        return 0

    for bulgu in bulgular[: args.sinir]:
        try:
            gosterilecek = bulgu["dosya"].relative_to(
                hedef if hedef.is_dir() else hedef.parent)
        except ValueError:
            gosterilecek = bulgu["dosya"].name

        print(f"[{AGIRLIK_ETIKETLERI[bulgu['agirlik']]}] {bulgu['aciklama']}")
        print(f"    {gosterilecek}:{bulgu['satir']}")
        print(f"    yapılacak: {bulgu['oneri']}")
        print()

    if len(bulgular) > args.sinir:
        print(f"... ve {len(bulgular) - args.sinir} bulgu daha")
        print()

    yuksek = sum(1 for b in bulgular if b["agirlik"] == "yuksek")
    print("=" * 70)
    print(f"Toplam {len(bulgular)} bulgu · {yuksek} tanesi yüksek ağırlıklı")

    if yuksek:
        print()
        print("Yüksek ağırlıklı bulgular bir cihaz sınıfında arayüzü kullanılamaz kılar.")
        return 1

    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Cihaza göre tasarım")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("liste", help="Cihaz sınıfları")
    p.add_argument("--genislik", type=int, help="Bu genişlik hangi sınıfa düşer")
    p.set_defaults(islev=komut_liste)

    p = alt.add_parser("css", help="Cihaz katmanı CSS'i")
    p.add_argument("--hedef")
    p.set_defaults(islev=komut_css)

    p = alt.add_parser("iskelet", help="Sayfa iskeleti")
    p.add_argument("--baslik")
    p.add_argument("--hedef")
    p.set_defaults(islev=komut_iskelet)

    p = alt.add_parser("denetle", help="Cihaz uyumunu ölç")
    p.add_argument("yol", nargs="?")
    p.add_argument("--sinir", type=int, default=8)
    p.set_defaults(islev=komut_denetle)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
