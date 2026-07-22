#!/usr/bin/env python3
"""Hafıza katmanı - ortak okuma ve yazma işlemleri.

İki ayrı alan vardır ve bilinçli olarak ayrılmışlardır:

  hafiza/   Kalıcı, özetlenmiş, PAYLAŞILAN bilgi. Depoya girer, makineler
            arasında senkron olur. Küçük ve okunabilir kalır.

  gunluk/   Ham oturum kaydı. Makineye özeldir, depoya GİRMEZ.
            Büyüyebilir; özetlenip hafızaya aktarılır.

Böylece "nerede kaldık" bilgisi her bilgisayarda aynı olur, ham kayıt ise
üretildiği makinede kalır.

Geliştirici: Enver KOCAK
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))

import yollar  # noqa: E402

HAFIZA_ADI = "hafiza"
GUNLUK_ADI = "gunluk"

DURUM_DOSYASI = "durum.md"
KARARLAR_DOSYASI = "kararlar.md"
HATALAR_DOSYASI = "hatalar.md"
CIZELGE_DOSYASI = "degisim-cizelgesi.md"
MAKINELER_DOSYASI = "makineler.json"
OTURUMLAR_DIZINI = "oturumlar"

KOMUT_KAYDI = "komutlar.jsonl"
CIKTI_DIZINI = "ciktilar"


# ---------------------------------------------------------------- yollar

def hafiza_dizini(kok=None, olustur=True):
    """Paylaşılan hafızanın bulunduğu dizin."""
    yol = Path(kok or yollar.proje_kok()) / HAFIZA_ADI
    if olustur:
        (yol / OTURUMLAR_DIZINI).mkdir(parents=True, exist_ok=True)
    return yol


def gunluk_dizini(kok=None, olustur=True):
    """Ham oturum kaydının bulunduğu, makineye özel dizin."""
    yol = Path(kok or yollar.proje_kok()) / GUNLUK_ADI
    if olustur:
        (yol / CIKTI_DIZINI).mkdir(parents=True, exist_ok=True)
    return yol


def hafiza_dosyasi(ad, kok=None):
    return hafiza_dizini(kok) / ad


# ---------------------------------------------------------------- zaman

def simdi():
    return datetime.now()


def tarih_metni(an=None):
    return (an or simdi()).strftime("%Y-%m-%d")


def zaman_metni(an=None):
    return (an or simdi()).strftime("%Y-%m-%d %H:%M")


# ---------------------------------------------------------------- okuma ve yazma

def metin_oku(yol, varsayilan=""):
    try:
        return Path(yol).read_text(encoding="utf-8")
    except OSError:
        return varsayilan


def json_oku(yol, varsayilan=None):
    try:
        veri = json.loads(Path(yol).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return varsayilan if varsayilan is not None else {}
    return veri


def json_yaz(yol, veri):
    yol = Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def satir_ekle(yol, kayit):
    """Ham günlüğe tek bir kayıt ekler (JSONL biçimi)."""
    yol = Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)
    with open(yol, "a", encoding="utf-8") as dosya:
        dosya.write(json.dumps(kayit, ensure_ascii=False) + "\n")


def satirlari_oku(yol, sinir=None):
    """Ham günlüğü okur. Sınır verilirse son N kaydı döndürür."""
    yol = Path(yol)
    if not yol.is_file():
        return []

    kayitlar = []
    try:
        with open(yol, "r", encoding="utf-8", errors="ignore") as dosya:
            for satir in dosya:
                satir = satir.strip()
                if not satir:
                    continue
                try:
                    kayitlar.append(json.loads(satir))
                except json.JSONDecodeError:
                    # Yarım yazılmış satır olabilir; kaydı atla, akışı bozma.
                    continue
    except OSError:
        return []

    return kayitlar[-sinir:] if sinir else kayitlar


# ------------------------------------------------------- bölümlü belgeler

def bolum_ekle(yol, baslik, govde, en_uste=True):
    """Belgeye tarihli bir bölüm ekler.

    Yeni kayıtlar varsayılan olarak en üste eklenir; en güncel bilgi
    belgenin başında durur, açan kişi önce onu görür.
    """
    yol = Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)

    mevcut = metin_oku(yol)
    yeni_bolum = f"## {baslik}\n\n{govde.strip()}\n"

    if not mevcut.strip():
        yol.write_text(yeni_bolum + "\n", encoding="utf-8")
        return

    # Belgenin kendi başlığını koru, yeni bölümü onun altına yerleştir.
    satirlar = mevcut.splitlines(keepends=True)
    basi = satirlar
    govdesi = []

    for sira, satir in enumerate(satirlar):
        if satir.startswith("## "):
            basi = satirlar[:sira]
            govdesi = satirlar[sira:]
            break

    if en_uste:
        yeni = "".join(basi).rstrip() + "\n\n" + yeni_bolum + "\n" + "".join(govdesi)
    else:
        yeni = mevcut.rstrip() + "\n\n" + yeni_bolum

    yol.write_text(yeni, encoding="utf-8")


def baslik_yoksa_yaz(yol, baslik, aciklama=""):
    """Belge boşsa üstüne başlığını yazar."""
    yol = Path(yol)
    if yol.is_file() and yol.read_text(encoding="utf-8").strip():
        return

    yol.parent.mkdir(parents=True, exist_ok=True)
    metin = f"# {baslik}\n"
    if aciklama:
        metin += f"\n{aciklama}\n"
    yol.write_text(metin + "\n", encoding="utf-8")


# ---------------------------------------------------------------- gizleme

# Kayda geçmeden önce gizlenecek desenler.
# Ham günlük bile olsa parola diske düz yazılmaz.
GIZLENECEK_DESENLER = [
    re.compile(r"(?i)(parola|password|passwd|sifre|şifre|secret|token|api[_-]?key)"
               r"(\s*[:=]\s*)(\S+)"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}"),
    re.compile(r"\bghp_[A-Za-z0-9]{20,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*KEY-----"),
]


def gizle(metin):
    """Sırları kayda geçmeden önce gizler."""
    if not metin:
        return metin

    sonuc = GIZLENECEK_DESENLER[0].sub(r"\1\2[GİZLENDİ]", metin)
    for desen in GIZLENECEK_DESENLER[1:]:
        sonuc = desen.sub("[GİZLENDİ]", sonuc)
    return sonuc


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    kok = yollar.proje_kok()
    print(f"Proje  : {kok}")
    print(f"Hafıza : {hafiza_dizini(kok, olustur=False)}  (depoya girer, senkron olur)")
    print(f"Günlük : {gunluk_dizini(kok, olustur=False)}  (makineye özel, depoya girmez)")
