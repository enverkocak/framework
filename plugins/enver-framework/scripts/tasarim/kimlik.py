#!/usr/bin/env python3
"""Tasarım kimliği üreteci - her projeye farklı bir görsel dil.

Sorun: projeler birbirine benziyor. Aynı renk, aynı tipografi, aynı boşluk
ritmi, aynı köşe yuvarlaklığı. Bakan kişi "bunlar aynı yerden çıkmış" diyor.

Çözüm: her projeye kendi görsel dili üretilir ve üretilenler kaydedilir.
Yeni bir proje, daha önce kullanılmış bir kimliğe yakın düşerse kaydırılır.
Böylece iki proje asla aynı görünmez.

Üretilenler:
    renk        ana ton, ikincil ton, vurgu, yüzey ve metin renkleri
    tipografi   başlık ve gövde yazı tipi eşleşmesi, ölçek oranı
    boşluk      aralık ritmi (dörtlü, beşli, altın oran)
    köşe        yuvarlaklık dili (keskin, yumuşak, yuvarlak, karışık)
    derinlik    gölge dili (düz, ince, katmanlı)
    karakter    düzen karakteri (editoryal, ızgara, asimetrik, sade)

Bütün renk çiftleri okunabilirlik açısından denetlenir; yeterli karşıtlığı
sağlamayan bir eşleşme üretilmez.

Komutlar:
    üret       Bu projeye kimlik üret
    göster     Mevcut kimliği göster
    css        Kimliği CSS değişkenlerine çevir
    liste      Kullanılmış bütün kimlikler
    denetle    Kimlik okunabilirlik ölçütlerini karşılıyor mu

Geliştirici: Enver KOCAK
"""

import argparse
import colorsys
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "hafiza"))

import hafiza  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

KIMLIK_DOSYASI = "tasarim-kimligi.json"
KAYIT_DOSYASI = "tasarim-kimlikleri.json"

# İki kimliğin ana tonu arasındaki en küçük açı farkı.
# Bunun altına düşerse gözle "aynı renk" olarak algılanır.
EN_KUCUK_TON_FARKI = 28

# Okunabilirlik eşikleri (WCAG AA)
METIN_KARSITLIK_ESIGI = 4.5
BUYUK_METIN_KARSITLIK_ESIGI = 3.0


# ---------------------------------------------------------------- renk

def _hsl_to_hex(ton, doygunluk, aydinlik):
    kirmizi, yesil, mavi = colorsys.hls_to_rgb(ton / 360, aydinlik, doygunluk)
    return "#{:02x}{:02x}{:02x}".format(
        round(kirmizi * 255), round(yesil * 255), round(mavi * 255))


def _hex_to_rgb(renk):
    renk = renk.lstrip("#")
    return tuple(int(renk[i:i + 2], 16) for i in (0, 2, 4))


def _isik_gucu(renk):
    """Rengin göreli parlaklığı - karşıtlık hesabının temeli."""
    bilesenler = []
    for deger in _hex_to_rgb(renk):
        oran = deger / 255
        bilesenler.append(oran / 12.92 if oran <= 0.03928
                          else ((oran + 0.055) / 1.055) ** 2.4)
    kirmizi, yesil, mavi = bilesenler
    return 0.2126 * kirmizi + 0.7152 * yesil + 0.0722 * mavi


def karsitlik(on_renk, arka_renk):
    """İki renk arasındaki karşıtlık oranı (1 ile 21 arası)."""
    a = _isik_gucu(on_renk)
    b = _isik_gucu(arka_renk)
    parlak, sonuk = max(a, b), min(a, b)
    return (parlak + 0.05) / (sonuk + 0.05)


def _okunur_metin(arka_renk, koyu="#14161a", acik="#ffffff"):
    """Arka renk üstünde hangi metin rengi daha okunur?"""
    return koyu if karsitlik(koyu, arka_renk) >= karsitlik(acik, arka_renk) else acik


def _ton_uygun_mu(ton, kullanilan_tonlar):
    """Bu ana ton daha önce kullanılmışlara çok yakın mı?"""
    for eski in kullanilan_tonlar:
        fark = abs(ton - eski) % 360
        fark = min(fark, 360 - fark)
        if fark < EN_KUCUK_TON_FARKI:
            return False
    return True


# ------------------------------------------------------------ seçenekler

