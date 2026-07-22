#!/usr/bin/env python3
"""Keşif - kodlamadan önceki dört aşama.

Yarım anlaşılmış bir işe başlayıp sonra baştan yazmak, en pahalı hatadır.
Bu yüzden koda geçmeden önce dört aşama işletilir:

    1. ISTEK        Ne olacak? Hangi özellikler isteniyor? Sorulur.
    2. ARAŞTIRMA    Ekstra neler olabilir? Benzer işlerde ne var, ne unutuluyor?
    3. NETLEŞTİRME  Araştırmadan çıkanlar üzerinden soru sorulur, belirsizlik kalmaz.
    4. PLAN         Fazlara bölünür, kapı kontrolleri konur, ancak sonra kodlanır.

Aşama atlanamaz. Her aşamanın çıktısı kaydedilir; oturum değişse bile
keşif kaldığı yerden sürer.

Durum `hafıza/keşif/<proje>.json` içinde durur, makineler arasında senkron olur.

Komutlar:
    başlat      Yeni keşif başlat
    durum       Hangi aşamadayız
    yaz         Bir aşamaya bulgu ekle
    sorular     O aşamanın soru listesini göster
    ilerle      Sonraki aşamaya geç
    özet        Keşfin tamamını göster
    plana-dök   Keşiften faz planı üret

Geliştirici: Enver KOCAK
"""

import argparse
import json
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

KESIF_DIZINI = "kesif"

ASAMALAR = ["istek", "arastirma", "netlestirme", "plan"]

ASAMA_ETIKETLERI = {
    "istek": "1. İSTEK TOPLAMA",
    "arastirma": "2. ARAŞTIRMA",
    "netlestirme": "3. NETLEŞTİRME",
    "plan": "4. PLAN",
}

ASAMA_AMACLARI = {
    "istek": "Ne isteniyor? Müşterinin ağzından, olduğu gibi.",
    "arastirma": "Ekstra neler olabilir? Benzer işlerde ne var, ne unutuluyor?",
    "netlestirme": "Belirsizlikler kapatılır. Araştırmadan çıkanlar sorulur.",
    "plan": "Fazlara bölünür, kapı kontrolleri konur.",
}

# Her aşamada sorulacaklar. Bunlar hatırlatıcıdır; sohbetin yerini almaz.
SORULAR = {
    "istek": [
        "Bu iş ne yapacak? Tek cümleyle.",
        "Kim kullanacak? Kaç kişi?",
        "Hangi sorunu çözüyor? Şu an nasıl çözülüyor?",
        "Olmazsa olmaz özellikler neler?",
        "Olsa iyi olur ama şart değil neler?",
        "Kesinlikle istenmeyen bir şey var mı?",
        "Ne zamana yetişmesi gerekiyor?",
        "Bütçe ya da kapsam sınırı var mı?",
        "Mevcut bir sistem var mı? Veri taşınacak mı?",
        "Başka bir sistemle konuşacak mı?",
    ],
    "arastirma": [
        "Benzer işlerde standart olarak ne bulunur?",
        "Bu işte en sık unutulan şey nedir?",
        "Hangi teknik seçenekler var? Artıları eksileri?",
        "Yasal ya da idari zorunluluk var mı? (kişisel veri, fatura, arşiv)",
        "Ölçek büyürse ne kırılır?",
        "Hangi dış servise bağımlı olacak? O servis kapanırsa ne olur?",
        "Mobilde nasıl çalışacak?",
        "Yedek ve geri dönüş nasıl olacak?",
        "Bakımı kim yapacak, nasıl?",
        "Müşteri kendi başına ne yapabilmeli?",
    ],
    "netlestirme": [
        "Araştırmada çıkan şu maddeyi istiyor musunuz? (her madde için)",
        "Şu iki seçenekten hangisi? Neden?",
        "Bu alan zorunlu mu, isteğe bağlı mı?",
        "Bu iş kimin sorumluluğunda: bizde mi, sizde mi?",
        "Şu durumda ne olmasını beklersiniz?",
        "Kapsam dışı bıraktıklarımız kabul mü?",
        "Teslim neyi kapsayacak? Neyi kapsamayacak?",
        "Kabul ölçütü ne? Hangi durumda 'bitti' diyeceğiz?",
    ],
    "plan": [
        "İş kaç faza bölünecek?",
        "Her fazın kapı kontrolü ne olacak?",
        "Hangi faz önce gelmeli? Neden?",
        "Riskli parça hangisi? Erken mi denenmeli?",
        "İlk gösterilebilir sonuç ne zaman çıkar?",
    ],
}


