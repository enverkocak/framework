#!/usr/bin/env python3
"""Oturum kaydı, özeti ve devir notu.

Akış:
  1. Çalışırken her komut ve dosya değişikliği ham günlüğe yazılır (kaydet).
  2. Oturum biterken ham kayıt özetlenir ve hafızaya geçer (bitir).
  3. Yeni oturum açılırken özet okunur ve "nerede kaldık" gösterilir (brifing).

Ham kayıt makinede kalır, özet depoya girer. Böylece başka bilgisayarda
devam edildiğinde "nerede kaldık" bilgisi hazır olur.

Komutlar:
    kaydet     Ham günlüğe bir olay yaz
    bitir      Oturumu özetle, hafızaya geçir
    brifing    Nerede kaldık - açılış özeti
    durum      Son durumu göster veya güncelle

Geliştirici: Enver KOCAK
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "senkron"))

import hafiza  # noqa: E402
import makine  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

# Özette gösterilmeyecek, gürültü sayılan komutlar
GURULTU = ("ls", "cd", "pwd", "echo", "cat", "clear", "which", "type")


# ---------------------------------------------------------------- kayıt

def kaydet(tur, ozet, ayrinti=None, kok=None):
    """Ham günlüğe bir olay yaz."""
    kayit = {
        "zaman": hafiza.zaman_metni(),
        "makine": makine.kimlik(),
        "tur": tur,
        "ozet": hafiza.gizle(str(ozet))[:400],
    }

    if ayrinti:
        kayit["ayrinti"] = hafiza.gizle(str(ayrinti))[:800]

    hafiza.satir_ekle(hafiza.gunluk_dizini(kok) / hafiza.KOMUT_KAYDI, kayit)
    return kayit


# ---------------------------------------------------------------- özet

def _komut_koku(komut):
    """Komutun ilk kelimesi - hangi araç kullanılmış?"""
    parcalar = str(komut).strip().split()
    return parcalar[0] if parcalar else ""


def ozetle(kayitlar):
    """Ham kayıtlardan okunabilir bir özet çıkar."""
    if not kayitlar:
        return None

    komutlar = [k for k in kayitlar if k.get("tur") == "komut"]
    dosyalar = [k for k in kayitlar if k.get("tur") == "dosya"]
    notlar = [k for k in kayitlar if k.get("tur") == "not"]

    araclar = Counter()
    for kayit in komutlar:
        kok = _komut_koku(kayit.get("ozet", ""))
        if kok and kok not in GURULTU:
            araclar[kok] += 1

    degisen = []
    gorulen = set()
    for kayit in dosyalar:
        yol = kayit.get("ozet", "")
        if yol and yol not in gorulen:
            gorulen.add(yol)
            degisen.append(yol)

    return {
        "baslangic": kayitlar[0].get("zaman"),
        "bitis": kayitlar[-1].get("zaman"),
        "makine": kayitlar[-1].get("makine"),
        "komut_sayisi": len(komutlar),
        "araclar": araclar.most_common(8),
        "degisen_dosyalar": degisen[:25],
        "dosya_sayisi": len(gorulen),
        "notlar": [k.get("ozet") for k in notlar],
    }


def ozet_metni(ozet, proje_adi):
    """Özeti okunabilir belgeye çevir."""
    if not ozet:
        return "Bu oturumda kayda değer bir işlem yapılmadı.\n"

    satirlar = [
        f"**Proje:** {proje_adi}  ",
        f"**Makine:** {ozet['makine']}  ",
        f"**Süre:** {ozet['baslangic']} → {ozet['bitis']}",
        "",
    ]

    if ozet["notlar"]:
        satirlar.append("### Yapılan iş")
        satirlar += [f"- {n}" for n in ozet["notlar"]]
        satirlar.append("")

    if ozet["araclar"]:
        arac_metni = ", ".join(f"{ad} ({sayi})" for ad, sayi in ozet["araclar"])
        satirlar += [f"**Çalıştırılan komutlar:** {ozet['komut_sayisi']} adet",
                     f"**En çok kullanılan:** {arac_metni}", ""]

    if ozet["degisen_dosyalar"]:
        satirlar.append(f"### Değişen dosyalar ({ozet['dosya_sayisi']})")
        satirlar += [f"- `{d}`" for d in ozet["degisen_dosyalar"]]
        if ozet["dosya_sayisi"] > len(ozet["degisen_dosyalar"]):
            kalan = ozet["dosya_sayisi"] - len(ozet["degisen_dosyalar"])
            satirlar.append(f"- ... ve {kalan} dosya daha")
        satirlar.append("")

    return "\n".join(satirlar)


# ---------------------------------------------------------------- komutlar

def komut_kaydet(args):
    kayit = kaydet(args.tur, args.ozet, args.ayrinti)
    print(f"Kaydedildi: [{kayit['tur']}] {kayit['ozet'][:60]}")
    return 0


def komut_bitir(args):
    kok = yollar.proje_kok()
    gunluk_yolu = hafiza.gunluk_dizini(kok) / hafiza.KOMUT_KAYDI

    kayitlar = hafiza.satirlari_oku(gunluk_yolu)
    ozet = ozetle(kayitlar)

    if ozet is None and not args.not_metni:
        print("Kaydedilecek bir şey yok - ham günlük boş.")
        return 0

    proje = yollar.proje_adi(kok)
    govde = ozet_metni(ozet, proje)

    if args.not_metni:
        govde += f"\n### Devir notu\n\n{args.not_metni.strip()}\n"

    if args.sirada:
        govde += f"\n### Sırada ne var\n\n{args.sirada.strip()}\n"

    # Oturum özetini tarihli dosyaya yaz
    oturumlar = hafiza.hafiza_dizini(kok) / hafiza.OTURUMLAR_DIZINI
    tarih = hafiza.tarih_metni()

    sira = 1
    while (oturumlar / f"{tarih}-{sira}.md").exists():
        sira += 1

    hedef = oturumlar / f"{tarih}-{sira}.md"
    hedef.write_text(f"# Oturum özeti - {tarih} ({sira})\n\n{govde}", encoding="utf-8")

    # Durum belgesini güncelle - "nerede kaldık" hep burayı gösterir
    durum_yolu = hafiza.hafiza_dosyasi(hafiza.DURUM_DOSYASI, kok)
    hafiza.baslik_yoksa_yaz(
        durum_yolu, f"{proje} - durum",
        "Bu belge her oturum sonunda güncellenir. En üstteki kayıt en günceldir.",
    )
    hafiza.bolum_ekle(durum_yolu, f"{hafiza.zaman_metni()} - {makine.kimlik()}", govde)

    # Makine kaydını tazele
    makine.tanit()

    print(f"Oturum özeti yazıldı: {hedef}")
    print(f"Durum güncellendi   : {durum_yolu}")

    if args.gunlugu_temizle:
        arsiv_yolu = hafiza.gunluk_dizini(kok) / f"komutlar-{tarih}-{sira}.jsonl"
        gunluk_yolu.replace(arsiv_yolu)
        print(f"Ham günlük arşivlendi: {arsiv_yolu}")

    return 0


def komut_brifing(args):
    kok = yollar.proje_kok()
    proje = yollar.proje_adi(kok)

    print(f"{proje.upper()}")
    print("=" * 52)
    print()

    # Makine durumu
    kendi = makine.bu_makine(kok)
    if kendi:
        print(f"Makine: {kendi.get('ad')}")
    else:
        print(f"Makine: {makine.kimlik()}  (TANINMIYOR)")
        print("  Kaydetmek için: python scripts/senkron/makine.py tanit --ad \"<ad>\"")

    if makine.baska_makinede_mi(kok):
        son = makine.son_calisan(kok)
        print()
        print(f"DİKKAT: Son çalışma başka makinede yapılmış:")
        print(f"  {son.get('ad')} - {son.get('son_gorulme')}")
        print("  Yerel bilgi eski olabilir. Önce: python scripts/senkron/senkron.py cek")

    print()

    # Nerede kaldık
    durum_yolu = hafiza.hafiza_dosyasi(hafiza.DURUM_DOSYASI, kok)
    durum = hafiza.metin_oku(durum_yolu).strip()

    if not durum:
        print("NEREDE KALDIK")
        print("-" * 52)
        print("  Henüz kayıt yok. İlk oturum sonunda oluşacak.")
    else:
        print("NEREDE KALDIK")
        print("-" * 52)
        # En üstteki bölüm en günceldir
        bolumler = durum.split("\n## ")
        if len(bolumler) > 1:
            son_bolum = "## " + bolumler[1]
            satirlar = son_bolum.splitlines()
            for satir in satirlar[: args.satir]:
                print(f"  {satir}")
            if len(satirlar) > args.satir:
                print(f"  ... (tamamı: {durum_yolu})")
        else:
            print(f"  {durum[:400]}")

    # Bekleyen kararlar ve son hatalar
    print()
    for dosya, etiket in ((hafiza.KARARLAR_DOSYASI, "SON KARARLAR"),
                          (hafiza.HATALAR_DOSYASI, "SON ÇÖZÜLEN HATALAR")):
        icerik = hafiza.metin_oku(hafiza.hafiza_dosyasi(dosya, kok)).strip()
        if not icerik:
            continue
        bolumler = [b for b in icerik.split("\n## ") if b.strip()][1:]
        if not bolumler:
            continue
        print(etiket)
        print("-" * 52)
        for bolum in bolumler[:3]:
            print(f"  - {bolum.splitlines()[0]}")
        print()

    return 0


def komut_durum(args):
    kok = yollar.proje_kok()
    durum_yolu = hafiza.hafiza_dosyasi(hafiza.DURUM_DOSYASI, kok)

    if args.yaz:
        hafiza.baslik_yoksa_yaz(durum_yolu, f"{yollar.proje_adi(kok)} - durum")
        hafiza.bolum_ekle(durum_yolu, f"{hafiza.zaman_metni()} - {makine.kimlik()}", args.yaz)
        makine.tanit()
        print(f"Durum kaydedildi: {durum_yolu}")
        return 0

    icerik = hafiza.metin_oku(durum_yolu).strip()
    print(icerik if icerik else "Henüz durum kaydı yok.")
    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Oturum kaydı ve özeti")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("kaydet", help="Ham günlüğe olay yaz")
    p.add_argument("tur", choices=["komut", "dosya", "not"])
    p.add_argument("ozet")
    p.add_argument("--ayrinti")
    p.set_defaults(islev=komut_kaydet)

    p = alt.add_parser("bitir", help="Oturumu özetle ve hafızaya geçir")
    p.add_argument("--not", dest="not_metni", help="Devir notu")
    p.add_argument("--sirada", help="Sırada ne var")
    p.add_argument("--gunlugu-temizle", action="store_true", dest="gunlugu_temizle")
    p.set_defaults(islev=komut_bitir)

    p = alt.add_parser("brifing", help="Nerede kaldık")
    p.add_argument("--satir", type=int, default=30)
    p.set_defaults(islev=komut_brifing)

    p = alt.add_parser("durum", help="Son durumu göster veya yaz")
    p.add_argument("--yaz")
    p.set_defaults(islev=komut_durum)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