# Yazı tipi eşleşmeleri. Hepsi yaygın olarak bulunan yığınlar; dışarıdan
# dosya yüklemeye gerek kalmadan farklı karakterler verirler.
TIPOGRAFI_SECENEKLERI = [
    {"ad": "geometrik", "baslik": '"Futura", "Century Gothic", "Avenir", sans-serif',
     "govde": '"Avenir Next", "Segoe UI", system-ui, sans-serif', "olcek": 1.25},
    {"ad": "hümanist", "baslik": '"Optima", "Segoe UI", "Candara", sans-serif',
     "govde": '"Segoe UI", system-ui, -apple-system, sans-serif', "olcek": 1.2},
    {"ad": "editoryal", "baslik": '"Georgia", "Iowan Old Style", "Times New Roman", serif',
     "govde": '"Segoe UI", system-ui, sans-serif', "olcek": 1.333},
    {"ad": "klasik", "baslik": '"Palatino Linotype", "Book Antiqua", Palatino, serif',
     "govde": '"Georgia", "Cambria", serif', "olcek": 1.2},
    {"ad": "teknik", "baslik": '"Segoe UI Semibold", "Roboto", system-ui, sans-serif',
     "govde": '"Consolas", "SF Mono", "Menlo", monospace', "olcek": 1.18},
    {"ad": "dar", "baslik": '"Haettenschweiler", "Impact", "Arial Narrow", sans-serif',
     "govde": '"Arial", "Helvetica Neue", sans-serif', "olcek": 1.414},
    {"ad": "yumuşak", "baslik": '"Trebuchet MS", "Verdana", sans-serif',
     "govde": '"Verdana", "Tahoma", sans-serif', "olcek": 1.15},
    {"ad": "keskin", "baslik": '"Arial Black", "Helvetica Neue", sans-serif',
     "govde": '"Helvetica Neue", Arial, sans-serif', "olcek": 1.5},
]

BOSLUK_SECENEKLERI = [
    {"ad": "dörtlü", "temel": 4, "adimlar": [4, 8, 12, 16, 24, 32, 48, 64, 96]},
    {"ad": "beşli", "temel": 5, "adimlar": [5, 10, 15, 20, 30, 45, 60, 90, 120]},
    {"ad": "altılı", "temel": 6, "adimlar": [6, 12, 18, 24, 36, 48, 72, 96, 144]},
    {"ad": "altın", "temel": 8, "adimlar": [8, 13, 21, 34, 55, 89, 144, 233, 377]},
    {"ad": "geniş", "temel": 8, "adimlar": [8, 16, 32, 56, 88, 128, 176, 240, 320]},
]

KOSE_SECENEKLERI = [
    {"ad": "keskin", "kucuk": "0", "orta": "0", "buyuk": "0", "tam": "0"},
    {"ad": "az yumuşak", "kucuk": "2px", "orta": "3px", "buyuk": "4px", "tam": "4px"},
    {"ad": "yumuşak", "kucuk": "4px", "orta": "8px", "buyuk": "12px", "tam": "999px"},
    {"ad": "yuvarlak", "kucuk": "8px", "orta": "14px", "buyuk": "22px", "tam": "999px"},
    {"ad": "karışık", "kucuk": "2px", "orta": "12px", "buyuk": "2px", "tam": "999px"},
    {"ad": "tek yön", "kucuk": "0 8px 0 8px", "orta": "0 16px 0 16px",
     "buyuk": "0 24px 0 24px", "tam": "999px"},
]

DERINLIK_SECENEKLERI = [
    {"ad": "düz", "kucuk": "none", "orta": "none",
     "buyuk": "none", "kenar": "1px solid"},
    {"ad": "ince", "kucuk": "0 1px 2px rgba(0,0,0,.06)",
     "orta": "0 2px 6px rgba(0,0,0,.08)", "buyuk": "0 6px 16px rgba(0,0,0,.10)",
     "kenar": "1px solid"},
    {"ad": "katmanlı", "kucuk": "0 1px 3px rgba(0,0,0,.10)",
     "orta": "0 4px 12px rgba(0,0,0,.12)", "buyuk": "0 12px 32px rgba(0,0,0,.16)",
     "kenar": "none"},
    {"ad": "sert", "kucuk": "3px 3px 0 currentColor",
     "orta": "5px 5px 0 currentColor", "buyuk": "8px 8px 0 currentColor",
     "kenar": "2px solid"},
]

