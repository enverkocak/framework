#!/usr/bin/env python3
"""PostToolUse kancası: Oturum kaydı.

Çalışırken ne yapıldığını sessizce kaydeder:
  - çalıştırılan komutlar
  - değiştirilen dosyalar

Kayıt ham günlüğe yazılır (makineye özel, depoya girmez). Oturum
biterken özetlenip hafızaya geçer; "nerede kaldık" bilgisi oradan gelir.

Kanca hiçbir şeyi engellemez, hiçbir çıktı üretmez. Sadece yazar.
Parolalar kayda geçmeden önce gizlenir.

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
    sys.path.insert(0, str(betik_dizini / "hafiza"))
    sys.path.insert(0, str(betik_dizini / "senkron"))
    try:
        import oturum
    except ImportError:
        oturum = None
else:
    oturum = None

# Kaydedilmesi anlamsız, gürültü üreten komutlar
ATLANACAK = ("ls", "pwd", "cd", "clear", "echo")


def _gurultu_mu(komut):
    ilk = str(komut).strip().split()
    return bool(ilk) and ilk[0] in ATLANACAK


def main():
    try:
        girdi = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return

    if oturum is None:
        return

    arac = girdi.get("tool_name", "")
    girdiler = girdi.get("tool_input", {})

    try:
        if arac == "Bash":
            komut = girdiler.get("command", "")
            if komut and not _gurultu_mu(komut):
                oturum.kaydet("komut", komut)

        elif arac in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
            dosya = girdiler.get("file_path", "")
            if dosya:
                # Yolu proje köküne göre kısalt, okunur kalsın
                try:
                    import yollar
                    kok = yollar.proje_kok(dosya)
                    dosya = str(Path(dosya).resolve().relative_to(Path(kok).resolve()))
                except (ValueError, OSError, ImportError):
                    pass
                oturum.kaydet("dosya", dosya.replace("\\", "/"))
    except Exception:
        # Kayıt tutmak, çalışmayı engellemeye değmez
        pass


if __name__ == "__main__":
    try:
        main()
    finally:
        # Bu kanca sessizdir; her koşulda boş karar döndürür
        print(json.dumps({}))
    sys.exit(0)
