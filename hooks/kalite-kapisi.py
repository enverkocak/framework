#!/usr/bin/env python3
"""Stop kancası: Kalite kapısı.

Tam yetki modunda iş kesintisiz akar; duracağı yeri fazın kapı kontrolü
belirler. Bu kanca, iş bitirilmek istendiğinde kapıyı çalıştırır ve
geçmediyse çalışmayı sürdürtür.

Böylece "bitti" bir görüş değil, ölçüm sonucu olur.

Yalnız şu iki koşul birden sağlanınca devreye girer:
  1. Tam yetki modu açık
  2. Aktif fazın tanımlı bir kapı kontrolü var

Diğer durumlarda sessiz kalır - normal çalışmayı engellemez.

Sonsuz döngü koruması: kanca kendi tetiklediği turda ikinci kez engellemez.

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
    sys.path.insert(0, str(betik_dizini / "faz"))
    sys.path.insert(0, str(betik_dizini / "hafiza"))
    try:
        import ayarlar
        import faz
        import yollar
    except ImportError:
        ayarlar = faz = yollar = None
else:
    ayarlar = faz = yollar = None


def main():
    try:
        girdi = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        print(json.dumps({}))
        return

    # Sonsuz dongu korumasi: bu kanca zaten bir kez engellediyse tekrar etme
    if girdi.get("stop_hook_active"):
        print(json.dumps({}))
        return

    if not BETIKLER_HAZIR or faz is None:
        print(json.dumps({}))
        return

    try:
        kok = yollar.proje_kok()
    except Exception:
        print(json.dumps({}))
        return

    # Yalniz tam yetki modunda devreye girer
    if not ayarlar.oku(kok).get("tam_yetki"):
        print(json.dumps({}))
        return

    aktif = faz.aktif_faz(kok)
    if aktif is None or not aktif.get("kapi_komutu"):
        print(json.dumps({}))
        return

    try:
        gecti, cikti = faz.kapi_calistir(aktif, kok)
    except Exception as hata:
        print(json.dumps({"systemMessage": f"Kalite kapisi calistirilamadi: {hata}"}))
        return

    if gecti:
        print(json.dumps({
            "systemMessage": (
                f"Kalite kapisi gecti - Faz {aktif['no']} tamamlanabilir. "
                "Ilerletmek icin: python scripts/faz/faz.py ilerle"
            )
        }))
        return

    ozet = cikti[-1200:] if cikti else "Kapi ciktisi alinamadi."

    print(json.dumps({
        "decision": "block",
        "reason": (
            f"KALITE KAPISI KAPALI - Faz {aktif['no']} ({aktif['ad']})\n"
            "\n"
            "Tam yetki modu acik ve bu fazin kapi kontrolu gecmedi.\n"
            "Is bitmis sayilmaz; eksikleri gider ve devam et.\n"
            "\n"
            "Kapi ciktisi:\n"
            f"{ozet}\n"
            "\n"
            "Duramayacaksan modu degistir: python scripts/faz/mod.py dikkatli"
        ),
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception as hata:
        print(json.dumps({"systemMessage": f"Kalite kapisi kancasi hatasi: {hata}"}))
    sys.exit(0)
