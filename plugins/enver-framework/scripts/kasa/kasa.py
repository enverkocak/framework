#!/usr/bin/env python3
"""Parola korumali kasa.

Kasa icerigi diskte SIFRELI durur. Parola verilmeden okunamaz.
Cozulmus icerik hicbir zaman diske yazilmaz - bellekte cozulur, ekrana verilir.

Oturum acildiginda parolanin kendisi degil, ondan turetilen anahtar
kullanici profilinde sureli olarak saklanir. Sure dolunca kasa kendiliginden kilitlenir.

Dosya bicimi (kasa.kilit):
    satir 1: ENVER-KASA-1
    satir 2: tuz (base64)
    satir 3: sifreli govde (base64)

Komutlar:
    kur       Mevcut duz metin kasayi sifreleyip kilitle
    ac        Parolayi dogrula, oturumu ac
    kilitle   Oturumu kapat
    durum     Kilitli mi acik mi
    liste     Kasadaki dosyalari listele
    oku       Bir dosyanin icerigini goster
    yaz       Bir dosyayi ekle veya guncelle
    parola    Parolayi degistir

Gelistirici: Enver KOCAK
"""

import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))

import yollar  # noqa: E402

BASLIK = "ENVER-KASA-1"
KASA_DIZIN_ADI = "kasa"
KASA_DOSYA_ADI = "kasa.kilit"

OTURUM_YOLU = Path.home() / ".claude" / "enver" / "kasa-oturum.json"
VARSAYILAN_SURE_DK = 60

# scrypt parametreleri - yavas kirilim icin bilincli olarak agir.
# Bellek ihtiyaci yaklasik: N * r * 128 bayt (burada 32 MB).
# maxmem acikca verilmezse altta yatan kitaplik 32 MB sinirinda hata veriyor.
SCRYPT_N = 2 ** 15
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_MAXMEM = 96 * 1024 * 1024


def _fernet():
    try:
        from cryptography.fernet import Fernet, InvalidToken
    except ImportError:
        print("HATA: 'cryptography' paketi kurulu değil.")
        print("Kurmak için:  python -m pip install cryptography")
        sys.exit(2)
    return Fernet, InvalidToken


def kasa_dizini(kok=None):
    return Path(kok or yollar.proje_kok()) / KASA_DIZIN_ADI


def kasa_dosyasi(kok=None):
    return kasa_dizini(kok) / KASA_DOSYA_ADI


def _anahtar_turet(parola, tuz):
    """Paroladan sifreleme anahtari uret."""
    import hashlib

    ham = hashlib.scrypt(
        parola.encode("utf-8"), salt=tuz,
        n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=32,
        maxmem=SCRYPT_MAXMEM,
    )
    return base64.urlsafe_b64encode(ham)


def _kasa_oku_ham(kok=None):
    """Kasa dosyasini oku, (tuz, sifreli govde) dondur."""
    yol = kasa_dosyasi(kok)
    if not yol.is_file():
        return None, None

    satirlar = yol.read_text(encoding="utf-8").strip().splitlines()
    if len(satirlar) < 3 or satirlar[0] != BASLIK:
        raise ValueError("Kasa dosyası bozuk veya tanınmıyor.")

    return base64.b64decode(satirlar[1]), satirlar[2].encode("ascii")


def _kasa_yaz_ham(tuz, govde, kok=None):
    yol = kasa_dosyasi(kok)
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(
        f"{BASLIK}\n{base64.b64encode(tuz).decode('ascii')}\n{govde.decode('ascii')}\n",
        encoding="utf-8",
    )


def _icerik_coz(anahtar, govde):
    Fernet, InvalidToken = _fernet()
    try:
        duz = Fernet(anahtar).decrypt(govde)
    except InvalidToken:
        return None
    return json.loads(duz.decode("utf-8"))


def _icerik_sifrele(anahtar, icerik):
    Fernet, _ = _fernet()
    ham = json.dumps(icerik, ensure_ascii=False).encode("utf-8")
    return Fernet(anahtar).encrypt(ham)


# ---------------------------------------------------------------- oturum

