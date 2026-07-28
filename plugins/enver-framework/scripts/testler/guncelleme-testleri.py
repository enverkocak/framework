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

import inspect
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


def olc(aciklama, kosul, ayrinti=""):
    global gecen, kalan
    if kosul:
        print(f"  [GECTI ] {aciklama}")
        gecen += 1
    else:
        print(f"  [HATA  ] {aciklama}" + (f" - {ayrinti}" if ayrinti else ""))
        kalan += 1


# --------------------------------------------------------------- sürüm okuma

# Sürüm okunamazsa karşılaştırma da anlamsızlaşır: 'var_mi' hiçbir zaman
# doğru olamaz ve kurulu kopya aylarca geride kalsa bile hiçbir şey
# söylenmez. Sessiz kalmanın en pahalı biçimi budur.
print("\n  Surum okuma - iki dizin duzeninde de calismali")

import shutil  # noqa: E402
import subprocess  # noqa: E402

DUZENLER = (
    # (ad, betigin yeri, manifestin yeri)
    ("Pazar yerinden kurulum", "surum-klasoru/scripts", "surum-klasoru/.claude-plugin"),
    ("Depo klonu", "plugins/enver-framework/scripts",
     "plugins/enver-framework/.claude-plugin"),
)

for ad, betik_dizini, manifest_dizini in DUZENLER:
    with tempfile.TemporaryDirectory() as gecici:
        kok = Path(gecici)
        (kok / betik_dizini).mkdir(parents=True)
        (kok / manifest_dizini).mkdir(parents=True)

        shutil.copy2(guncelleme.__file__, kok / betik_dizini / "guncelleme.py")
        (kok / manifest_dizini / "plugin.json").write_text(
            '{"name": "enver-framework", "version": "9.8.7"}', encoding="utf-8")

        sonuc = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, sys.argv[1]); import guncelleme;"
             " print(guncelleme.yerel_surum())",
             str(kok / betik_dizini)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=60)
        okunan = (sonuc.stdout or "").strip()

        olc(f"{ad} duzeninde surum okunuyor", okunan == "9.8.7",
            f"okunan: {okunan or sonuc.stderr.strip()[:80]}")

# ------------------------------------------------------- kurulu kopya geride

# Depo klonu ile çalışan eklenti ayrı sürümde olabilir. Depo 3.3.4'teyken
# çalışan kopya 3.2.9'da kaldı ve hiçbir şey haber vermedi.
print("\n  Kurulu kopya geride kaldiginda haber verilmeli")


def _kurulu_kur(gecici, surum):
    yol = Path(gecici) / "installed_plugins.json"
    yol.write_text(json.dumps({"plugins": {"enver-framework@enver-framework": [
        {"scope": "user", "version": surum, "installPath": "x"}]}}),
        encoding="utf-8")
    return yol


for baslik, kurulu_surum, calisan, beklenen in (
        ("Kurulu 3.2.9, calisan 3.3.4 -> uyarmali", "3.2.9", "3.3.4", True),
        ("Ikisi de 3.3.4 -> susmali", "3.3.4", "3.3.4", False),
        ("Kurulu ileride -> susmali", "3.4.0", "3.3.4", False)):
    with tempfile.TemporaryDirectory() as gecici:
        eski_kayit = guncelleme.KURULU_EKLENTILER
        eski_yerel = guncelleme.yerel_surum
        eski_manifest = guncelleme.plugin_manifesti
        try:
            guncelleme.KURULU_EKLENTILER = _kurulu_kur(gecici, kurulu_surum)
            guncelleme.yerel_surum = lambda: calisan
            guncelleme.eklenti_adi = lambda: "enver-framework"
            geride = guncelleme.pazar_geride_mi()
        finally:
            guncelleme.KURULU_EKLENTILER = eski_kayit
            guncelleme.yerel_surum = eski_yerel
            guncelleme.plugin_manifesti = eski_manifest

    olc(baslik, bool(geride) == beklenen)

# Güncelleme uygulanınca pazar yeri kopyası da tazelenmeli; yoksa komut
# "bitti" der ama çalışan eklenti eski sürümde kalır.
kaynak = inspect.getsource(guncelleme.komut_yap)
olc("Guncelleme pazar yeri kopyasini da tazeliyor",
    "pazar_yerini_tazele" in kaynak)

# Pazar yerinden kurulu makinede klon kurulumu ÇALIŞMAMALI: ikinci bir
# paralel kurulum bırakır ve hangi kopyanın canlı olduğu belirsizleşir.
print("\n  Iki paralel kurulum olusmamali")
for baslik, kayitli, beklenen in (
        ("Pazar yerinden kuruluysa pazar yolu", True, "pazar"),
        ("Kayit yoksa klon yolu", False, "klon")):
    with tempfile.TemporaryDirectory() as gecici:
        eski_kayit = guncelleme.KURULU_EKLENTILER
        eski_ad = guncelleme.eklenti_adi
        try:
            guncelleme.eklenti_adi = lambda: "enver-framework"
            guncelleme.KURULU_EKLENTILER = (
                _kurulu_kur(gecici, "3.3.4") if kayitli
                else Path(gecici) / "yok.json")
            yol = guncelleme.guncelleme_yolu()
        finally:
            guncelleme.KURULU_EKLENTILER = eski_kayit
            guncelleme.eklenti_adi = eski_ad

    olc(baslik, yol == beklenen, f"gelen: {yol}")

olc("Pazar yolunda kurulum betigi cagrilmiyor",
    kaynak.index("pazar_yerini_tazele") < kaynak.index("klon_dizini()"),
    "kurulum, pazar yolundan once calisiyor")
olc("Tazeleme claude komutunu cagiriyor",
    "plugin" in inspect.getsource(guncelleme.pazar_yerini_tazele)
    and "marketplace" in inspect.getsource(guncelleme.pazar_yerini_tazele))

print()
print(f"  Senaryo sonucu: {gecen} gecti, {kalan} kaldi")
sys.exit(1 if kalan else 0)
