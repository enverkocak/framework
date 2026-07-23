#!/usr/bin/env python3
"""SessionStart kancası: Açılış brifingi.

Oturum açıldığında "nerede kaldık" bilgisini hazırlar ve bağlama ekler.
Böylece her seferinde yeniden anlatmak gerekmez.

Yaptıkları:
  1. Bu makine tanınıyor mu bakar; tanınmıyorsa bildirir.
  2. Son çalışma başka makinede yapıldıysa uyarır (yerel bilgi eski olabilir).
  3. Son durumu, bekleyen işi ve son kararları özetler.

Hiçbir şeyi engellemez, hiçbir şeyi değiştirmez. Sadece bilgi verir.

Geliştirici: Enver KOCAK
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _ortak_yol as ortak_yol  # noqa: E402

BETIKLER_HAZIR = ortak_yol.hazirla()

if BETIKLER_HAZIR:
    betik_dizini = ortak_yol.betik_dizini()
    sys.path.insert(0, str(betik_dizini))
    sys.path.insert(0, str(betik_dizini / "hafiza"))
    sys.path.insert(0, str(betik_dizini / "senkron"))
    try:
        import hafiza
        import makine
        import yollar
    except ImportError:
        hafiza = makine = yollar = None
    try:
        import guncelleme
    except ImportError:
        guncelleme = None
else:
    hafiza = makine = yollar = None
    guncelleme = None

SATIR_SINIRI = 40


def _son_durum(kok):
    """Durum belgesindeki en güncel bölümü döndür."""
    icerik = hafiza.metin_oku(hafiza.hafiza_dosyasi(hafiza.DURUM_DOSYASI, kok)).strip()
    if not icerik:
        return None

    bolumler = icerik.split("\n## ")
    if len(bolumler) < 2:
        return icerik[:1200]

    son = "## " + bolumler[1]
    satirlar = son.splitlines()[:SATIR_SINIRI]
    return "\n".join(satirlar)


def _son_kayitlar(kok, dosya, sayi=3):
    """Bir defterin en güncel başlıklarını döndür."""
    icerik = hafiza.metin_oku(hafiza.hafiza_dosyasi(dosya, kok)).strip()
    if not icerik:
        return []

    basliklar = []
    for satir in icerik.splitlines():
        if satir.startswith("## "):
            basliklar.append(satir[3:].strip())
        if len(basliklar) >= sayi:
            break
    return basliklar


def brifing_uret():
    kok = yollar.proje_kok()
    proje = yollar.proje_adi(kok)

    bolumler = [f"OTURUM AÇILIŞ BRİFİNGİ - {proje}"]

    # Güncelleme bildirimi (varsa) en üstte, en görünür yerde durur.
    # Ağı günde bir kez yoklar; yoksa ya da güncelse hiçbir şey eklemez.
    if guncelleme is not None:
        try:
            haber = guncelleme.banner()
        except Exception:
            haber = ""
        if haber:
            bolumler.append(haber)

    # Makine durumu
    kendi = makine.bu_makine(kok)
    if kendi:
        bolumler.append(f"Makine: {kendi.get('ad')}")
    else:
        bolumler.append(
            f"Makine: {makine.kimlik()} - BU MAKİNE TANINMIYOR.\n"
            "Kullanıcıya sor: bu bilgisayara ne ad verelim? Sonra kaydet:\n"
            "  python scripts/senkron/makine.py tanit --ad \"<ad>\""
        )

    if makine.baska_makinede_mi(kok):
        son = makine.son_calisan(kok)
        bolumler.append(
            f"DİKKAT: Son çalışma başka makinede yapılmış "
            f"({son.get('ad')}, {son.get('son_gorulme')}).\n"
            "Yerel bilgi eski olabilir. Kullanıcıya senkron almayı öner:\n"
            "  python scripts/senkron/senkron.py cek"
        )

    # Nerede kaldık
    durum = _son_durum(kok)
    if durum:
        bolumler.append("NEREDE KALDIK\n" + durum)
    else:
        bolumler.append("NEREDE KALDIK\nHenüz kayıt yok. İlk oturum sonunda oluşacak.")

    # Defterler
    kararlar = _son_kayitlar(kok, hafiza.KARARLAR_DOSYASI)
    if kararlar:
        bolumler.append("SON KARARLAR\n" + "\n".join(f"- {k}" for k in kararlar))

    hatalar = _son_kayitlar(kok, hafiza.HATALAR_DOSYASI)
    if hatalar:
        bolumler.append(
            "SON ÇÖZÜLEN HATALAR (aynısı çıkarsa çözümü hazır)\n"
            + "\n".join(f"- {h}" for h in hatalar)
        )

    return "\n\n".join(bolumler)


def main():
    # Girdiyi tüket; içeriği kullanılmasa da akış tıkanmasın
    try:
        json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        pass

    if not BETIKLER_HAZIR or hafiza is None:
        print(json.dumps({}))
        return

    try:
        metin = brifing_uret()
    except Exception as hata:
        print(json.dumps({"systemMessage": f"Acilis kancasi hatasi: {hata}"}))
        return

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": metin,
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception as hata:
        print(json.dumps({"systemMessage": f"Acilis kancasi hatasi: {hata}"}))
    sys.exit(0)