def kesif_dizini(kok=None):
    yol = hafiza.hafiza_dizini(kok) / KESIF_DIZINI
    yol.mkdir(parents=True, exist_ok=True)
    return yol


def _guvenli_ad(ad):
    temiz = "".join(h if h.isalnum() or h in "-_" else "-" for h in ad)
    return temiz.strip("-").lower() or "kesif"


def dosya_yolu(proje=None, kok=None):
    proje = proje or yollar.proje_adi(kok)
    return kesif_dizini(kok) / f"{_guvenli_ad(proje)}.json"


def oku(proje=None, kok=None):
    yol = dosya_yolu(proje, kok)
    if not yol.is_file():
        return None
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def yaz(veri, proje=None, kok=None):
    yol = dosya_yolu(proje or veri.get("proje"), kok)
    yol.write_text(json.dumps(veri, ensure_ascii=False, indent=2) + "\n",
                   encoding="utf-8")
    return yol


def baslat(proje, musteri="", kok=None):
    veri = {
        "proje": proje,
        "musteri": musteri,
        "asama": "istek",
        "baslangic": hafiza.zaman_metni(),
        "bulgular": {asama: [] for asama in ASAMALAR},
        "tamamlanan": [],
    }
    yaz(veri, proje, kok)
    return veri


def bulgu_ekle(metin, asama=None, proje=None, kok=None):
    veri = oku(proje, kok)
    if veri is None:
        return None

    asama = asama or veri["asama"]
    veri["bulgular"].setdefault(asama, []).append({
        "metin": metin.strip(),
        "tarih": hafiza.zaman_metni(),
    })

    yaz(veri, proje, kok)
    return veri


def ilerle(proje=None, kok=None, zorla=False):
    """Sonraki aşamaya geç. Aşama boşsa geçilmez."""
    veri = oku(proje, kok)
    if veri is None:
        return None, "Keşif kaydı yok."

    simdiki = veri["asama"]
    bulgular = veri["bulgular"].get(simdiki, [])

    if not bulgular and not zorla:
        return None, (f"'{ASAMA_ETIKETLERI[simdiki]}' aşamasında hiç bulgu yok.\n"
                      "Aşama atlanamaz. Önce bulgu ekle ya da --zorla kullan.")

    sira = ASAMALAR.index(simdiki)
    if sira >= len(ASAMALAR) - 1:
        veri["tamamlanan"].append(simdiki)
        veri["bitis"] = hafiza.zaman_metni()
        yaz(veri, proje, kok)
        return veri, "Keşif tamamlandı. Artık kodlamaya geçilebilir."

    veri["tamamlanan"].append(simdiki)
    veri["asama"] = ASAMALAR[sira + 1]
    yaz(veri, proje, kok)

    return veri, f"Sıradaki aşama: {ASAMA_ETIKETLERI[veri['asama']]}"


def kodlamaya_hazir_mi(proje=None, kok=None):
    """Keşif bitmeden kodlamaya geçilmemeli."""
    veri = oku(proje, kok)
    if veri is None:
        return False, "Bu proje için keşif başlatılmamış."

    if "bitis" not in veri:
        eksik = [a for a in ASAMALAR if a not in veri.get("tamamlanan", [])]
        return False, (f"Keşif sürüyor. Tamamlanmamış aşamalar: "
                       f"{', '.join(ASAMA_ETIKETLERI[a] for a in eksik)}")

    return True, "Keşif tamamlandı."


