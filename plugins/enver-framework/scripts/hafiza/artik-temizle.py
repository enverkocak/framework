#!/usr/bin/env python3
"""Hafızadaki test artıklarını ayıklar.

Kapı testleri bir dönem gerçek hafızaya yazdı. Bu betik geriye kalan
test kayıtlarını hafızadan çıkarır: görev listesinden, karar defterinden,
hata kütüphanesinden, cihaz envanterinden ve durum belgesinden.

HİÇBİR VERİ SİLİNMEZ. Değişiklikten önce hafızanın tamamının kopyası
arşive alınır; ayıklanan kayıtlar oradan her zaman geri okunabilir.

Neyin test verisi olduğu tek yerde tanımlıdır: testler/sizinti-kontrol.py.
Aynı imzalar hem denetimde hem temizlikte kullanılır, böylece ikisi
birbirinden ayrı düşemez.

Kullanım:
    python artik-temizle.py --kuru      neyin çıkacağını yazar, dokunmaz
    python artik-temizle.py             arşivler ve ayıklar

Geliştirici: Enver KOCAK
"""

import argparse
import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))

import arsiv  # noqa: E402
import yollar  # noqa: E402


def imzalari_yukle():
    """Sızıntı denetimindeki imzaları oku - tek kaynak orası."""
    yol = SCRIPT_DIZINI.parent / "testler" / "sizinti-kontrol.py"
    tanim = importlib.util.spec_from_file_location("sizinti_kontrol", yol)
    modul = importlib.util.module_from_spec(tanim)
    tanim.loader.exec_module(modul)
    return modul


IMZA = imzalari_yukle()


# ------------------------------------------------------------ belgeler

def belge_ayikla(metin):
    """Markdown defterinden test bloklarını ve satırlarını çıkar.

    İki tür artık vardır:
      - Başlığı test imzası taşıyan bütün bir '## ...' bloğu
      - Gerçek bir oturum özetinin içine karışmış tek satır
    """
    satirlar = metin.splitlines()
    sonuc = []
    atlanan_blok = False
    cikan_satir = 0
    cikan_blok = 0

    for satir in satirlar:
        if satir.startswith("## "):
            atlanan_blok = any(imza in satir for imza in IMZA.BELGE_IMZALARI)
            if atlanan_blok:
                cikan_blok += 1
                continue

        if atlanan_blok:
            continue

        if any(imza in satir for imza in IMZA.BELGE_IMZALARI):
            cikan_satir += 1
            continue

        sonuc.append(satir)

    # Blok çıkarınca arka arkaya boş satır kalabiliyor, sadeleştir
    sade = []
    for satir in sonuc:
        if not satir.strip() and sade and not sade[-1].strip():
            continue
        sade.append(satir)

    return "\n".join(sade).rstrip() + "\n", cikan_blok, cikan_satir


# ------------------------------------------------------------ kayıtlar

def test_kaydi_mi(girdi):
    """Bu JSON kaydı test verisi mi?"""
    for alan, degerler in IMZA.KAYIT_IMZALARI.items():
        deger = str(girdi.get(alan, ""))
        if not deger:
            continue
        if alan in IMZA.ON_EK_ALANLARI:
            if deger.startswith(degerler):
                return True
        elif deger in degerler:
            return True
    return False


def kayit_ayikla(veri):
    """Kayıt dosyasındaki listelerden test girdilerini çıkar."""
    cikan = 0

    if isinstance(veri, dict):
        for anahtar, deger in veri.items():
            if isinstance(deger, list):
                temiz = [g for g in deger
                         if not (isinstance(g, dict) and test_kaydi_mi(g))]
                cikan += len(deger) - len(temiz)
                veri[anahtar] = temiz
            elif isinstance(deger, (dict, list)):
                cikan += kayit_ayikla(deger)
    elif isinstance(veri, list):
        for deger in veri:
            if isinstance(deger, (dict, list)):
                cikan += kayit_ayikla(deger)

    return cikan


# ------------------------------------------------------------ akış

def dosyalari_gez(hafiza_dizini):
    belgeler = sorted(hafiza_dizini.rglob("*.md"))
    kayitlar = sorted(hafiza_dizini.rglob("*.json"))
    return belgeler, kayitlar


def temizle(kok, kuru):
    hafiza_dizini = Path(kok) / "hafiza"
    if not hafiza_dizini.is_dir():
        print(f"Hafıza dizini yok: {hafiza_dizini}")
        return 1

    belgeler, kayitlar = dosyalari_gez(hafiza_dizini)
    planlanan = []
    tamami_test = []

    for yol in belgeler:
        metin = yol.read_text(encoding="utf-8")
        yeni, blok, satir = belge_ayikla(metin)
        if blok or satir:
            planlanan.append((yol, yeni, f"{blok} blok, {satir} satır"))

    for yol in kayitlar:
        try:
            veri = json.loads(yol.read_text(encoding="utf-8"))
        except ValueError:
            continue

        # Dosyanın kendisi tek bir test kaydı mı (örn. keşif dosyası)?
        if isinstance(veri, dict) and test_kaydi_mi(veri):
            tamami_test.append(yol)
            continue

        cikan = kayit_ayikla(veri)
        if cikan:
            yeni = json.dumps(veri, ensure_ascii=False, indent=2) + "\n"
            planlanan.append((yol, yeni, f"{cikan} kayıt"))

    if not planlanan and not tamami_test:
        print("Hafızada test artığı yok.")
        return 0

    print("AYIKLANACAK TEST ARTIKLARI")
    print("-" * 46)
    for yol, _, ozet in planlanan:
        print(f"  {yol.relative_to(kok)}: {ozet}")
    for yol in tamami_test:
        print(f"  {yol.relative_to(kok)}: dosyanın tamamı test verisi")
    print("-" * 46)

    if kuru:
        print("Kuru deneme - hiçbir dosyaya dokunulmadı.")
        return 0

    # Önce yedek: hafızanın tamamının kopyası arşive alınır
    hedef = arsiv.arsivle(
        hafiza_dizini,
        "hafiza kapi testi artiklari",
        "Kapı testleri gerçek hafızaya yazıyordu; artıklar ayıklanmadan "
        "önce hafızanın tamamı kopyalandı. Ayıklanan kayıtlar buradan "
        "geri okunabilir.",
        sonuc="Testler kum havuzuna yonlendirildi, artiklar ayiklandi.",
        tasi=False,
    )
    print(f"\nYedek alındı: {hedef}")

    for yol, yeni, _ in planlanan:
        yol.write_text(yeni, encoding="utf-8")

    for yol in tamami_test:
        arsiv.arsivle(
            yol,
            f"hafiza test dosyasi {yol.stem}",
            "Kapı testinin ürettiği kayıt dosyası; gerçek hafızada yeri yok.",
            tasi=True,
        )

    print(f"Ayıklandı: {len(planlanan)} dosya düzeltildi, "
          f"{len(tamami_test)} dosya arşive taşındı.")
    return 0


def main():
    cozumleyici = argparse.ArgumentParser(
        description="Hafızadaki kapı testi artıklarını ayıklar")
    cozumleyici.add_argument("--kuru", action="store_true",
                             help="Neyin çıkacağını yazar, dosyalara dokunmaz")
    cozumleyici.add_argument("--kok", default=None, help="Proje kökü")
    secenekler = cozumleyici.parse_args()

    kok = Path(secenekler.kok or yollar.proje_kok()).resolve()
    return temizle(kok, secenekler.kuru)


if __name__ == "__main__":
    sys.exit(main())
