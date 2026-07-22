#!/usr/bin/env python3
"""Faz motoru - plan, ilerleme ve kapı kontrolü.

Faz planı varsa sırasına uyulur, faz atlanmaz. Her fazın sonunda bir
kapı kontrolü vardır; geçilmeden sonraki faza geçilmez.

Plan `hafiza/faz-plani.json` içinde durur, yani makineler arasında senkron olur.
Bir bilgisayarda ilerlenen faz diğerinde de ilerlemiş görünür.

Kapı kontrolü bir komuttur. Çıkış kodu sıfırsa kapı açılır, değilse kapalı
kalır. Böylece "bitti" demek bir görüş değil, ölçüm sonucu olur.

Komutlar:
    durum      Aktif faz ve ilerleme
    plan       Bütün fazlar
    kapi       Aktif fazın kapı kontrolünü çalıştır
    ilerle     Kapı geçtiyse sonraki faza geç
    ekle       Plana faz ekle
    ayarla     Bir fazın alanını güncelle

Geliştirici: Enver KOCAK
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "hafiza"))

import hafiza  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

PLAN_DOSYASI = "faz-plani.json"

DURUMLAR = ["bekliyor", "calisiyor", "kapi-bekliyor", "tamamlandi"]

DURUM_ETIKETLERI = {
    "bekliyor": "Bekliyor",
    "calisiyor": "Çalışıyor",
    "kapi-bekliyor": "Kapı bekliyor",
    "tamamlandi": "Tamamlandı",
}


def _numara(deger):
    """Faz numarasini sayiya cevir.

    Numara metin olarak saklanirsa siralama alfabetik olur:
    0, 1, 10, 11, 2, 3... Bu da aktif fazi yanlis hesaplatir.
    """
    try:
        return int(str(deger).strip())
    except (TypeError, ValueError):
        return deger


def _sira_anahtari(faz):
    """Sayilar once ve buyukluge gore, sayi olmayanlar sonra."""
    no = faz.get("no")
    return (0, no, "") if isinstance(no, int) else (1, 0, str(no))


def plan_duzelt(kok=None):
    """Eski kayitlarda metin olarak saklanmis numaralari sayiya cevir."""
    veri = plan_oku(kok)
    degisti = False

    for faz in veri["fazlar"]:
        yeni = _numara(faz.get("no"))
        if yeni != faz.get("no"):
            faz["no"] = yeni
            degisti = True

    sirali = sorted(veri["fazlar"], key=_sira_anahtari)
    if sirali != veri["fazlar"]:
        veri["fazlar"] = sirali
        degisti = True

    if degisti:
        plan_yaz(veri, kok)

    return degisti


def plan_yolu(kok=None):
    return hafiza.hafiza_dosyasi(PLAN_DOSYASI, kok)


def plan_oku(kok=None):
    veri = hafiza.json_oku(plan_yolu(kok), {"fazlar": []})
    veri.setdefault("fazlar", [])
    return veri


def plan_yaz(veri, kok=None):
    hafiza.json_yaz(plan_yolu(kok), veri)


def aktif_faz(kok=None):
    """Şu an hangi fazdayız?

    Tamamlanmamış ilk faz aktiftir. Hepsi tamamlandıysa None döner.
    """
    for faz in plan_oku(kok)["fazlar"]:
        if faz.get("durum") != "tamamlandi":
            return faz
    return None


def faz_bul(no, kok=None):
    for faz in plan_oku(kok)["fazlar"]:
        if str(faz.get("no")) == str(no):
            return faz
    return None


def kapi_calistir(faz, kok=None):
    """Fazın kapı kontrolünü çalıştır, (gecti, cikti) döndür."""
    komut = faz.get("kapi_komutu")
    if not komut:
        return None, "Bu faza kapı kontrolü tanımlanmamış."

    kok = kok or yollar.proje_kok()

    try:
        sonuc = subprocess.run(
            komut, shell=True, cwd=str(kok),
            capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=900,
        )
    except (OSError, subprocess.TimeoutExpired) as hata:
        return False, f"Kapı kontrolü çalıştırılamadı: {hata}"

    cikti = (sonuc.stdout or "") + (sonuc.stderr or "")

    # Kapı testleri "N gecti, M kaldi" biçiminde rapor veriyor
    gecti = sonuc.returncode == 0
    if "kaldi" in cikti:
        import re
        eslesme = re.search(r"(\d+)\s+gecti,\s+(\d+)\s+kaldi", cikti)
        if eslesme:
            gecti = int(eslesme.group(2)) == 0

    return gecti, cikti


def ilerlet(kok=None, zorla=False):
    """Aktif fazı tamamla, sonrakine geç."""
    veri = plan_oku(kok)
    faz = aktif_faz(kok)

    if faz is None:
        return False, "Bütün fazlar tamamlanmış."

    if not zorla:
        gecti, cikti = kapi_calistir(faz, kok)
        if gecti is None:
            return False, cikti
        if not gecti:
            return False, "Kapı kontrolü geçmedi. Faz kapalı kalıyor.\n\n" + cikti[-1500:]

    for kayit in veri["fazlar"]:
        if kayit.get("no") == faz.get("no"):
            kayit["durum"] = "tamamlandi"
            kayit["tamamlanma"] = hafiza.zaman_metni()
            break

    sonraki = aktif_faz_hesapla(veri)
    if sonraki:
        sonraki["durum"] = "calisiyor"
        sonraki.setdefault("baslangic", hafiza.zaman_metni())

    plan_yaz(veri, kok)

    if sonraki:
        return True, f"Faz {faz['no']} tamamlandı. Sıradaki: Faz {sonraki['no']} - {sonraki['ad']}"
    return True, f"Faz {faz['no']} tamamlandı. Bütün fazlar bitti."


def aktif_faz_hesapla(veri):
    for faz in veri["fazlar"]:
        if faz.get("durum") != "tamamlandi":
            return faz
    return None


def ilerleme(kok=None):
    """Kaç faz bitti, kaç kaldı."""
    fazlar = plan_oku(kok)["fazlar"]
    if not fazlar:
        return 0, 0
    biten = sum(1 for f in fazlar if f.get("durum") == "tamamlandi")
    return biten, len(fazlar)


# ---------------------------------------------------------------- komutlar

def komut_durum(args):
    kok = yollar.proje_kok()
    faz = aktif_faz(kok)
    biten, toplam = ilerleme(kok)

    if toplam == 0:
        print("Faz planı yok.")
        print("Oluşturmak için: python faz.py ekle <no> \"<ad>\" --kapi \"<komut>\"")
        return 1

    print(f"İLERLEME: {biten}/{toplam} faz tamamlandı")
    print("=" * 56)

    if faz is None:
        print("Bütün fazlar tamamlandı.")
        return 0

    print(f"Aktif faz : {faz['no']} - {faz['ad']}")
    print(f"Durum     : {DURUM_ETIKETLERI.get(faz.get('durum'), faz.get('durum'))}")

    if faz.get("aciklama"):
        print(f"Kapsam    : {faz['aciklama']}")

    if faz.get("kapi_komutu"):
        print(f"Kapı      : {faz['kapi_komutu']}")
    else:
        print("Kapı      : tanımlanmamış")

    if faz.get("maddeler"):
        print()
        print("Maddeler:")
        for madde in faz["maddeler"]:
            print(f"  - {madde}")

    return 0


def komut_plan(args):
    kok = yollar.proje_kok()
    fazlar = plan_oku(kok)["fazlar"]

    if not fazlar:
        print("Faz planı yok.")
        return 1

    aktif = aktif_faz(kok)
    aktif_no = aktif.get("no") if aktif else None

    print("FAZ PLANI")
    print("=" * 62)

    for faz in fazlar:
        isaret = "→" if faz.get("no") == aktif_no else " "
        durum = DURUM_ETIKETLERI.get(faz.get("durum"), faz.get("durum", "-"))
        print(f" {isaret} Faz {faz['no']:<3} {faz['ad']:<40} {durum}")

    biten, toplam = ilerleme(kok)
    print()
    print(f"{biten}/{toplam} tamamlandı")
    return 0


def komut_kapi(args):
    kok = yollar.proje_kok()
    faz = aktif_faz(kok)

    if faz is None:
        print("Aktif faz yok.")
        return 1

    print(f"Faz {faz['no']} kapı kontrolü çalışıyor...")
    print()

    gecti, cikti = kapi_calistir(faz, kok)

    if gecti is None:
        print(cikti)
        return 1

    print(cikti[-3000:])
    print()

    if gecti:
        print(f"KAPI AÇIK - Faz {faz['no']} tamamlanabilir.")
        print("Geçmek için: python faz.py ilerle")
        return 0

    print(f"KAPI KAPALI - Faz {faz['no']} devam ediyor.")
    return 1


def komut_ilerle(args):
    basarili, mesaj = ilerlet(zorla=args.zorla)
    print(mesaj)
    return 0 if basarili else 1


def komut_ekle(args):
    kok = yollar.proje_kok()
    veri = plan_oku(kok)

    if any(str(f.get("no")) == str(args.no) for f in veri["fazlar"]):
        print(f"Faz {args.no} zaten var.")
        return 1

    veri["fazlar"].append({
        # Numara SAYI olarak saklanir. Metin olarak saklanirsa siralama
        # alfabetik olur ve "10" ile "11", "2"den once gelir.
        "no": _numara(args.no),
        "ad": args.ad,
        "aciklama": args.aciklama or "",
        "kapi_komutu": args.kapi or "",
        "maddeler": args.madde or [],
        "durum": "bekliyor",
    })

    veri["fazlar"].sort(key=_sira_anahtari)
    plan_yaz(veri, kok)

    print(f"Faz {args.no} eklendi: {args.ad}")
    return 0


def komut_ayarla(args):
    kok = yollar.proje_kok()
    veri = plan_oku(kok)

    bulundu = False
    for faz in veri["fazlar"]:
        if str(faz.get("no")) == str(args.no):
            try:
                faz[args.alan] = json.loads(args.deger)
            except json.JSONDecodeError:
                faz[args.alan] = args.deger
            bulundu = True
            break

    if not bulundu:
        print(f"Faz {args.no} bulunamadı.")
        return 1

    plan_yaz(veri, kok)
    print(f"Faz {args.no}: {args.alan} güncellendi.")
    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Faz motoru")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("durum", help="Aktif faz ve ilerleme")
    p.set_defaults(islev=komut_durum)

    p = alt.add_parser("plan", help="Bütün fazlar")
    p.set_defaults(islev=komut_plan)

    p = alt.add_parser("kapi", help="Kapı kontrolünü çalıştır")
    p.set_defaults(islev=komut_kapi)

    p = alt.add_parser("ilerle", help="Sonraki faza geç")
    p.add_argument("--zorla", action="store_true", help="Kapıyı atlayarak geç")
    p.set_defaults(islev=komut_ilerle)

    p = alt.add_parser("ekle", help="Plana faz ekle")
    p.add_argument("no")
    p.add_argument("ad")
    p.add_argument("--aciklama")
    p.add_argument("--kapi")
    p.add_argument("--madde", action="append")
    p.set_defaults(islev=komut_ekle)

    p = alt.add_parser("ayarla", help="Bir fazın alanını güncelle")
    p.add_argument("no")
    p.add_argument("alan")
    p.add_argument("deger")
    p.set_defaults(islev=komut_ayarla)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
