#!/usr/bin/env python3
"""Görev takibi - proje bazlı, kalıcı yapılacaklar.

Müşteriye verilen sözler akılda tutulmaz. Buraya yazılır, biri unutulmaz.

Görevler `hafiza/gorevler.json` içinde durur; yani makineler arasında
senkron olur. Bir bilgisayarda eklenen görev diğerinde de görünür.

Her görevin kaynağı yazılır: müşteri isteği mi, kendi kararımız mı,
bulunan bir hata mı. Altı ay sonra "bunu neden yapıyorduk" sorusunun
cevabı burada durur.

Durumlar:
    yapilacak · yapiliyor · beklemede · bitti · iptal

Öncelikler:
    acil · yuksek · normal · dusuk

Komutlar:
    ekle      Yeni görev
    liste     Görevleri göster
    bitir     Görevi tamamla
    durum     Görevin durumunu değiştir
    ozet      Bütün projelerin görev özeti

Geliştirici: Enver KOCAK
"""

import argparse
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

GOREV_DOSYASI = "gorevler.json"

DURUMLAR = ["yapilacak", "yapiliyor", "beklemede", "bitti", "iptal"]
ONCELIKLER = ["acil", "yuksek", "normal", "dusuk"]
KAYNAKLAR = ["musteri", "kendi", "hata", "bakim"]

DURUM_ETIKETLERI = {
    "yapilacak": "Yapılacak", "yapiliyor": "Yapılıyor",
    "beklemede": "Beklemede", "bitti": "Bitti", "iptal": "İptal",
}

ONCELIK_ETIKETLERI = {
    "acil": "ACİL", "yuksek": "yüksek", "normal": "normal", "dusuk": "düşük",
}

KAYNAK_ETIKETLERI = {
    "musteri": "müşteri isteği", "kendi": "kendi kararımız",
    "hata": "bulunan hata", "bakim": "bakım işi",
}

ONCELIK_SIRASI = {"acil": 0, "yuksek": 1, "normal": 2, "dusuk": 3}
DURUM_SIRASI = {"yapiliyor": 0, "yapilacak": 1, "beklemede": 2, "bitti": 3, "iptal": 4}

ACIK_DURUMLAR = ("yapilacak", "yapiliyor", "beklemede")


def dosya_yolu(kok=None):
    return hafiza.hafiza_dosyasi(GOREV_DOSYASI, kok)


def oku(kok=None):
    veri = hafiza.json_oku(dosya_yolu(kok), {"gorevler": []})
    veri.setdefault("gorevler", [])
    return veri


def yaz(veri, kok=None):
    hafiza.json_yaz(dosya_yolu(kok), veri)


def _sonraki_no(veri):
    return max((g.get("no", 0) for g in veri["gorevler"]), default=0) + 1


def ekle(baslik, proje=None, oncelik="normal", kaynak="kendi",
         aciklama="", tarih=None, kok=None):
    veri = oku(kok)

    gorev = {
        "no": _sonraki_no(veri),
        "baslik": baslik.strip(),
        "proje": proje or yollar.proje_adi(kok),
        "oncelik": oncelik,
        "kaynak": kaynak,
        "aciklama": aciklama.strip(),
        "durum": "yapilacak",
        "olusturma": hafiza.zaman_metni(),
        "son_tarih": tarih,
        "bitis": None,
    }

    veri["gorevler"].append(gorev)
    yaz(veri, kok)
    return gorev


def gorev_bul(no, kok=None):
    for gorev in oku(kok)["gorevler"]:
        if gorev.get("no") == no:
            return gorev
    return None


def durum_degistir(no, yeni_durum, kok=None):
    veri = oku(kok)

    for gorev in veri["gorevler"]:
        if gorev.get("no") != no:
            continue

        gorev["durum"] = yeni_durum
        if yeni_durum in ("bitti", "iptal"):
            gorev["bitis"] = hafiza.zaman_metni()
        else:
            gorev["bitis"] = None

        yaz(veri, kok)
        return gorev

    return None


def suzgecle(proje=None, durum=None, oncelik=None, acik_olanlar=False, kok=None):
    gorevler = oku(kok)["gorevler"]

    if proje:
        gorevler = [g for g in gorevler if g.get("proje") == proje]
    if durum:
        gorevler = [g for g in gorevler if g.get("durum") == durum]
    if oncelik:
        gorevler = [g for g in gorevler if g.get("oncelik") == oncelik]
    if acik_olanlar:
        gorevler = [g for g in gorevler if g.get("durum") in ACIK_DURUMLAR]

    gorevler.sort(key=lambda g: (DURUM_SIRASI.get(g.get("durum"), 9),
                                 ONCELIK_SIRASI.get(g.get("oncelik"), 9),
                                 g.get("no", 0)))
    return gorevler


def _gorev_satiri(gorev, proje_goster=True):
    oncelik = ONCELIK_ETIKETLERI.get(gorev.get("oncelik"), gorev.get("oncelik"))
    durum = DURUM_ETIKETLERI.get(gorev.get("durum"), gorev.get("durum"))

    satirlar = [f"  #{gorev['no']:<4} [{oncelik:>6}] {gorev['baslik']}"]

    ayrinti = [f"durum: {durum}"]
    if proje_goster:
        ayrinti.append(f"proje: {gorev.get('proje', '-')}")
    ayrinti.append(f"kaynak: {KAYNAK_ETIKETLERI.get(gorev.get('kaynak'), '-')}")
    if gorev.get("son_tarih"):
        ayrinti.append(f"tarih: {gorev['son_tarih']}")

    satirlar.append("         " + " · ".join(ayrinti))

    if gorev.get("aciklama"):
        satirlar.append(f"         {gorev['aciklama'][:76]}")

    return "\n".join(satirlar)