KARAKTER_SECENEKLERI = [
    {"ad": "editoryal", "aciklama": "Geniş kenar boşlukları, güçlü tipografi, az görsel"},
    {"ad": "ızgara", "aciklama": "Belirgin ızgara, hizalı bloklar, düzenli ritim"},
    {"ad": "asimetrik", "aciklama": "Dengesiz yerleşim, kayan bloklar, hareketli his"},
    {"ad": "sade", "aciklama": "Az öğe, çok boşluk, tek vurgu"},
    {"ad": "yoğun", "aciklama": "Bilgi yoğun, sıkı yerleşim, panel hissi"},
    {"ad": "katmanlı", "aciklama": "Üst üste binen bloklar, derinlik hissi"},
]

DOYGUNLUK_SECENEKLERI = [
    {"ad": "sönük", "ana": 0.28, "vurgu": 0.42},
    {"ad": "dengeli", "ana": 0.45, "vurgu": 0.62},
    {"ad": "canlı", "ana": 0.62, "vurgu": 0.78},
    {"ad": "yoğun", "ana": 0.75, "vurgu": 0.88},
]

# İkincil rengin ana renge göre konumu
UYUM_SECENEKLERI = [
    {"ad": "komşu", "fark": 32},
    {"ad": "üçlü", "fark": 120},
    {"ad": "karşıt", "fark": 180},
    {"ad": "bölünmüş", "fark": 150},
    {"ad": "tek renk", "fark": 12},
]


# ---------------------------------------------------------------- kayıt

def kayit_yolu():
    return hafiza.hafiza_dosyasi(KAYIT_DOSYASI)


def kullanilan_kimlikler():
    return hafiza.json_oku(kayit_yolu(), {"kimlikler": {}}).get("kimlikler", {})


def kimlik_kaydet(proje_adi, kimlik):
    yol = kayit_yolu()
    veri = hafiza.json_oku(yol, {"kimlikler": {}})
    veri.setdefault("kimlikler", {})
    veri["kimlikler"][proje_adi] = {
        "ton": kimlik["renk"]["ton"],
        "tipografi": kimlik["tipografi"]["ad"],
        "bosluk": kimlik["bosluk"]["ad"],
        "kose": kimlik["kose"]["ad"],
        "derinlik": kimlik["derinlik"]["ad"],
        "karakter": kimlik["karakter"]["ad"],
        "uretim": hafiza.zaman_metni(),
    }
    hafiza.json_yaz(yol, veri)


def kimlik_yolu(kok=None):
    return Path(kok or yollar.proje_kok()) / ".claude" / KIMLIK_DOSYASI