# ---------------------------------------------------------------- komutlar

def komut_baslat(args):
    proje = args.proje or yollar.proje_adi()

    if oku(proje) and not args.uzerine_yaz:
        print(f"'{proje}' için keşif zaten başlatılmış.")
        print("Durum için: python kesif.py durum")
        print("Yeniden başlatmak için --uzerine-yaz kullan.")
        return 1

    veri = baslat(proje, args.musteri or "")

    print(f"KEŞİF BAŞLADI - {proje}")
    print("=" * 62)
    print()
    print("Dört aşama var, hiçbiri atlanmaz:")
    for sira, asama in enumerate(ASAMALAR, 1):
        isaret = "→" if asama == veri["asama"] else " "
        print(f" {isaret} {sira}. {ASAMA_ETIKETLERI[asama][3:]:<16} {ASAMA_AMACLARI[asama]}")

    print()
    print(f"Şu anki aşama: {ASAMA_ETIKETLERI[veri['asama']]}")
    print()
    print("Sorular için: python kesif.py sorular")
    return 0


def komut_durum(args):
    veri = oku(args.proje)

    if veri is None:
        print("Bu proje için keşif başlatılmamış.")
        print("Başlatmak için: python kesif.py baslat")
        return 1

    print(f"KEŞİF DURUMU - {veri['proje']}")
    print("=" * 62)
    if veri.get("musteri"):
        print(f"Müşteri: {veri['musteri']}")
    print()

    for sira, asama in enumerate(ASAMALAR, 1):
        sayi = len(veri["bulgular"].get(asama, []))

        if asama in veri.get("tamamlanan", []):
            durum = "tamamlandı"
            isaret = " "
        elif asama == veri["asama"]:
            durum = "çalışılıyor"
            isaret = "→"
        else:
            durum = "bekliyor"
            isaret = " "

        print(f" {isaret} {sira}. {ASAMA_ETIKETLERI[asama][3:]:<16} "
              f"{durum:<12} {sayi} bulgu")

    print()

    hazir, mesaj = kodlamaya_hazir_mi(args.proje)
    if hazir:
        print("KEŞİF TAMAMLANDI - kodlamaya geçilebilir.")
    else:
        print(f"KODLAMAYA GEÇİLMEZ: {mesaj}")

    return 0


def komut_sorular(args):
    veri = oku(args.proje)
    asama = args.asama or (veri["asama"] if veri else "istek")

    print(f"{ASAMA_ETIKETLERI[asama]}")
    print("=" * 62)
    print(ASAMA_AMACLARI[asama])
    print()

    for sira, soru in enumerate(SORULAR[asama], 1):
        print(f"  {sira}. {soru}")

    print()
    print("Bunlar hatırlatıcıdır; sohbetin yerini almaz.")
    print("Cevapları kaydetmek için: python kesif.py yaz \"<bulgu>\"")
    return 0


def komut_yaz(args):
    veri = bulgu_ekle(args.metin, args.asama, args.proje)

    if veri is None:
        print("Keşif kaydı yok. Önce: python kesif.py baslat")
        return 1

    asama = args.asama or veri["asama"]
    sayi = len(veri["bulgular"][asama])

    print(f"Kaydedildi ({ASAMA_ETIKETLERI[asama]}, {sayi}. bulgu)")
    print(f"  {args.metin[:70]}")
    return 0


def komut_ilerle(args):
    veri, mesaj = ilerle(args.proje, zorla=args.zorla)

    if veri is None:
        print(mesaj)
        return 1

    print(mesaj)

    if "bitis" not in veri:
        print()
        print(f"Sorular için: python kesif.py sorular")

    return 0