# ---------------------------------------------------------------- komutlar

def komut_ekle(args):
    gorev = ekle(args.baslik, args.proje, args.oncelik, args.kaynak,
                 args.aciklama or "", args.tarih)

    print(f"Görev eklendi: #{gorev['no']}")
    print(f"  {gorev['baslik']}")
    print(f"  proje: {gorev['proje']} · öncelik: "
          f"{ONCELIK_ETIKETLERI[gorev['oncelik']]} · "
          f"kaynak: {KAYNAK_ETIKETLERI[gorev['kaynak']]}")

    if gorev["kaynak"] == "musteri":
        print()
        print("Müşteri isteği olarak kaydedildi - unutulmaması gereken bir söz.")

    return 0


def komut_liste(args):
    proje = args.proje
    if not proje and not args.hepsi:
        proje = yollar.proje_adi()

    gorevler = suzgecle(proje, args.durum, args.oncelik,
                        acik_olanlar=not args.kapalilar_dahil)

    baslik = f"GÖREVLER - {proje}" if proje else "GÖREVLER - bütün projeler"
    print(baslik)
    print("=" * 72)

    if not gorevler:
        print()
        print("Açık görev yok.")
        if not args.kapalilar_dahil:
            print("Bitmiş görevleri de görmek için: --kapalilar-dahil")
        return 0

    print()
    for gorev in gorevler[: args.sinir]:
        print(_gorev_satiri(gorev, proje_goster=not proje))
        print()

    if len(gorevler) > args.sinir:
        print(f"... ve {len(gorevler) - args.sinir} görev daha")

    acil = sum(1 for g in gorevler if g.get("oncelik") == "acil")
    if acil:
        print(f"{acil} acil görev var.")

    return 0


def komut_bitir(args):
    gorev = durum_degistir(args.no, "bitti")

    if gorev is None:
        print(f"#{args.no} numaralı görev bulunamadı.")
        return 1

    print(f"Bitti: #{gorev['no']} - {gorev['baslik']}")
    return 0


def komut_durum(args):
    gorev = durum_degistir(args.no, args.durum)

    if gorev is None:
        print(f"#{args.no} numaralı görev bulunamadı.")
        return 1

    print(f"#{gorev['no']} durumu: {DURUM_ETIKETLERI[gorev['durum']]}")
    print(f"  {gorev['baslik']}")
    return 0


def komut_ozet(args):
    gorevler = oku()["gorevler"]

    if not gorevler:
        print("Henüz görev yok.")
        return 0

    projeler = {}
    for gorev in gorevler:
        proje = gorev.get("proje", "-")
        projeler.setdefault(proje, {"acik": 0, "acil": 0, "bitti": 0})

        if gorev.get("durum") in ACIK_DURUMLAR:
            projeler[proje]["acik"] += 1
            if gorev.get("oncelik") == "acil":
                projeler[proje]["acil"] += 1
        elif gorev.get("durum") == "bitti":
            projeler[proje]["bitti"] += 1

    print("GÖREV ÖZETİ")
    print("=" * 66)
    print(f"  {'proje':<32} {'açık':>6} {'acil':>6} {'bitti':>7}")
    print("  " + "-" * 62)

    sirali = sorted(projeler.items(), key=lambda i: (-i[1]["acil"], -i[1]["acik"]))

    for proje, sayilar in sirali:
        print(f"  {proje[:31]:<32} {sayilar['acik']:>6} "
              f"{sayilar['acil']:>6} {sayilar['bitti']:>7}")

    toplam_acik = sum(s["acik"] for s in projeler.values())
    toplam_acil = sum(s["acil"] for s in projeler.values())

    print()
    print(f"Toplam {toplam_acik} açık görev, {toplam_acil} tanesi acil.")
    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Görev takibi")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("ekle", help="Yeni görev")
    p.add_argument("baslik")
    p.add_argument("--proje")
    p.add_argument("--oncelik", choices=ONCELIKLER, default="normal")
    p.add_argument("--kaynak", choices=KAYNAKLAR, default="kendi")
    p.add_argument("--aciklama")
    p.add_argument("--tarih", help="Son tarih (YYYY-AA-GG)")
    p.set_defaults(islev=komut_ekle)

    p = alt.add_parser("liste", help="Görevleri göster")
    p.add_argument("--proje")
    p.add_argument("--hepsi", action="store_true", help="Bütün projeler")
    p.add_argument("--durum", choices=DURUMLAR)
    p.add_argument("--oncelik", choices=ONCELIKLER)
    p.add_argument("--kapalilar-dahil", action="store_true", dest="kapalilar_dahil")
    p.add_argument("--sinir", type=int, default=20)
    p.set_defaults(islev=komut_liste)

    p = alt.add_parser("bitir", help="Görevi tamamla")
    p.add_argument("no", type=int)
    p.set_defaults(islev=komut_bitir)

    p = alt.add_parser("durum", help="Durumu değiştir")
    p.add_argument("no", type=int)
    p.add_argument("durum", choices=DURUMLAR)
    p.set_defaults(islev=komut_durum)

    p = alt.add_parser("ozet", help="Bütün projelerin özeti")
    p.set_defaults(islev=komut_ozet)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