def kimlik_oku(kok=None):
    yol = kimlik_yolu(kok)
    if not yol.is_file():
        return None
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def kimlik_yaz(kimlik, kok=None):
    yol = kimlik_yolu(kok)
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(kimlik, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    return yol


# ---------------------------------------------------------------- üretim

def _tohum(metin, ek=""):
    ham = hashlib.sha256(f"{metin}|{ek}".encode("utf-8")).digest()
    return int.from_bytes(ham[:8], "big")


def _sec(secenekler, tohum, kaydirma=0):
    return secenekler[(tohum + kaydirma) % len(secenekler)]


def uret(proje_adi, tohum_eki="", kacinilacak_tonlar=None):
    """Bir projeye görsel kimlik üret."""
    kacinilacak_tonlar = kacinilacak_tonlar or []

    tohum = _tohum(proje_adi, tohum_eki)

    # Ana ton: kullanılmış tonlardan yeterince uzak olana kadar kaydır
    ton = tohum % 360
    denemeler = 0
    while not _ton_uygun_mu(ton, kacinilacak_tonlar) and denemeler < 360:
        ton = (ton + EN_KUCUK_TON_FARKI) % 360
        denemeler += 1

    doygunluk = _sec(DOYGUNLUK_SECENEKLERI, tohum, 1)
    uyum = _sec(UYUM_SECENEKLERI, tohum, 2)
    tipografi = _sec(TIPOGRAFI_SECENEKLERI, tohum, 3)
    bosluk = _sec(BOSLUK_SECENEKLERI, tohum, 5)
    kose = _sec(KOSE_SECENEKLERI, tohum, 7)
    derinlik = _sec(DERINLIK_SECENEKLERI, tohum, 11)
    karakter = _sec(KARAKTER_SECENEKLERI, tohum, 13)

    ikincil_ton = (ton + uyum["fark"]) % 360
    vurgu_ton = (ton + uyum["fark"] // 2 + 180) % 360

    # Aydınlık düzeyleri okunabilirlik sağlayacak aralıkta tutulur
    ana = _hsl_to_hex(ton, doygunluk["ana"], 0.42)
    ana_koyu = _hsl_to_hex(ton, doygunluk["ana"], 0.30)
    ana_acik = _hsl_to_hex(ton, doygunluk["ana"] * 0.5, 0.94)
    ikincil = _hsl_to_hex(ikincil_ton, doygunluk["ana"] * 0.85, 0.46)
    vurgu = _hsl_to_hex(vurgu_ton, doygunluk["vurgu"], 0.48)

    zemin_acik = _hsl_to_hex(ton, 0.10, 0.985)
    yuzey_acik = "#ffffff"
    metin_acik = _hsl_to_hex(ton, 0.18, 0.12)
    soluk_acik = _hsl_to_hex(ton, 0.10, 0.42)

    zemin_koyu = _hsl_to_hex(ton, 0.14, 0.09)
    yuzey_koyu = _hsl_to_hex(ton, 0.12, 0.14)
    metin_koyu = _hsl_to_hex(ton, 0.06, 0.94)
    soluk_koyu = _hsl_to_hex(ton, 0.08, 0.66)

    return {
        "proje": proje_adi,
        "uretim": hafiza.zaman_metni(),
        "renk": {
            "ton": ton,
            "uyum": uyum["ad"],
            "doygunluk": doygunluk["ad"],
            "ana": ana,
            "ana_koyu": ana_koyu,
            "ana_acik": ana_acik,
            "ikincil": ikincil,
            "vurgu": vurgu,
            "ana_ustu_metin": _okunur_metin(ana),
            "vurgu_ustu_metin": _okunur_metin(vurgu),
            "acik_tema": {
                "zemin": zemin_acik, "yuzey": yuzey_acik,
                "metin": metin_acik, "soluk": soluk_acik,
                "cizgi": _hsl_to_hex(ton, 0.12, 0.88),
            },
            "koyu_tema": {
                "zemin": zemin_koyu, "yuzey": yuzey_koyu,
                "metin": metin_koyu, "soluk": soluk_koyu,
                "cizgi": _hsl_to_hex(ton, 0.10, 0.24),
            },
        },
        "tipografi": tipografi,
        "bosluk": bosluk,
        "kose": kose,
        "derinlik": derinlik,
        "karakter": karakter,
    }


def denetle(kimlik):
    """Kimlik okunabilirlik ölçütlerini karşılıyor mu?"""
    sorunlar = []
    renk = kimlik["renk"]

    olcumler = [
        ("gövde metni (açık tema)", renk["acik_tema"]["metin"],
         renk["acik_tema"]["zemin"], METIN_KARSITLIK_ESIGI),
        ("soluk metin (açık tema)", renk["acik_tema"]["soluk"],
         renk["acik_tema"]["zemin"], BUYUK_METIN_KARSITLIK_ESIGI),
        ("gövde metni (koyu tema)", renk["koyu_tema"]["metin"],
         renk["koyu_tema"]["zemin"], METIN_KARSITLIK_ESIGI),
        ("soluk metin (koyu tema)", renk["koyu_tema"]["soluk"],
         renk["koyu_tema"]["zemin"], BUYUK_METIN_KARSITLIK_ESIGI),
        ("ana renk üstü metin", renk["ana_ustu_metin"], renk["ana"],
         METIN_KARSITLIK_ESIGI),
        ("vurgu üstü metin", renk["vurgu_ustu_metin"], renk["vurgu"],
         METIN_KARSITLIK_ESIGI),
    ]

    for ad, on, arka, esik in olcumler:
        oran = karsitlik(on, arka)
        if oran < esik:
            sorunlar.append(f"{ad}: karşıtlık {oran:.2f}, en az {esik} olmalı")

    return sorunlar


def css_uret(kimlik):
    """Kimliği CSS değişkenlerine çevir."""
    renk = kimlik["renk"]
    bosluk = kimlik["bosluk"]
    kose = kimlik["kose"]
    derinlik = kimlik["derinlik"]
    tipografi = kimlik["tipografi"]

    olcek = tipografi["olcek"]
    boyutlar = [round(1 * olcek ** ussu, 3) for ussu in range(0, 6)]

    aralik = "\n".join(
        f"  --aralik-{sira}: {deger}px;" for sira, deger in enumerate(bosluk["adimlar"], 1))

    yazi = "\n".join(
        f"  --yazi-{sira}: {deger}rem;" for sira, deger in enumerate(boyutlar, 1))

    return f"""/* Tasarım kimliği: {kimlik['proje']}
   Karakter: {kimlik['karakter']['ad']} - {kimlik['karakter']['aciklama']}
   Tipografi: {tipografi['ad']} · Boşluk: {bosluk['ad']} · Köşe: {kose['ad']} · Derinlik: {derinlik['ad']}

   Bu dosya üretilmiştir. Değerleri elle değiştirmek yerine kimliği
   yeniden üretmek, tutarlılığı korur. */

:root {{
  /* Renk */
  --ana: {renk['ana']};
  --ana-koyu: {renk['ana_koyu']};
  --ana-acik: {renk['ana_acik']};
  --ikincil: {renk['ikincil']};
  --vurgu: {renk['vurgu']};
  --ana-ustu: {renk['ana_ustu_metin']};
  --vurgu-ustu: {renk['vurgu_ustu_metin']};

  --zemin: {renk['acik_tema']['zemin']};
  --yuzey: {renk['acik_tema']['yuzey']};
  --metin: {renk['acik_tema']['metin']};
  --soluk: {renk['acik_tema']['soluk']};
  --cizgi: {renk['acik_tema']['cizgi']};

  /* Tipografi */
  --yazi-baslik: {tipografi['baslik']};
  --yazi-govde: {tipografi['govde']};
{yazi}

  /* Boşluk */
{aralik}

  /* Köşe */
  --kose-kucuk: {kose['kucuk']};
  --kose-orta: {kose['orta']};
  --kose-buyuk: {kose['buyuk']};
  --kose-tam: {kose['tam']};

  /* Derinlik */
  --golge-kucuk: {derinlik['kucuk']};
  --golge-orta: {derinlik['orta']};
  --golge-buyuk: {derinlik['buyuk']};
  --kenar: {derinlik['kenar']} var(--cizgi);
}}

@media (prefers-color-scheme: dark) {{
  :root {{
    --zemin: {renk['koyu_tema']['zemin']};
    --yuzey: {renk['koyu_tema']['yuzey']};
    --metin: {renk['koyu_tema']['metin']};
    --soluk: {renk['koyu_tema']['soluk']};
    --cizgi: {renk['koyu_tema']['cizgi']};
  }}
}}

:root[data-tema="koyu"] {{
  --zemin: {renk['koyu_tema']['zemin']};
  --yuzey: {renk['koyu_tema']['yuzey']};
  --metin: {renk['koyu_tema']['metin']};
  --soluk: {renk['koyu_tema']['soluk']};
  --cizgi: {renk['koyu_tema']['cizgi']};
}}

:root[data-tema="acik"] {{
  --zemin: {renk['acik_tema']['zemin']};
  --yuzey: {renk['acik_tema']['yuzey']};
  --metin: {renk['acik_tema']['metin']};
  --soluk: {renk['acik_tema']['soluk']};
  --cizgi: {renk['acik_tema']['cizgi']};
}}
"""


def ozet_metni(kimlik):
    renk = kimlik["renk"]
    sorunlar = denetle(kimlik)

    satirlar = [
        f"TASARIM KİMLİĞİ - {kimlik['proje']}",
        "=" * 56,
        "",
        f"Karakter  : {kimlik['karakter']['ad']} - {kimlik['karakter']['aciklama']}",
        f"Tipografi : {kimlik['tipografi']['ad']} (ölçek {kimlik['tipografi']['olcek']})",
        f"Boşluk    : {kimlik['bosluk']['ad']} ritmi",
        f"Köşe      : {kimlik['kose']['ad']}",
        f"Derinlik  : {kimlik['derinlik']['ad']}",
        "",
        f"Renk uyumu: {renk['uyum']} · doygunluk: {renk['doygunluk']} · ana ton: {renk['ton']}°",
        f"  ana     {renk['ana']}",
        f"  ikincil {renk['ikincil']}",
        f"  vurgu   {renk['vurgu']}",
        "",
    ]

    if sorunlar:
        satirlar.append("OKUNABİLİRLİK SORUNLARI:")
        satirlar += [f"  - {s}" for s in sorunlar]
    else:
        satirlar.append("Okunabilirlik: bütün renk çiftleri ölçütü karşılıyor.")

    return "\n".join(satirlar)


# ---------------------------------------------------------------- komutlar

def komut_uret(args):
    kok = yollar.proje_kok()
    proje_adi = args.proje or yollar.proje_adi(kok)

    if kimlik_oku(kok) and not args.uzerine_yaz:
        print("Bu projenin tasarım kimliği zaten var.")
        print("Yeniden üretmek için --uzerine-yaz kullan.")
        print("(Yeniden üretmek görsel dili tamamen değiştirir.)")
        return 1

    kullanilanlar = kullanilan_kimlikler()
    kacinilacak = [k["ton"] for ad, k in kullanilanlar.items() if ad != proje_adi]

    kimlik = uret(proje_adi, args.tohum or "", kacinilacak)

    sorunlar = denetle(kimlik)
    deneme = 0
    while sorunlar and deneme < 24:
        deneme += 1
        kimlik = uret(proje_adi, f"{args.tohum or ''}#{deneme}", kacinilacak)
        sorunlar = denetle(kimlik)

    if sorunlar:
        print("Okunabilirlik ölçütlerini karşılayan kimlik üretilemedi:")
        for sorun in sorunlar:
            print(f"  - {sorun}")
        return 1

    yol = kimlik_yaz(kimlik, kok)
    kimlik_kaydet(proje_adi, kimlik)

    print(ozet_metni(kimlik))
    print()
    print(f"Kaydedildi: {yol}")

    if kacinilacak:
        print(f"{len(kacinilacak)} kullanılmış kimlikten uzak tutuldu.")

    return 0


def komut_goster(args):
    kimlik = kimlik_oku()
    if kimlik is None:
        print("Bu projenin tasarım kimliği yok.")
        print("Üretmek için: python kimlik.py uret")
        return 1

    print(ozet_metni(kimlik))
    return 0


def komut_css(args):
    kimlik = kimlik_oku()
    if kimlik is None:
        print("Tasarım kimliği yok. Önce: python kimlik.py uret")
        return 1

    icerik = css_uret(kimlik)

    if args.hedef:
        hedef = Path(args.hedef)
        hedef.parent.mkdir(parents=True, exist_ok=True)
        hedef.write_text(icerik, encoding="utf-8")
        print(f"Yazıldı: {hedef}")
        return 0

    print(icerik)
    return 0


def komut_liste(args):
    kullanilanlar = kullanilan_kimlikler()

    if not kullanilanlar:
        print("Kayıtlı tasarım kimliği yok.")
        return 0

    print(f"KULLANILMIŞ TASARIM KİMLİKLERİ ({len(kullanilanlar)})")
    print("=" * 72)
    print(f"  {'proje':<28} {'ton':>5}  {'tipografi':<12} {'karakter':<12} {'köşe'}")
    print("  " + "-" * 68)

    for ad, kayit in sorted(kullanilanlar.items(), key=lambda i: i[1]["ton"]):
        print(f"  {ad[:27]:<28} {kayit['ton']:>4}°  "
              f"{kayit['tipografi']:<12} {kayit['karakter']:<12} {kayit['kose']}")

    # Tekrar denetimi
    tonlar = {}
    for ad, kayit in kullanilanlar.items():
        tonlar.setdefault(kayit["ton"], []).append(ad)

    cakisan = {ton: adlar for ton, adlar in tonlar.items() if len(adlar) > 1}
    if cakisan:
        print()
        print("DİKKAT: Aynı ana tonu paylaşan projeler var:")
        for ton, adlar in cakisan.items():
            print(f"  {ton}°: {', '.join(adlar)}")

    return 0


def komut_denetle(args):
    kimlik = kimlik_oku()
    if kimlik is None:
        print("Tasarım kimliği yok.")
        return 1

    sorunlar = denetle(kimlik)
    if not sorunlar:
        print("Bütün renk çiftleri okunabilirlik ölçütünü karşılıyor.")
        return 0

    print(f"{len(sorunlar)} sorun:")
    for sorun in sorunlar:
        print(f"  - {sorun}")
    return 1


def main():
    ayristirici = argparse.ArgumentParser(description="Tasarım kimliği")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("uret", help="Kimlik üret")
    p.add_argument("--proje")
    p.add_argument("--tohum", help="Aynı projeye farklı kimlik üretmek için")
    p.add_argument("--uzerine-yaz", action="store_true", dest="uzerine_yaz")
    p.set_defaults(islev=komut_uret)

    p = alt.add_parser("goster", help="Mevcut kimliği göster")
    p.set_defaults(islev=komut_goster)

    p = alt.add_parser("css", help="CSS değişkenlerine çevir")
    p.add_argument("--hedef")
    p.set_defaults(islev=komut_css)

    p = alt.add_parser("liste", help="Kullanılmış kimlikler")
    p.set_defaults(islev=komut_liste)

    p = alt.add_parser("denetle", help="Okunabilirlik denetimi")
    p.set_defaults(islev=komut_denetle)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
