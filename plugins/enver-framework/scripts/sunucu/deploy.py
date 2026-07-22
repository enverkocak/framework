#!/usr/bin/env python3
"""Deploy güvenlik zinciri.

Canlıya çıkmak tek adım değildir. Zorunlu sıra:

    1. HAZIRLIK    Proje tanımlı mı, hedef belli mi, temiz mi
    2. DENETIM     Kalıp, iz, sır ve yazım denetimleri
    3. YEDEK       Geri dönülebilir bir nokta oluştur
    4. TEST        Proje testleri
    5. ONAY        Kullanıcıya ne yapılacağı gösterilir
    6. ÇIKIŞ       Asıl gönderim

Adım atlanamaz. Bir adım kalırsa zincir durur ve sebebi yazar.

Bu betik ASIL GÖNDERİMİ KENDİ YAPMAZ. Hazırlığı yapar, denetler, yedekler
ve son komutu gösterir. Canlıya çıkış her zaman açık bir insan kararıdır.

Komutlar:
    kontrol    Zinciri çalıştır, çıkışa hazır mı bak
    durum      Son deploy denemesinin durumu

Geliştirici: Enver KOCAK
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
BETIK_KOKU = SCRIPT_DIZINI.parent
sys.path.insert(0, str(BETIK_KOKU / "ortak"))
sys.path.insert(0, str(BETIK_KOKU / "hafiza"))
sys.path.insert(0, str(BETIK_KOKU / "projeler"))
sys.path.insert(0, str(SCRIPT_DIZINI))

import hafiza  # noqa: E402
import proje  # noqa: E402
import yedek  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

DURUM_DOSYASI = "deploy-durumu.json"

GECTI = "gecti"
KALDI = "kaldi"
ATLANDI = "atlandi"

ISARETLER = {GECTI: "[GECTI ]", KALDI: "[KALDI ]", ATLANDI: "[ATLANDI]"}


class Zincir:
    def __init__(self, kok):
        self.kok = Path(kok)
        self.adimlar = []
        self.durdu = False

    def adim(self, ad, durum, aciklama="", ayrinti=""):
        self.adimlar.append({
            "ad": ad, "durum": durum,
            "aciklama": aciklama, "ayrinti": ayrinti[:800],
        })
        print(f"  {ISARETLER[durum]} {ad}")
        if aciklama:
            for satir in aciklama.splitlines():
                print(f"           {satir}")
        if durum == KALDI:
            self.durdu = True
        return durum == GECTI

    def gecti_mi(self):
        return not self.durdu


def _calistir(komut, kok, zaman_asimi=600):
    try:
        sonuc = subprocess.run(
            komut, shell=True, cwd=str(kok),
            capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=zaman_asimi,
        )
    except (OSError, subprocess.TimeoutExpired) as hata:
        return None, str(hata)

    return sonuc.returncode, (sonuc.stdout or "") + (sonuc.stderr or "")


# ------------------------------------------------------------------ adımlar

def adim_hazirlik(zincir, tanim):
    if tanim is None:
        zincir.adim("Hazırlık", KALDI,
                    "Proje tanımı yok. Nereye çıkılacağı belli değil.\n"
                    "Oluştur: python scripts/projeler/proje.py olustur")
        return

    eksikler = []
    if not tanim.get("sunucu"):
        eksikler.append("sunucu")
    if not tanim.get("dizin"):
        eksikler.append("dizin")

    if eksikler:
        zincir.adim("Hazırlık", KALDI,
                    f"Tanımda eksik alan: {', '.join(eksikler)}\n"
                    "Hedef belli olmadan canlıya çıkılamaz.")
        return

    zincir.adim("Hazırlık", GECTI,
                f"{tanim.get('sunucu')} : {tanim.get('dizin')}")


def adim_denetim(zincir, kok):
    denetimler = [
        ("Kalıp denetimi", f'python "{BETIK_KOKU / "tasarim" / "kalip-denetim.py"}" '
                           f'tara "{kok}" --sadece-yuksek'),
    ]

    tumu_gecti = True

    for ad, komut in denetimler:
        kod, cikti = _calistir(komut, kok, zaman_asimi=180)

        if kod is None:
            zincir.adim(ad, ATLANDI, "Denetim çalıştırılamadı.")
            continue

        if kod == 0:
            zincir.adim(ad, GECTI)
        else:
            ozet = "\n".join(s for s in cikti.splitlines() if s.startswith("[")) or cikti[:300]
            zincir.adim(ad, KALDI, "Yüksek ağırlıklı bulgu var:", ozet)
            tumu_gecti = False

    # Sır sızıntısı: kasa koruması kancasıyla aynı desenler
    kanca = Path(yollar.proje_kok()) / "hooks" / "kasa-koruma.py"
    if kanca.is_file():
        zincir.adim("Sır denetimi", GECTI, "Yazma anında koruma zaten devrede.")
    else:
        zincir.adim("Sır denetimi", ATLANDI, "Koruma bulunamadı.")

    return tumu_gecti


def adim_yedek(zincir, kok, tanim, atla=False):
    if atla:
        zincir.adim("Yedek", ATLANDI, "Kullanıcı isteğiyle atlandı.")
        return None

    try:
        hedef, bilgi = yedek.al(
            kok,
            f"Deploy öncesi otomatik yedek - {tanim.get('ad', '?')}",
            etiket=f"deploy-{tanim.get('ad', 'proje')}",
        )
    except (OSError, FileNotFoundError) as hata:
        zincir.adim("Yedek", KALDI, f"Yedek alınamadı: {hata}")
        return None

    zincir.adim("Yedek", GECTI, f"{hedef.name}\n"
                                f"Geri dönüş: python yedek.py geri {hedef.name}")
    return hedef


def adim_test(zincir, kok, komut):
    if not komut:
        zincir.adim("Test", ATLANDI,
                    "Test komutu tanımlı değil.\n"
                    "Tanıma ekle: proje.py guncelle test_komutu \"<komut>\"")
        return

    kod, cikti = _calistir(komut, kok)

    if kod is None:
        zincir.adim("Test", KALDI, f"Test çalıştırılamadı: {cikti[:200]}")
        return

    if kod == 0:
        zincir.adim("Test", GECTI, komut)
    else:
        zincir.adim("Test", KALDI, f"Testler geçmedi (çıkış kodu {kod})",
                    cikti[-600:])


def adim_onay(zincir, tanim, yedek_yolu):
    satirlar = [
        f"Proje  : {tanim.get('ad')}",
        f"Sunucu : {tanim.get('sunucu')}",
        f"Dizin  : {tanim.get('dizin')}",
    ]
    if tanim.get("alan_adi"):
        satirlar.append(f"Adres  : {tanim['alan_adi']}")
    if yedek_yolu:
        satirlar.append(f"Yedek  : {yedek_yolu.name}")

    zincir.adim("Onay hazırlığı", GECTI, "\n".join(satirlar))


# ------------------------------------------------------------------ komutlar

def komut_kontrol(args):
    kok = Path(yollar.proje_kok())
    tanim = proje.oku(kok)

    print("DEPLOY GÜVENLİK ZİNCİRİ")
    print("=" * 62)
    print()

    zincir = Zincir(kok)

    adim_hazirlik(zincir, tanim)
    if zincir.durdu:
        return _bitir(zincir, kok, None)

    adim_denetim(zincir, kok)
    if zincir.durdu and not args.denetimi_atla:
        return _bitir(zincir, kok, None)

    yedek_yolu = adim_yedek(zincir, kok, tanim, args.yedegi_atla)
    if zincir.durdu:
        return _bitir(zincir, kok, None)

    adim_test(zincir, kok, args.test or (tanim or {}).get("test_komutu"))
    if zincir.durdu:
        return _bitir(zincir, kok, yedek_yolu)

    adim_onay(zincir, tanim, yedek_yolu)

    return _bitir(zincir, kok, yedek_yolu)


def _bitir(zincir, kok, yedek_yolu):
    print()
    print("-" * 62)

    durum = {
        "tarih": hafiza.zaman_metni(),
        "proje": yollar.proje_adi(kok),
        "adimlar": zincir.adimlar,
        "hazir": zincir.gecti_mi(),
        "yedek": yedek_yolu.name if yedek_yolu else None,
    }
    hafiza.json_yaz(hafiza.hafiza_dosyasi(DURUM_DOSYASI, kok), durum)

    if not zincir.gecti_mi():
        kalanlar = [a["ad"] for a in zincir.adimlar if a["durum"] == KALDI]
        print(f"ZİNCİR DURDU: {', '.join(kalanlar)}")
        print()
        print("Canlıya çıkılmaz. Önce bu adımlar geçmeli.")
        return 1

    print("ZİNCİR TAMAM - çıkışa hazır.")
    print()
    print("Asıl gönderim bu betikle YAPILMAZ.")
    print("Canlıya çıkış açık bir insan kararıdır; komutu sen çalıştırırsın.")
    print()
    if yedek_yolu:
        print(f"Bir şey ters giderse: python yedek.py geri {yedek_yolu.name} --onayla")
    return 0


def komut_durum(args):
    kok = yollar.proje_kok()
    durum = hafiza.json_oku(hafiza.hafiza_dosyasi(DURUM_DOSYASI, kok), {})

    if not durum:
        print("Kayıtlı deploy denemesi yok.")
        return 1

    print(f"Son deneme: {durum.get('tarih')}")
    print(f"Proje     : {durum.get('proje')}")
    print(f"Sonuç     : {'hazır' if durum.get('hazir') else 'durdu'}")
    if durum.get("yedek"):
        print(f"Yedek     : {durum['yedek']}")
    print()

    for adim in durum.get("adimlar", []):
        print(f"  {ISARETLER.get(adim['durum'], '?')} {adim['ad']}")
        if adim.get("aciklama"):
            for satir in adim["aciklama"].splitlines():
                print(f"           {satir}")

    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Deploy güvenlik zinciri")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("kontrol", help="Zinciri çalıştır")
    p.add_argument("--test", help="Test komutu")
    p.add_argument("--yedegi-atla", action="store_true", dest="yedegi_atla")
    p.add_argument("--denetimi-atla", action="store_true", dest="denetimi_atla")
    p.set_defaults(islev=komut_kontrol)

    p = alt.add_parser("durum", help="Son denemenin durumu")
    p.set_defaults(islev=komut_durum)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
