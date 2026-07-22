#!/usr/bin/env python3
"""İzole deneme alanı - riskli değişikliği ayrı kopyada dene.

Bir fikri denemek istiyorsun ama projeyi bozmak istemiyorsun.
Bu araç, aynı depodan ayrı bir çalışma kopyası açar. Denemeyi orada
yaparsın; beğenirsen alırsın, beğenmezsen kopyayı kapatırsın ve
asıl projede hiçbir iz kalmaz.

Kopya aynı depoyu paylaşır, yani dosyalar iki kez indirilmez.

Deneme kapatılırken içeriği silinmez, arşive alınır: hiçbir veri
kaybolmaz kuralı burada da geçerlidir.

Komutlar:
    ac       Yeni deneme alanı aç
    liste    Açık deneme alanları
    kapat    Deneme alanını kapat (arşivlenir)

Geliştirici: Enver KOCAK
"""

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))

import arsiv  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

DENEME_KOKU = "_denemeler"


def _git(*argumanlar, kok=None):
    kok = kok or yollar.proje_kok()
    try:
        sonuc = subprocess.run(
            ["git", *argumanlar], cwd=str(kok),
            capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as hata:
        return False, str(hata)

    return sonuc.returncode == 0, ((sonuc.stdout or "") + (sonuc.stderr or "")).strip()


def deneme_koku(kok=None):
    """Deneme alanları projenin YANINDA açılır, içinde değil.

    İçinde açılsaydı asıl projenin dosya listesine karışır, ana dizin
    temiz kalır kuralını bozardı.
    """
    proje = Path(kok or yollar.proje_kok())
    return proje.parent / f"{DENEME_KOKU}-{proje.name}"


def komut_ac(args):
    kok = Path(yollar.proje_kok())
    hedef = deneme_koku(kok) / args.ad

    if hedef.exists():
        print(f"Bu adla bir deneme zaten var: {hedef}")
        return 1

    hedef.parent.mkdir(parents=True, exist_ok=True)

    dal = args.dal or f"deneme/{args.ad}"

    basarili, cikti = _git("worktree", "add", "-b", dal, str(hedef), kok=kok)
    if not basarili:
        print("Deneme alanı açılamadı:")
        print(cikti[:600])
        return 1

    print(f"Deneme alanı açıldı: {hedef}")
    print(f"Dal: {dal}")
    print()
    print("Denemeyi burada yap. Asıl projeye dokunulmaz.")
    print(f"Kapatmak için: python izole.py kapat {args.ad}")
    return 0


def komut_liste(args):
    kok = Path(yollar.proje_kok())
    basarili, cikti = _git("worktree", "list", kok=kok)

    if not basarili:
        print("Deneme alanları okunamadı.")
        return 1

    satirlar = [s for s in cikti.splitlines() if DENEME_KOKU in s]

    if not satirlar:
        print("Açık deneme alanı yok.")
        return 0

    print(f"Açık deneme alanları ({len(satirlar)}):")
    for satir in satirlar:
        print(f"  {satir}")
    return 0


def komut_kapat(args):
    kok = Path(yollar.proje_kok())
    hedef = deneme_koku(kok) / args.ad

    if not hedef.exists():
        print(f"Böyle bir deneme yok: {hedef}")
        return 1

    # Once arsivle - hicbir veri silinmez
    if not args.arsivleme:
        try:
            klasor = arsiv.arsivle(
                hedef,
                f"Deneme alani: {args.ad}",
                args.neden or "Deneme kapatildi.",
                tasi=False,
            )
            print(f"Arşivlendi: {klasor}")
        except (OSError, FileNotFoundError) as hata:
            print(f"Arşivleme başarısız, kapatma durduruldu: {hata}")
            return 1

    basarili, cikti = _git("worktree", "remove", "--force", str(hedef), kok=kok)
    if not basarili:
        print("Deneme alanı kapatılamadı:")
        print(cikti[:400])
        return 1

    print(f"Deneme alanı kapatıldı: {args.ad}")
    print("Asıl projede iz kalmadı.")
    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="İzole deneme alanı")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("ac", help="Yeni deneme alanı aç")
    p.add_argument("ad")
    p.add_argument("--dal")
    p.set_defaults(islev=komut_ac)

    p = alt.add_parser("liste", help="Açık deneme alanları")
    p.set_defaults(islev=komut_liste)

    p = alt.add_parser("kapat", help="Deneme alanını kapat")
    p.add_argument("ad")
    p.add_argument("--neden")
    p.add_argument("--arsivleme", action="store_true",
                   help="Arşivlemeden kapat (önerilmez)")
    p.set_defaults(islev=komut_kapat)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
