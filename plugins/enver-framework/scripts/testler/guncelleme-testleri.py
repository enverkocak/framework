#!/usr/bin/env python3
"""Güncelleme bildirimi senaryoları.

Bu bildirim iki yönde de yanılabilir ve ikisi de kullanıcıyı yanıltır:

  YANLIŞ UYARI   Güncelledikten sonra "GÜNCELLEME VAR" demeye devam eder.
                 Kullanıcı güncellemenin işe yaramadığını sanır.
  SESSİZ KALMA   Yeni sürüm yayınlandığı halde hiçbir şey söylemez.
                 Kullanıcı eski sürümde kalır ve bunu bilmez.

Senaryolar ikisini de ölçer. Ağ gerekmez: önbellek dosyası ve yerel sürüm
okuyucusu değiştirilerek durumlar kurulur.

Geliştirici: Enver KOCAK
"""

import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent))

import guncelleme  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

gecen = 0
kalan = 0


def dene(aciklama, onbellek, yerel, beklenen_var_mi):
    """Önbelleği ve yerel sürümü kur, kontrol()'un kararını ölç."""
    global gecen, kalan

    with tempfile.TemporaryDirectory() as gecici:
        durum_yolu = Path(gecici) / "guncelle-durum.json"
        durum_yolu.write_text(json.dumps(onbellek), encoding="utf-8")

        eski_durum = guncelleme.DURUM_DOSYASI
        eski_yerel = guncelleme.yerel_surum
        eski_klon = guncelleme.klon_dizini
        eski_canli = guncelleme._canli_kontrol

        canli_cagrildi = {"sayi": 0}

        def sahte_canli(kaynak):
            canli_cagrildi["sayi"] += 1
            # Ağ yokmuş gibi davran: önbellek atlanınca ne olduğu görülsün
            return None

        try:
            guncelleme.DURUM_DOSYASI = durum_yolu
            guncelleme.yerel_surum = lambda: yerel
            guncelleme.klon_dizini = lambda: Path(gecici)
            guncelleme._canli_kontrol = sahte_canli

            sonuc = guncelleme.kontrol()
            gelen = bool(sonuc and sonuc.get("var_mi"))
        finally:
            guncelleme.DURUM_DOSYASI = eski_durum
            guncelleme.yerel_surum = eski_yerel
            guncelleme.klon_dizini = eski_klon
            guncelleme._canli_kontrol = eski_canli

    if gelen == beklenen_var_mi:
        print(f"  [GECTI ] {aciklama}")
        gecen += 1
    else:
        print(f"  [HATA  ] {aciklama} "
              f"(beklenen {beklenen_var_mi}, gelen {gelen})")
        kalan += 1

    return canli_cagrildi["sayi"]


taze = datetime.now().isoformat(timespec="seconds")
eski = (datetime.now() - timedelta(days=2)).isoformat(timespec="seconds")

print("GUNCELLEME BILDIRIMI SENARYOLARI")
print("-" * 52)

print("\n  Yanlis uyari - guncelledikten sonra susmali")
dene("Onbellek 3.2.0->3.2.1 diyor ama yerel artik 3.2.1",
     {"var_mi": True, "yerel": "3.2.0", "uzak": "3.2.1",
      "degisiklikler": ["x"], "son_kontrol": taze},
     "3.2.1", False)

dene("Yerel uzagin ONUNDE (yerel 3.3.0, uzak 3.2.1)",
     {"var_mi": True, "yerel": "3.2.0", "uzak": "3.2.1",
      "degisiklikler": ["x"], "son_kontrol": taze},
     "3.3.0", False)

print("\n  Dogru uyari - gercekten geride kalmissa soylemeli")
dene("Yerel 3.2.0, uzak 3.2.1 (onbellek tutarli)",
     {"var_mi": True, "yerel": "3.2.0", "uzak": "3.2.1",
      "degisiklikler": ["x"], "son_kontrol": taze},
     "3.2.0", True)

print("\n  Sessiz kalma - yerel degisince aga yeniden bakmali")
canli = dene("Yerel surum onbellektekinden farkli",
             {"var_mi": True, "yerel": "3.2.0", "uzak": "3.2.1",
              "degisiklikler": ["x"], "son_kontrol": taze},
             "3.2.2", False)
if canli >= 1:
    print("  [GECTI ] Yerel degisince canli kontrol calisti")
    gecen += 1
else:
    print("  [HATA  ] Yerel degisti ama canli kontrol calismadi - "
          "yeni surum bir gun boyunca kacar")
    kalan += 1

print("\n  Onbellek eskiyince aga bakilmali")
canli = dene("son_kontrol iki gun onceki",
             {"var_mi": False, "yerel": "3.2.1", "uzak": "3.2.1",
              "degisiklikler": [], "son_kontrol": eski},
             "3.2.1", False)
if canli >= 1:
    print("  [GECTI ] Eski onbellekte canli kontrol calisti")
    gecen += 1
else:
    print("  [HATA  ] Onbellek eski ama aga bakilmadi")
    kalan += 1

print()
print(f"  Senaryo sonucu: {gecen} gecti, {kalan} kaldi")
sys.exit(1 if kalan else 0)