def _oturum_oku():
    if not OTURUM_YOLU.is_file():
        return None
    try:
        veri = json.loads(OTURUM_YOLU.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if veri.get("bitis", 0) < time.time():
        _oturum_sil()
        return None

    return veri


def _oturum_yaz(anahtar, sure_dk, kasa_yolu):
    OTURUM_YOLU.parent.mkdir(parents=True, exist_ok=True)
    OTURUM_YOLU.write_text(json.dumps({
        "anahtar": anahtar.decode("ascii"),
        "bitis": time.time() + sure_dk * 60,
        "kasa": str(kasa_yolu),
    }), encoding="utf-8")

    try:
        os.chmod(OTURUM_YOLU, 0o600)
    except OSError:
        pass


def _oturum_sil():
    try:
        OTURUM_YOLU.unlink()
    except OSError:
        pass


def _acik_anahtar(kok=None):
    """Oturum acıksa anahtari dondur, degilse None."""
    oturum = _oturum_oku()
    if not oturum:
        return None
    if oturum.get("kasa") != str(kasa_dosyasi(kok)):
        return None
    return oturum["anahtar"].encode("ascii")


def _parola_al(arg_parola):
    """Parolayi arguman, ortam degiskeni veya stdin'den al."""
    if arg_parola:
        return arg_parola

    ortam = os.environ.get("ENVER_KASA_PAROLA")
    if ortam:
        return ortam

    if not sys.stdin.isatty():
        okunan = sys.stdin.read().strip()
        if okunan:
            return okunan

    import getpass
    return getpass.getpass("Kasa parolası: ")


# ---------------------------------------------------------------- komutlar

def komut_kur(args):
    """Duz metin kasayi sifrele."""
    kok = yollar.proje_kok()
    kaynak = Path(args.kaynak) if args.kaynak else Path(kok) / "vault"

    if kasa_dosyasi(kok).is_file() and not args.uzerine_yaz:
        print("Kasa zaten kurulu. Üzerine yazmak için --uzerine-yaz kullan.")
        return 1

    if not kaynak.is_dir():
        print(f"Kaynak klasör bulunamadı: {kaynak}")
        return 1

    icerik = {}
    for dosya in sorted(kaynak.rglob("*")):
        if not dosya.is_file() or dosya.name == ".gitignore":
            continue
        bagil = dosya.relative_to(kaynak).as_posix()
        icerik[bagil] = dosya.read_text(encoding="utf-8", errors="replace")

    if not icerik:
        print(f"Kaynak klasörde dosya yok: {kaynak}")
        return 1

    parola = _parola_al(args.parola)
    if len(parola) < 8:
        print("Parola en az 8 karakter olmalı.")
        return 1

    tuz = os.urandom(16)
    anahtar = _anahtar_turet(parola, tuz)
    _kasa_yaz_ham(tuz, _icerik_sifrele(anahtar, icerik), kok)

    print(f"Kasa kuruldu: {kasa_dosyasi(kok)}")
    print(f"Şifrelenen dosya sayısı: {len(icerik)}")
    print()
    print("SIRADAKİ ADIM: Düz metin kaynağı arşivle, projede bırakma:")
    print(f'  python scripts/ortak/arsiv.py "{kaynak}" "Kasa duz metin yedegi" "Kasa sifrelendi, duz metin kaynak arsivlendi."')
    return 0


def komut_ac(args):
    kok = yollar.proje_kok()
    tuz, govde = _kasa_oku_ham(kok)

    if tuz is None:
        print("Kasa kurulu değil. Önce: python kasa.py kur")
        return 1

    parola = _parola_al(args.parola)
    anahtar = _anahtar_turet(parola, tuz)

    if _icerik_coz(anahtar, govde) is None:
        print("Parola yanlış. Kasa açılmadı.")
        return 1

    _oturum_yaz(anahtar, args.sure, kasa_dosyasi(kok))
    print(f"Kasa açıldı. Süre: {args.sure} dakika.")
    print("Kapatmak için: python kasa.py kilitle")
    return 0


def komut_kilitle(_args):
    _oturum_sil()
    print("Kasa kilitlendi.")
    return 0


def komut_durum(_args):
    kok = yollar.proje_kok()
    yol = kasa_dosyasi(kok)

    if not yol.is_file():
        print("Kasa kurulu değil.")
        return 0

    print(f"Kasa dosyası: {yol}")

    oturum = _oturum_oku()
    if not oturum or oturum.get("kasa") != str(yol):
        print("Durum: KİLİTLİ")
        print("Açmak için: python kasa.py ac")
        return 0

    kalan = int((oturum["bitis"] - time.time()) / 60)
    print(f"Durum: AÇIK (kalan süre: {kalan} dakika)")
    return 0


def _acik_icerik(kok):
    """Oturum acıksa kasa icerigini dondur."""
    anahtar = _acik_anahtar(kok)
    if anahtar is None:
        print("Kasa KİLİTLİ. Önce açman gerekiyor:")
        print("  python kasa.py ac")
        return None

    tuz, govde = _kasa_oku_ham(kok)
    if tuz is None:
        print("Kasa kurulu değil.")
        return None

    icerik = _icerik_coz(anahtar, govde)
    if icerik is None:
        print("Oturum anahtarı bu kasayı açmıyor. Yeniden aç.")
        _oturum_sil()
        return None

    return icerik


def komut_liste(_args):
    kok = yollar.proje_kok()
    icerik = _acik_icerik(kok)
    if icerik is None:
        return 1

    print(f"Kasadaki dosyalar ({len(icerik)}):")
    for ad in sorted(icerik):
        print(f"  {ad}   ({len(icerik[ad])} karakter)")
    return 0


def komut_oku(args):
    kok = yollar.proje_kok()
    icerik = _acik_icerik(kok)
    if icerik is None:
        return 1

    if args.dosya not in icerik:
        print(f"Kasada böyle bir dosya yok: {args.dosya}")
        print("Mevcut dosyalar: " + ", ".join(sorted(icerik)))
        return 1

    print(icerik[args.dosya])
    return 0


def komut_yaz(args):
    kok = yollar.proje_kok()
    icerik = _acik_icerik(kok)
    if icerik is None:
        return 1

    if args.icerik:
        yeni = args.icerik
    elif not sys.stdin.isatty():
        yeni = sys.stdin.read()
    else:
        print("İçerik verilmedi.")
        return 1

    icerik[args.dosya] = yeni

    anahtar = _acik_anahtar(kok)
    tuz, _ = _kasa_oku_ham(kok)
    _kasa_yaz_ham(tuz, _icerik_sifrele(anahtar, icerik), kok)

    print(f"Kasaya yazıldı: {args.dosya}")
    return 0


def komut_parola(args):
    kok = yollar.proje_kok()
    tuz, govde = _kasa_oku_ham(kok)

    if tuz is None:
        print("Kasa kurulu değil.")
        return 1

    eski = _parola_al(args.eski)
    icerik = _icerik_coz(_anahtar_turet(eski, tuz), govde)

    if icerik is None:
        print("Eski parola yanlış.")
        return 1

    yeni = args.yeni or _parola_al(None)
    if len(yeni) < 8:
        print("Yeni parola en az 8 karakter olmalı.")
        return 1

    yeni_tuz = os.urandom(16)
    _kasa_yaz_ham(yeni_tuz, _icerik_sifrele(_anahtar_turet(yeni, yeni_tuz), icerik), kok)
    _oturum_sil()

    print("Parola değiştirildi. Kasa kilitlendi, yeni parolayla açman gerekiyor.")
    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Parola korumalı kasa")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("kur", help="Düz metin kasayı şifrele")
    p.add_argument("--kaynak")
    p.add_argument("--parola")
    p.add_argument("--uzerine-yaz", action="store_true", dest="uzerine_yaz")
    p.set_defaults(islev=komut_kur)

    p = alt.add_parser("ac", help="Kasayı aç")
    p.add_argument("--parola")
    p.add_argument("--sure", type=int, default=VARSAYILAN_SURE_DK)
    p.set_defaults(islev=komut_ac)

    p = alt.add_parser("kilitle", help="Kasayı kilitle")
    p.set_defaults(islev=komut_kilitle)

    p = alt.add_parser("durum", help="Kilitli mi açık mı")
    p.set_defaults(islev=komut_durum)

    p = alt.add_parser("liste", help="Kasadaki dosyaları listele")
    p.set_defaults(islev=komut_liste)

    p = alt.add_parser("oku", help="Bir dosyayı göster")
    p.add_argument("dosya")
    p.set_defaults(islev=komut_oku)

    p = alt.add_parser("yaz", help="Bir dosyayı ekle veya güncelle")
    p.add_argument("dosya")
    p.add_argument("icerik", nargs="?")
    p.set_defaults(islev=komut_yaz)

    p = alt.add_parser("parola", help="Parolayı değiştir")
    p.add_argument("--eski")
    p.add_argument("--yeni")
    p.set_defaults(islev=komut_parola)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