def komut_ozet(args):
    veri = oku(args.proje)

    if veri is None:
        print("Keşif kaydı yok.")
        return 1

    print(f"KEŞİF ÖZETİ - {veri['proje']}")
    print("=" * 66)
    if veri.get("musteri"):
        print(f"Müşteri: {veri['musteri']}")
    print(f"Başlangıç: {veri.get('baslangic')}")
    if veri.get("bitis"):
        print(f"Bitiş: {veri['bitis']}")
    print()

    for asama in ASAMALAR:
        bulgular = veri["bulgular"].get(asama, [])
        if not bulgular:
            continue

        print(f"{ASAMA_ETIKETLERI[asama]} ({len(bulgular)})")
        print("-" * 66)
        for bulgu in bulgular:
            print(f"  - {bulgu['metin']}")
        print()

    return 0


def komut_plana_dok(args):
    veri = oku(args.proje)

    if veri is None:
        print("Keşif kaydı yok.")
        return 1

    hazir, mesaj = kodlamaya_hazir_mi(args.proje)
    if not hazir and not args.zorla:
        print(f"Keşif tamamlanmadan plan üretilmez.")
        print(mesaj)
        return 1

    plan_bulgulari = veri["bulgular"].get("plan", [])

    if not plan_bulgulari:
        print("Plan aşamasında bulgu yok; faz planı üretilemez.")
        return 1

    satirlar = [
        f"# {veri['proje']} - Faz planı",
        "",
        "Bu plan keşif sürecinden üretildi.",
        f"Keşif: {veri.get('baslangic')} → {veri.get('bitis', 'sürüyor')}",
        "",
    ]

    for sira, bulgu in enumerate(plan_bulgulari, 1):
        satirlar += [f"## Faz {sira}", "", bulgu["metin"], "",
                     "**Kapı kontrolü:** (tanımlanacak)", ""]

    satirlar += [
        "---",
        "",
        "## Keşif özeti",
        "",
    ]

    for asama in ("istek", "arastirma", "netlestirme"):
        bulgular = veri["bulgular"].get(asama, [])
        if not bulgular:
            continue
        satirlar += [f"### {ASAMA_ETIKETLERI[asama][3:]}", ""]
        satirlar += [f"- {b['metin']}" for b in bulgular]
        satirlar.append("")

    hedef = Path(args.hedef) if args.hedef else Path(yollar.proje_kok()) / "_calisma" / "faz-plani.md"
    hedef.parent.mkdir(parents=True, exist_ok=True)
    hedef.write_text("\n".join(satirlar), encoding="utf-8")

    print(f"Faz planı üretildi: {hedef}")
    print(f"  {len(plan_bulgulari)} faz")
    print()
    print("Faz motoruna eklemek için: python scripts/faz/faz.py ekle <no> \"<ad>\"")
    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Keşif - kodlamadan önceki aşamalar")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("baslat", help="Yeni keşif başlat")
    p.add_argument("--proje")
    p.add_argument("--musteri")
    p.add_argument("--uzerine-yaz", action="store_true", dest="uzerine_yaz")
    p.set_defaults(islev=komut_baslat)

    p = alt.add_parser("durum", help="Hangi aşamadayız")
    p.add_argument("--proje")
    p.set_defaults(islev=komut_durum)

    p = alt.add_parser("sorular", help="Aşamanın soru listesi")
    p.add_argument("--proje")
    p.add_argument("--asama", choices=ASAMALAR)
    p.set_defaults(islev=komut_sorular)

    p = alt.add_parser("yaz", help="Bulgu ekle")
    p.add_argument("metin")
    p.add_argument("--proje")
    p.add_argument("--asama", choices=ASAMALAR)
    p.set_defaults(islev=komut_yaz)

    p = alt.add_parser("ilerle", help="Sonraki aşamaya geç")
    p.add_argument("--proje")
    p.add_argument("--zorla", action="store_true")
    p.set_defaults(islev=komut_ilerle)

    p = alt.add_parser("ozet", help="Keşfin tamamı")
    p.add_argument("--proje")
    p.set_defaults(islev=komut_ozet)

    p = alt.add_parser("plana-dok", help="Faz planı üret")
    p.add_argument("--proje")
    p.add_argument("--hedef")
    p.add_argument("--zorla", action="store_true")
    p.set_defaults(islev=komut_plana_dok)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
