#!/usr/bin/env python3
"""Proje içi index üreteci.

Her ana klasöre bir INDEX.md yazar: burada ne var, neyi ne için yaptık,
ne işe yarıyor. Altı ay sonra "bu dosya neydi" sorusunun cevabı burada durur.

Açıklamalar şu sırayla aranır:
  1. Dosyanın ön bilgisindeki description alanı
  2. Kod dosyalarında ilk belge metni (docstring)
  3. Belgelerde ilk anlamlı satır
  4. Elle yazılmış açıklamalar.json kaydı

Elle liste tutulmaz. Yeni dosya eklenince index yeniden üretilir.

Komutlar:
    üret     Index dosyalarını üret
    kontrol  Index güncel mi (üretmeden bakar)

Geliştirici: Enver KOCAK
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))

import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

# Üretilen belgenin adı bilinçli olarak İÇİNDEKİLER.md.
#
# Önce INDEX.md kullanılmıştı ve bu bir veri kaybına yol açtı: Windows dosya
# sistemi büyük/küçük harf ayırmadığı için, içinde index.md bulunan bir klasöre
# INDEX.md yazmak o dosyanın üzerine yazıyor. commands/index.md böyle silindi.
# Türkçe ad hem çakışmayı tamamen ortadan kaldırıyor hem de dil kuralına uyuyor.
INDEX_ADI = "ICINDEKILER.md"
ELLE_ACIKLAMA = "aciklamalar.json"

ATLANACAK_DIZINLER = {
    ".git", ".claude", ".claude-plugin", "node_modules", "vendor", "__pycache__",
    "dist", "build", "_arsiv", "_calisma", "gunluk", "kasa", "vault",
    ".venv", "venv", ".idea", ".vscode",
    # Plugin bilesen dizinleri: Claude Code buradaki her .md'yi komut/ajan/
    # beceri sanar. Uretilen ICINDEKILER.md buralara YAZILMAZ, yoksa sahte
    # komut olusur ve "claude plugin validate" uyari verir.
    "commands", "agents", "skills", "hooks",
}

ATLANACAK_DOSYALAR = {INDEX_ADI, ELLE_ACIKLAMA, ".gitignore", ".DS_Store"}

KOD_UZANTILARI = {".py", ".js", ".ts", ".php", ".sh", ".ps1"}
BELGE_UZANTILARI = {".md", ".txt"}


def _on_bilgi(icerik):
    """Belgenin başındaki ön bilgi bloğunu oku."""
    eslesme = re.match(r"^---\s*\n(.*?)\n---\s*\n", icerik, re.DOTALL)
    if not eslesme:
        return {}

    sonuc = {}
    for satir in eslesme.group(1).splitlines():
        if ":" in satir and not satir.startswith((" ", "-", "#")):
            ad, _, deger = satir.partition(":")
            sonuc[ad.strip()] = deger.strip().strip("\"'")
    return sonuc


def _belge_metni(icerik):
    """Kod dosyasının başındaki açıklama metnini al."""
    eslesme = re.search(r'^\s*(?:#!.*\n)?\s*"""(.*?)"""', icerik, re.DOTALL)
    if eslesme:
        satirlar = [s.strip() for s in eslesme.group(1).strip().splitlines() if s.strip()]
        if satirlar:
            return satirlar[0]

    # Kabuk ve PowerShell dosyalarında baştaki yorum satırları
    satirlar = icerik.splitlines()
    for satir in satirlar[:12]:
        temiz = satir.strip()
        if temiz.startswith("#") and len(temiz) > 3 and not temiz.startswith("#!"):
            aday = temiz.lstrip("#").strip(" =-")
            if aday:
                return aday
    return ""


def aciklama_bul(yol, elle):
    """Bir dosyanın ne işe yaradığını bul."""
    ad = yol.name

    if ad in elle:
        return elle[ad]

    uzanti = yol.suffix.lower()

    try:
        icerik = yol.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""

    if uzanti in BELGE_UZANTILARI:
        on = _on_bilgi(icerik)
        for anahtar in ("description", "aciklama"):
            if on.get(anahtar):
                return on[anahtar]

        govde = re.sub(r"^---\s*\n.*?\n---\s*\n", "", icerik, flags=re.DOTALL)
        for satir in govde.splitlines():
            temiz = satir.strip()
            if temiz and not temiz.startswith(("#", "`", "|", ">", "-", "*", "_")):
                return temiz[:150]
        return ""

    if uzanti in KOD_UZANTILARI:
        return _belge_metni(icerik)[:150]

    if uzanti == ".json":
        try:
            veri = json.loads(icerik)
        except json.JSONDecodeError:
            return ""
        if isinstance(veri, dict):
            for anahtar in ("_aciklama", "aciklama", "description"):
                deger = veri.get(anahtar)
                if isinstance(deger, list):
                    return " ".join(str(s) for s in deger if s)[:150]
                if isinstance(deger, str):
                    return deger[:150]
        return ""

    return ""


def dizin_index(dizin, kok):
    """Bir dizin için index metni üret."""
    elle = {}
    elle_yolu = dizin / ELLE_ACIKLAMA
    if elle_yolu.is_file():
        try:
            elle = json.loads(elle_yolu.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            elle = {}

    alt_dizinler = []
    dosyalar = []

    for oge in sorted(dizin.iterdir()):
        if oge.name.startswith(".") and oge.name not in (".iz-muaf",):
            continue

        if oge.is_dir():
            if oge.name in ATLANACAK_DIZINLER:
                continue
            alt_index = oge / INDEX_ADI
            aciklama = ""
            if alt_index.is_file():
                icerik = alt_index.read_text(encoding="utf-8", errors="ignore")
                for satir in icerik.splitlines():
                    if satir.startswith("> "):
                        aciklama = satir[2:].strip()
                        break
            alt_dizinler.append((oge.name, elle.get(oge.name, aciklama)))
        elif oge.is_file():
            if oge.name in ATLANACAK_DOSYALAR:
                continue
            dosyalar.append((oge.name, aciklama_bul(oge, elle)))

    bagil = dizin.relative_to(kok).as_posix() or "."

    satirlar = [
        f"# {bagil} - içindekiler",
        "",
        "> Bu belge otomatik üretilir. Elle satır eklenmez;",
        "> açıklamalar dosyaların kendisinden okunur.",
        "",
    ]

    if alt_dizinler:
        satirlar += ["## Klasörler", "", "| Klasör | Ne için |", "|--------|---------|"]
        satirlar += [f"| `{ad}/` | {acik or '-'} |" for ad, acik in alt_dizinler]
        satirlar.append("")

    if dosyalar:
        satirlar += ["## Dosyalar", "", "| Dosya | Ne işe yarar |", "|-------|--------------|"]
        satirlar += [f"| `{ad}` | {acik or '-'} |" for ad, acik in dosyalar]
        satirlar.append("")

    if not alt_dizinler and not dosyalar:
        satirlar += ["Bu klasör şu an boş.", ""]

    satirlar += [
        "---",
        "",
        "Açıklaması eksik olan bir dosya varsa iki yol var:",
        "dosyanın başına açıklama yaz, ya da bu klasöre `aciklamalar.json` koy.",
        "",
    ]

    return "\n".join(satirlar)


def dizinleri_gez(kok, derinlik=3):
    """Index yazılacak dizinleri topla."""
    kok = Path(kok)
    bulunanlar = [kok]

    def gez(dizin, kalan):
        if kalan <= 0:
            return
        for oge in sorted(dizin.iterdir()):
            if not oge.is_dir() or oge.name in ATLANACAK_DIZINLER or oge.name.startswith("."):
                continue
            bulunanlar.append(oge)
            gez(oge, kalan - 1)

    gez(kok, derinlik)
    return bulunanlar


def cakisma_var_mi(dizin):
    """Bu klasörde, üretilecek adla büyük/küçük harf farkıyla çakışan dosya var mı?

    Windows dosya sistemi harf büyüklüğüne bakmaz. Böyle bir dosyanın üzerine
    yazmak, elle yazılmış içeriği sessizce yok eder. Yazmadan önce bakılır.
    """
    hedef_kucuk = INDEX_ADI.lower()

    for oge in dizin.iterdir():
        if not oge.is_file():
            continue
        if oge.name == INDEX_ADI:
            continue
        if oge.name.lower() == hedef_kucuk:
            return oge
    return None


def komut_uret(args):
    kok = Path(yollar.proje_kok())
    dizinler = dizinleri_gez(kok, args.derinlik)

    yazilan = 0
    for dizin in dizinler:
        cakisan = cakisma_var_mi(dizin)
        if cakisan:
            print(f"  ATLANDI: {dizin.relative_to(kok)} - "
                  f"'{cakisan.name}' dosyasıyla ad çakışması var, üzerine yazılmadı.")
            continue

        metin = dizin_index(dizin, kok)
        hedef = dizin / INDEX_ADI

        mevcut = ""
        if hedef.is_file():
            mevcut = hedef.read_text(encoding="utf-8", errors="ignore")

        if mevcut.strip() == metin.strip():
            continue

        hedef.write_text(metin, encoding="utf-8")
        yazilan += 1
        if args.ayrintili:
            print(f"  yazıldı: {hedef.relative_to(kok)}")

    print(f"{len(dizinler)} klasör tarandı, {yazilan} index güncellendi.")
    return 0


def komut_kontrol(args):
    kok = Path(yollar.proje_kok())
    dizinler = dizinleri_gez(kok, args.derinlik)

    eski = []
    for dizin in dizinler:
        hedef = dizin / INDEX_ADI
        metin = dizin_index(dizin, kok)

        if not hedef.is_file():
            eski.append((dizin.relative_to(kok).as_posix() or ".", "yok"))
            continue

        mevcut = hedef.read_text(encoding="utf-8", errors="ignore")
        if mevcut.strip() != metin.strip():
            eski.append((dizin.relative_to(kok).as_posix() or ".", "eski"))

    if not eski:
        print(f"{len(dizinler)} klasörün index'i güncel.")
        return 0

    print(f"{len(eski)} klasörün index'i güncel değil:")
    for ad, durum in eski:
        print(f"  [{durum}] {ad}")
    print()
    print("Güncellemek için: python proje-index.py uret")
    return 1


def main():
    ayristirici = argparse.ArgumentParser(description="Proje içi index üreteci")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("uret", help="Index dosyalarını üret")
    p.add_argument("--derinlik", type=int, default=3)
    p.add_argument("--ayrintili", action="store_true")
    p.set_defaults(islev=komut_uret)

    p = alt.add_parser("kontrol", help="Index güncel mi")
    p.add_argument("--derinlik", type=int, default=3)
    p.set_defaults(islev=komut_kontrol)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
