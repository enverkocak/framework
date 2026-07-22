#!/usr/bin/env python3
"""Makineler arası senkron - her yerden aynı bilgiyle çalışmak.

Enver birden çok bilgisayar kullanıyor. Bir makinede yarım bırakılan iş
diğerinde kaldığı yerden devam edebilmeli.

Akış:
  çek     Depodan en güncel hali al, sonra "nerede kaldık" göster
  gönder  Yerel değişiklikleri depoya işle
  durum   Yerel ile depo arasında fark var mı

Çakışma koruması: göndermeden önce depoda yeni kayıt olup olmadığına bakılır.
Varsa üzerine yazılmaz; önce alınması istenir.

Kasa senkrona DAHİL DEĞİLDİR. Şifreli kasa depoya girmez; ayrı taşınır.

Geliştirici: Enver KOCAK
"""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "hafiza"))

import hafiza  # noqa: E402
import makine  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

# Senkrona dahil edilen yollar. Kasa ve ham günlük bilinçli olarak dışarıda.
SENKRON_YOLLARI = ["hafiza"]


def _git(*argumanlar, kok=None):
    """Depo komutu çalıştır, (başarılı, çıktı) döndür."""
    kok = kok or yollar.proje_kok()
    try:
        sonuc = subprocess.run(
            ["git", *argumanlar],
            cwd=str(kok), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=90,
        )
    except (OSError, subprocess.TimeoutExpired) as hata:
        return False, str(hata)

    cikti = (sonuc.stdout or "") + (sonuc.stderr or "")
    return sonuc.returncode == 0, cikti.strip()


def depo_var_mi(kok=None):
    basarili, _ = _git("rev-parse", "--git-dir", kok=kok)
    return basarili


def uzak_var_mi(kok=None):
    basarili, cikti = _git("remote", kok=kok)
    return basarili and bool(cikti.strip())


def yerel_degisiklik(kok=None):
    """Senkron kapsamındaki yollarda bekleyen değişiklikler."""
    basarili, cikti = _git("status", "--porcelain", "--", *SENKRON_YOLLARI, kok=kok)
    if not basarili or not cikti:
        return []
    return [satir.strip() for satir in cikti.splitlines() if satir.strip()]


def uzakta_yeni_var_mi(kok=None):
    """Depoda bizde olmayan kayıt var mı?"""
    _git("fetch", "--quiet", kok=kok)
    basarili, cikti = _git("rev-list", "--count", "HEAD..@{u}", kok=kok)
    if not basarili:
        return None
    try:
        return int(cikti.strip()) > 0
    except ValueError:
        return None


# ---------------------------------------------------------------- komutlar

def komut_durum(args):
    kok = yollar.proje_kok()

    print(f"Proje : {yollar.proje_adi(kok)}")
    print(f"Makine: {makine.kimlik()}")
    print()

    if not depo_var_mi(kok):
        print("Bu klasör bir depo değil. Senkron yapılamaz.")
        return 1

    if not uzak_var_mi(kok):
        print("Uzak depo tanımlı değil. Senkron yapılamaz.")
        return 1

    bekleyen = yerel_degisiklik(kok)
    print(f"Yerel bekleyen değişiklik: {len(bekleyen)}")
    for satir in bekleyen[:10]:
        print(f"  {satir}")

    uzak = uzakta_yeni_var_mi(kok)
    if uzak is None:
        print("Uzak durum okunamadı (dal takip etmiyor olabilir).")
    elif uzak:
        print("Uzakta YENİ KAYIT VAR - önce çekmelisin.")
    else:
        print("Uzak depo güncel.")

    if makine.baska_makinede_mi(kok):
        son = makine.son_calisan(kok)
        print()
        print(f"Son çalışma başka makinede: {son.get('ad')} - {son.get('son_gorulme')}")

    return 0


def komut_cek(args):
    kok = yollar.proje_kok()

    if not depo_var_mi(kok) or not uzak_var_mi(kok):
        print("Depo veya uzak tanımlı değil, çekme atlandı.")
        return 1

    bekleyen = yerel_degisiklik(kok)
    if bekleyen and not args.zorla:
        print("Yerelde işlenmemiş değişiklik var. Önce gönder ya da --zorla kullan.")
        for satir in bekleyen[:10]:
            print(f"  {satir}")
        return 1

    print("Depodan güncel hali alınıyor...")
    basarili, cikti = _git("pull", "--ff-only", kok=kok)

    if not basarili:
        print("Çekme başarısız:")
        print(cikti[:600])
        print()
        print("Muhtemel sebep: iki makinede aynı dosya değişmiş.")
        print("Elle çözmen gerekiyor.")
        return 1

    print(cikti[:400] or "Zaten güncel.")
    makine.tanit()

    if not args.sessiz:
        print()
        print("=" * 52)
        alt_sonuc = subprocess.run(
            [sys.executable, str(SCRIPT_DIZINI.parent / "hafiza" / "oturum.py"), "brifing"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        print(alt_sonuc.stdout)

    return 0


def komut_gonder(args):
    kok = yollar.proje_kok()

    if not depo_var_mi(kok) or not uzak_var_mi(kok):
        print("Depo veya uzak tanımlı değil, gönderme atlandı.")
        return 1

    bekleyen = yerel_degisiklik(kok)
    if not bekleyen:
        print("Gönderilecek hafıza değişikliği yok.")
        return 0

    # Çakışma koruması: üzerine yazma
    uzak = uzakta_yeni_var_mi(kok)
    if uzak:
        print("DUR: Uzak depoda bizde olmayan kayıt var.")
        print("Üzerine yazmamak için gönderme durduruldu.")
        print()
        print("Önce al:  python senkron.py cek")
        return 1

    print(f"{len(bekleyen)} değişiklik işleniyor...")

    basarili, cikti = _git("add", "--", *SENKRON_YOLLARI, kok=kok)
    if not basarili:
        print(f"Ekleme başarısız: {cikti[:300]}")
        return 1

    kayit = bu_makine_etiketi()
    mesaj = args.mesaj or f"hafiza guncellendi - {kayit}"

    basarili, cikti = _git("commit", "-m", mesaj, "--", *SENKRON_YOLLARI, kok=kok)
    if not basarili and "nothing to commit" not in cikti.lower():
        print(f"İşleme başarısız: {cikti[:300]}")
        return 1

    basarili, cikti = _git("push", kok=kok)
    if not basarili:
        print(f"Gönderme başarısız: {cikti[:400]}")
        return 1

    print("Hafıza gönderildi.")
    return 0


def bu_makine_etiketi():
    kayit = makine.bu_makine()
    return kayit.get("ad") if kayit else makine.kimlik()


def main():
    ayristirici = argparse.ArgumentParser(description="Makineler arası senkron")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("durum", help="Yerel ile depo arasında fark var mı")
    p.set_defaults(islev=komut_durum)

    p = alt.add_parser("cek", help="Depodan güncel hali al")
    p.add_argument("--zorla", action="store_true")
    p.add_argument("--sessiz", action="store_true", help="Brifing gösterme")
    p.set_defaults(islev=komut_cek)

    p = alt.add_parser("gonder", help="Yerel hafızayı depoya işle")
    p.add_argument("--mesaj")
    p.set_defaults(islev=komut_gonder)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
