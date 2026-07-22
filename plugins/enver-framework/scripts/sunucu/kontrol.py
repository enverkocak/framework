#!/usr/bin/env python3
"""Teslim öncesi denetimler - güvenlik, erişilebilirlik, arama ve başarım.

Müşteriye teslim edilmeden önce bakılması gereken şeyler bir listede durur;
akılda tutulmaya çalışılmaz.

Denetimler dosya üzerinden çalışır, siteyi ayağa kaldırmak gerekmez.
Bulunamayan şey "yok" sayılmaz, "bakılamadı" sayılır - ikisi farklı şeydir.

Alanlar:
    güvenlik        Açıkta kalmış bilgi, tehlikeli kalıplar, eksik başlıklar
    erişilebilirlik Alternatif metin, etiket, başlık düzeni, dil bilgisi
    arama           Sayfa başlığı, açıklama, adres yapısı
    başarım         Büyük dosyalar, engelleyici yüklemeler

Komutlar:
    tara <yol>    Bütün denetimleri çalıştır
    liste         Hangi denetimler var

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

TARANMAYAN = ("/node_modules/", "/.git/", "/vendor/", "/dist/", "/build/",
              "/_arsiv/", "/_calisma/", "/.venv/")

SAYFA_UZANTILARI = {".html", ".htm", ".php", ".vue", ".jsx", ".tsx", ".twig"}
KOD_UZANTILARI = {".js", ".ts", ".php", ".py", ".jsx", ".tsx"}

BUYUK_DOSYA_ESIGI = 500 * 1024

# (alan, kod, ağırlık, açıklama, desen, ne yapılmalı, hangi uzantılar)
DENETIMLER = [
    # --- güvenlik ---
    ("guvenlik", "acik-anahtar", "yuksek",
     "Kaynakta açıkta anahtar ya da parola",
     re.compile(r"(?i)(api[_-]?key|secret|password|parola)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
     "Değeri kasaya taşı, kodda ortam değişkeni kullan.", KOD_UZANTILARI | SAYFA_UZANTILARI),

    ("guvenlik", "eval-kullanimi", "yuksek",
     "Dışarıdan gelen veriyi çalıştıran kalıp",
     re.compile(r"\beval\s*\(|\bnew Function\s*\(|\bdocument\.write\s*\("),
     "Bu kalıplar kod enjeksiyonuna açıktır; başka bir yol bul.", KOD_UZANTILARI),

    ("guvenlik", "sql-birlestirme", "yuksek",
     "Sorgu metni birleştirilerek kuruluyor",
     # Bayrak desenin BAŞINDA olmalı; iki parçayı birleştirirken ortada kalınca
     # Python deseni derlemiyor. Bu yüzden re.IGNORECASE ayrı veriliyor.
     re.compile(r"(SELECT|INSERT|UPDATE|DELETE)[^;'\"]{0,80}[\"']\s*\.\s*\$"
                r"|(SELECT|INSERT|UPDATE|DELETE)[^;'\"]{0,80}\+\s*(req|params|input)",
                re.IGNORECASE),
     "Hazır ifade (prepared statement) kullan.", KOD_UZANTILARI),

    ("guvenlik", "hata-gosterimi", "orta",
     "Hata ayrıntıları kullanıcıya gösteriliyor",
     re.compile(r"(?i)display_errors\s*[=,]\s*(1|on|true)|\bDEBUG\s*=\s*True"),
     "Canlıda hata ayrıntısı kapalı olmalı.", KOD_UZANTILARI),

    ("guvenlik", "http-adres", "orta",
     "Güvensiz bağlantı adresi",
     re.compile(r"[\"'](http://(?!localhost|127\.0\.0\.1)[^\"']+)[\"']"),
     "Adresleri https olarak yaz.", SAYFA_UZANTILARI | KOD_UZANTILARI),

    # --- erişilebilirlik ---
    ("erisilebilirlik", "alt-metni-yok", "yuksek",
     "Görselde alternatif metin yok",
     re.compile(r"<img(?![^>]*\balt\s*=)[^>]*>", re.IGNORECASE),
     "Her görsele alt metni yaz; ekran okuyucu onu okur.", SAYFA_UZANTILARI),

    ("erisilebilirlik", "dil-yok", "yuksek",
     "Sayfanın dili belirtilmemiş",
     re.compile(r"<html(?![^>]*\blang\s*=)[^>]*>", re.IGNORECASE),
     'Kök etikete dil ekle: <html lang="tr">', {".html", ".htm"}),

    ("erisilebilirlik", "etiketsiz-alan", "orta",
     "Form alanının etiketi yok",
     re.compile(r"<input(?![^>]*\b(aria-label|id)\s*=)[^>]*type=[\"'](?!hidden|submit)",
                re.IGNORECASE),
     "Her form alanına etiket bağla.", SAYFA_UZANTILARI),

    ("erisilebilirlik", "tiklanabilir-div", "orta",
     "Tıklanabilir öğe düğme değil",
     re.compile(r"<div[^>]*\bonclick\s*=", re.IGNORECASE),
     "Tıklanan öğe <button> olmalı; klavyeyle de kullanılabilsin.", SAYFA_UZANTILARI),

    # --- arama ---
    ("arama", "baslik-yok", "yuksek",
     "Sayfa başlığı yok",
     re.compile(r"<head\b(?![\s\S]{0,3000}?<title)", re.IGNORECASE),
     "Her sayfaya kendine özgü bir başlık yaz.", {".html", ".htm"}),

    ("arama", "aciklama-yok", "orta",
     "Sayfa açıklaması yok",
     re.compile(r"<head\b(?![\s\S]{0,3000}?name=[\"']description)", re.IGNORECASE),
     "Arama sonucunda görünecek açıklamayı ekle.", {".html", ".htm"}),

    ("arama", "govde-basligi-yok", "orta",
     "Sayfada ana başlık yok",
     re.compile(r"<body\b(?![\s\S]*?<h1)", re.IGNORECASE),
     "Her sayfada bir ana başlık bulunmalı.", {".html", ".htm"}),

    # --- başarım ---
    ("basarim", "engelleyici-betik", "orta",
     "Sayfanın açılmasını geciktiren betik",
     re.compile(r"<script(?![^>]*\b(async|defer|type=[\"']module))[^>]*\bsrc=", re.IGNORECASE),
     "Betiklere defer ya da async ekle.", SAYFA_UZANTILARI),

    ("basarim", "olcusuz-gorsel", "dusuk",
     "Görselin ölçüsü belirtilmemiş",
     re.compile(r"<img(?![^>]*\b(width|height)\s*=)[^>]*>", re.IGNORECASE),
     "Genişlik ve yükseklik ver; sayfa yüklenirken zıplamasın.", SAYFA_UZANTILARI),
]

ALAN_ADLARI = {
    "guvenlik": "GÜVENLİK",
    "erisilebilirlik": "ERİŞİLEBİLİRLİK",
    "arama": "ARAMA GÖRÜNÜRLÜĞÜ",
    "basarim": "BAŞARIM",
}

AGIRLIK_ETIKETLERI = {"yuksek": "YÜKSEK", "orta": "orta", "dusuk": "düşük"}
AGIRLIK_SIRASI = {"yuksek": 0, "orta": 1, "dusuk": 2}


def _dosyalar(hedef):
    hedef = Path(hedef)
    if hedef.is_file():
        return [hedef]

    sonuc = []
    for yol in hedef.rglob("*"):
        if not yol.is_file():
            continue
        if any(parca in yol.as_posix() for parca in TARANMAYAN):
            continue
        if yol.suffix.lower() in (SAYFA_UZANTILARI | KOD_UZANTILARI):
            sonuc.append(yol)
    return sonuc


def buyuk_dosyalar(hedef):
    """Sayfayı yavaşlatacak büyük varlıklar."""
    hedef = Path(hedef)
    if hedef.is_file():
        return []

    bulunanlar = []
    for yol in hedef.rglob("*"):
        if not yol.is_file() or any(p in yol.as_posix() for p in TARANMAYAN):
            continue
        if yol.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".webp",
                                      ".mp4", ".webm", ".pdf", ".zip"}:
            continue
        try:
            boyut = yol.stat().st_size
        except OSError:
            continue
        if boyut > BUYUK_DOSYA_ESIGI:
            bulunanlar.append((yol, boyut))

    return sorted(bulunanlar, key=lambda i: i[1], reverse=True)


def tara(hedef, alanlar=None):
    bulgular = []

    for yol in _dosyalar(hedef):
        uzanti = yol.suffix.lower()
        try:
            icerik = yol.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for alan, kod, agirlik, aciklama, desen, oneri, uzantilar in DENETIMLER:
            if alanlar and alan not in alanlar:
                continue
            if uzanti not in uzantilar:
                continue

            eslesme = desen.search(icerik)
            if not eslesme:
                continue

            bulgular.append({
                "alan": alan, "kod": kod, "agirlik": agirlik,
                "aciklama": aciklama, "oneri": oneri, "dosya": yol,
                "satir": icerik[:eslesme.start()].count("\n") + 1,
            })

    return sorted(bulgular, key=lambda b: (AGIRLIK_SIRASI[b["agirlik"]], b["alan"]))


def komut_tara(args):
    hedef = Path(args.yol) if args.yol else Path(yollar.proje_kok())

    if not hedef.exists():
        print(f"Bulunamadı: {hedef}")
        return 1

    dosyalar = _dosyalar(hedef)

    print(f"TESLİM ÖNCESİ DENETİM - {hedef.name}")
    print("=" * 70)

    if not dosyalar:
        print()
        print("Taranacak sayfa ya da kod dosyası bulunamadı.")
        print("Bu, 'sorun yok' demek DEĞİLDİR - bakılamadı demektir.")
        return 0

    print(f"{len(dosyalar)} dosya tarandı")
    print()

    alanlar = set(args.alan) if args.alan else None
    bulgular = tara(hedef, alanlar)

    if not bulgular:
        print("Denetimlerden geçti, bulgu yok.")
    else:
        gruplar = {}
        for bulgu in bulgular:
            gruplar.setdefault(bulgu["alan"], []).append(bulgu)

        for alan in ("guvenlik", "erisilebilirlik", "arama", "basarim"):
            grup = gruplar.get(alan)
            if not grup:
                continue

            print(f"{ALAN_ADLARI[alan]} ({len(grup)})")
            print("-" * 70)

            for bulgu in grup[: args.sinir]:
                try:
                    gosterilecek = bulgu["dosya"].relative_to(
                        hedef if hedef.is_dir() else hedef.parent)
                except ValueError:
                    gosterilecek = bulgu["dosya"].name

                print(f"  [{AGIRLIK_ETIKETLERI[bulgu['agirlik']]}] {bulgu['aciklama']}")
                print(f"      {gosterilecek}:{bulgu['satir']}")
                print(f"      yapılacak: {bulgu['oneri']}")
                print()

            if len(grup) > args.sinir:
                print(f"  ... ve {len(grup) - args.sinir} bulgu daha")
                print()

    # Büyük dosyalar
    if not alanlar or "basarim" in alanlar:
        buyukler = buyuk_dosyalar(hedef)
        if buyukler:
            print(f"BÜYÜK DOSYALAR ({len(buyukler)})")
            print("-" * 70)
            for yol, boyut in buyukler[:8]:
                try:
                    ad = yol.relative_to(hedef)
                except ValueError:
                    ad = yol.name
                print(f"  {boyut / 1024:>7.0f} KB  {ad}")
            print()
            print("  yapılacak: Görselleri sıkıştır, videoları dışarıdan sun.")
            print()

    yuksek = sum(1 for b in bulgular if b["agirlik"] == "yuksek")
    print("=" * 70)
    print(f"Toplam {len(bulgular)} bulgu · {yuksek} tanesi yüksek ağırlıklı")

    if yuksek:
        print()
        print("Yüksek ağırlıklı bulgular teslimden önce giderilmeli.")
        return 1

    return 0


def komut_liste(args):
    print(f"DENETİMLER ({len(DENETIMLER)})")
    print("=" * 70)

    for alan in ("guvenlik", "erisilebilirlik", "arama", "basarim"):
        grup = [d for d in DENETIMLER if d[0] == alan]
        print()
        print(f"{ALAN_ADLARI[alan]} ({len(grup)})")
        print("-" * 70)
        for _, kod, agirlik, aciklama, _, oneri, _ in grup:
            print(f"  [{AGIRLIK_ETIKETLERI[agirlik]}] {kod}")
            print(f"      {aciklama}")
            print(f"      yapılacak: {oneri}")
    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Teslim öncesi denetimler")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("tara", help="Denetimleri çalıştır")
    p.add_argument("yol", nargs="?")
    p.add_argument("--alan", action="append",
                   choices=["guvenlik", "erisilebilirlik", "arama", "basarim"])
    p.add_argument("--sinir", type=int, default=5)
    p.set_defaults(islev=komut_tara)

    p = alt.add_parser("liste", help="Denetimleri listele")
    p.set_defaults(islev=komut_liste)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
