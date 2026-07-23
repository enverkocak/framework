#!/usr/bin/env python3
"""PreToolUse kancası: Tam yetki modu.

Tam yetki açıkken "Do you want to proceed? 1 Yes / 2 Yes all / 3 No"
kutusu HİÇ çıkmaz; iş baştan sona kesintisiz akar. git push, deploy,
DROP dahil her şey sessizce geçer. (Enver'in kararı, 23 Temmuz 2026.)

TAM YETKİ, HIZ DEMEKTİR - KONTROLSÜZLÜK DEĞİL.

Bu modda bile SERT engelle duran işlemler AYRI kancalarda tanımlıdır;
bu kanca "izin ver" dese de onlar "engelle" der ve işlem durur
("engelle" her zaman "izin ver"i yener):
  - Dosya silme         -> veri-koruma.py        (E7)
  - Kasaya erişim        -> kasa-koruma.py        (E1)
  - Herkese açık depo    -> git-gizlilik-koruma.py
  - Harita dışı sunucu   -> sunucu-koruma.py

Böylece tam yetki hiçbir sert korumayı devre dışı bırakamaz; yalnızca
"onay isteyen" katmanı susturur.

Geliştirici: Enver KOCAK
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _ortak_yol as ortak_yol  # noqa: E402

BETIKLER_HAZIR = ortak_yol.hazirla()

if BETIKLER_HAZIR:
    try:
        import ayarlar
        import yollar
    except ImportError:
        ayarlar = yollar = None
else:
    ayarlar = yollar = None


# Tam yetki modunda hiçbir işlem burada ayrıca sorulmaz.
#
# Enver'in kararı (23 Temmuz 2026): tam yetki açıkken "Do you want to
# proceed? 1 Yes / 2 Yes all / 3 No" kutusu HİÇ çıkmasın; iş baştan sona
# kesintisiz aksın. git push, deploy, DROP dahil.
#
# Bu, hiçbir korumayı zayıflatmaz. Sert engeller AYRI kancalarda durur ve
# "engelle" her zaman "izin ver"i yener:
#   - Silme            -> veri-koruma.py       (E7, kesin engel)
#   - Kasa             -> kasa-koruma.py       (E1, kesin engel)
#   - Herkese açık depo -> git-gizlilik-koruma.py (kesin engel)
#   - Yasak sunucu dizini -> sunucu-koruma.py  (harita dışı, kesin engel)
# Bu kanca "izin ver" dese de o kancalar "engelle" derse işlem durur.
#
# Liste boş; yeniden kısıtlamak istenirse buraya (desen, ad) eklemek yeter.
ISTISNALAR = []


def istisna_mi(metin):
    """Bu işlem tam yetki modunda bile ayrı değerlendirilmeli mi?"""
    if not metin:
        return None

    for desen, ad in ISTISNALAR:
        if desen.search(str(metin)):
            return ad
    return None


def tam_yetki_acik_mi(kok=None):
    if ayarlar is None:
        return False
    return bool(ayarlar.oku(kok).get("tam_yetki"))


def main():
    try:
        girdi = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        print(json.dumps({}))
        return

    if not BETIKLER_HAZIR or ayarlar is None:
        print(json.dumps({}))
        return

    try:
        kok = yollar.proje_kok()
    except Exception:
        kok = None

    if not tam_yetki_acik_mi(kok):
        print(json.dumps({}))
        return

    girdiler = girdi.get("tool_input", {})

    # İncelenecek metin: komut ya da dosya yolu
    incelenecek = " ".join(str(deger) for deger in (
        girdiler.get("command"),
        girdiler.get("file_path"),
        girdiler.get("url"),
    ) if deger)

    ad = istisna_mi(incelenecek)

    if ad:
        # Karar verme; normal izin akışına bırak
        print(json.dumps({}))
        return

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": (
                "Tam yetki modu acik - faz bitene kadar izin sorulmuyor.\n"
                "Kapatmak icin: python scripts/faz/mod.py dikkatli"
            ),
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception as hata:
        # Kanca çökerse tam yetki kendiliğinden devre dışı kalır - güvenli taraf
        print(json.dumps({"systemMessage": f"Tam yetki kancasi hatasi: {hata}"}))
    sys.exit(0)
