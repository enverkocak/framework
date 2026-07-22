#!/usr/bin/env python3
"""Müşteri teslim paketi.

Teslim, dosyaları göndermekten ibaret değildir. Müşterinin eline geçmesi
gerekenler bir listede durur ve hiçbiri unutulmaz:

    kilavuz      Kullanım kılavuzu - müşteri ne yapacağını bilsin
    teknik       Teknik doküman - başka biri devralabilsin
    erisim       Erişim bilgileri - NEREDE olduğu, kendisi değil
    tutanak      Teslim tutanağı - imzalanacak belge
    kvkk         Kişisel veri kontrol listesi

ÖNEMLİ: Erişim belgesine parola YAZILMAZ. Belge, hangi bilginin kasada
durduğunu söyler; bilginin kendisi ayrı ve güvenli bir yoldan verilir.
Teslim belgesi e-postayla dolaşır, parola dolaşmamalı.

Komutlar:
    hazirla    Teslim paketini üret
    kontrol    Teslime hazır mı
    liste      Pakette neler var

Geliştirici: Enver KOCAK
"""

import argparse
import html
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "ortak"))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "hafiza"))
sys.path.insert(0, str(SCRIPT_DIZINI.parent / "projeler"))

import ayarlar  # noqa: E402
import hafiza  # noqa: E402
import proje  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

# Teslimden önce sağlanması gereken koşullar
HAZIRLIK_KOSULLARI = [
    ("tanim", "Proje tanımı var mı",
     "Tanım olmadan kılavuz ve teknik belge üretilemez."),
    ("gorev", "Açık acil görev kaldı mı",
     "Acil görevler kapanmadan teslim edilmez."),
    ("kalip", "Kalıp denetimi geçti mi",
     "Şablon hissi veren bulgular teslimden önce giderilir."),
    ("denetim", "Teslim öncesi denetimler geçti mi",
     "Güvenlik ve erişilebilirlik bulguları kapanmalı."),
]

KVKK_MADDELERI = [
    ("cerez", "Çerez bildirimi var mı",
     "Site çerez kullanıyorsa ziyaretçiye bildirilmeli ve onayı alınmalı."),
    ("aydinlatma", "Aydınlatma metni var mı",
     "Kişisel veri toplanıyorsa hangi veri, ne amaçla, ne kadar süre saklanacak yazılmalı."),
    ("acik-riza", "Açık rıza alınıyor mu",
     "Pazarlama izni gibi ek kullanımlar için ayrı onay gerekir."),
    ("form-veri", "Formlarda gereksiz veri isteniyor mu",
     "Yalnız işin gerektirdiği alanlar istenmeli; fazlası risktir."),
    ("saklama", "Veri saklama süresi belirlendi mi",
     "Süresiz saklama kabul edilmez."),
    ("silme", "Silme talebi karşılanabiliyor mu",
     "Kullanıcı verisinin silinmesi istenebilir; teknik olarak mümkün olmalı."),
    ("aktarim", "Veri üçüncü tarafa aktarılıyor mu",
     "Analiz, e-posta, ödeme sağlayıcıları aktarım sayılır ve bildirilmeli."),
    ("guvenlik", "Veri güvenliği önlemi alındı mı",
     "Şifreli bağlantı, sınırlı erişim, düzenli yedek."),
]


def _kacir(metin):
    return html.escape(str(metin or ""))


# ---------------------------------------------------------------- belgeler

def kilavuz_uret(tanim, kok):
    ad = tanim.get("ad", yollar.proje_adi(kok))

    satirlar = [
        f"# {ad} - Kullanım Kılavuzu",
        "",
        f"**Tarih:** {date.today().isoformat()}",
        "",
    ]

    if tanim.get("gorev") or tanim.get("aciklama"):
        satirlar += ["## Bu sistem ne yapar", "",
                     tanim.get("gorev") or tanim.get("aciklama"), ""]

    if tanim.get("alan_adi"):
        satirlar += ["## Adres", "", f"https://{tanim['alan_adi']}", ""]
        if tanim.get("alt_alan_adlari"):
            satirlar.append("Diğer adresler:")
            satirlar += [f"- https://{a}" for a in tanim["alt_alan_adlari"]]
            satirlar.append("")

    servisler = tanim.get("servisler", [])
    if servisler:
        satirlar += ["## Bölümler", ""]
        for servis in servisler:
            gorev = servis.get("gorev") or servis.get("aciklama") or ""
            satirlar.append(f"### {servis.get('ad')}")
            satirlar += ["", gorev, ""]

    satirlar += [
        "## Sık sorulanlar",
        "",
        "**Şifremi unuttum, ne yapmalıyım?**  ",
        "Giriş ekranındaki şifre sıfırlama bağlantısını kullanın.",
        "",
        "**Bir şey bozuk görünüyor.**  ",
        "Ekran görüntüsü alıp iletin; hangi sayfada ve ne yaparken olduğunu yazın.",
        "",
        "**Yeni bir özellik istiyorum.**  ",
        "Ne yapmak istediğinizi yazın; kapsam ve süre birlikte değerlendirilir.",
        "",
        "## Destek",
        "",
        f"{ayarlar.kimlik(kok).get('gelistirici') or '(geliştirici)'}  ",
        f"{ayarlar.kimlik_satiri(kok)}",
        "",
    ]

    return "\n".join(satirlar)


def teknik_uret(tanim, kok):
    ad = tanim.get("ad", yollar.proje_adi(kok))

    satirlar = [
        f"# {ad} - Teknik Belge",
        "",
        "Bu belge, sistemi başka birinin devralabilmesi için yazılmıştır.",
        "",
        f"**Tarih:** {date.today().isoformat()}",
        "",
        "## Genel",
        "",
    ]

    alanlar = [
        ("Görev", tanim.get("gorev")),
        ("Sunucu", tanim.get("sunucu")),
        ("Dizin", tanim.get("dizin")),
        ("Alan adı", tanim.get("alan_adi")),
        ("Veritabanı", tanim.get("veritabani")),
    ]
    for etiket, deger in alanlar:
        if deger:
            satirlar.append(f"- **{etiket}:** {deger}")

    if tanim.get("teknolojiler"):
        satirlar.append(f"- **Teknolojiler:** {', '.join(tanim['teknolojiler'])}")

    satirlar.append("")

    servisler = tanim.get("servisler", [])
    if servisler:
        satirlar += ["## Çalışan bileşenler", "",
                     "| Bileşen | Tür | Görev |", "|---------|-----|-------|"]
        for servis in servisler:
            satirlar.append(f"| {servis.get('ad')} | {servis.get('tur', '-')} | "
                            f"{servis.get('gorev') or servis.get('aciklama') or '-'} |")
        satirlar.append("")

    baglantilar = tanim.get("baglantilar", [])
    if baglantilar:
        satirlar += ["## Bağlı sistemler", ""]
        for bag in baglantilar:
            satirlar.append(f"- **{bag.get('hedef')}** ({bag.get('tur', '-')}) — "
                            f"{bag.get('aciklama', '')}")
        satirlar.append("")

    satirlar += [
        "## Yedek ve geri dönüş",
        "",
        "Yedekler `_arsiv/yedekler/` altında tarihli klasörlerde durur.",
        "Her yedeğin yanında ne için alındığı yazar.",
        "",
        "## Erişim bilgileri",
        "",
        "**Bu belgede parola bulunmaz.** Erişim bilgileri ayrı ve güvenli",
        "bir yoldan iletilir. Bakınız: erişim belgesi.",
        "",
    ]

    return "\n".join(satirlar)


def erisim_uret(tanim, kok):
    ad = tanim.get("ad", yollar.proje_adi(kok))

    satirlar = [
        f"# {ad} - Erişim Bilgileri",
        "",
        "> **Bu belgede parola YAZILMAZ.**",
        "> Belge, hangi bilginin nerede durduğunu söyler.",
        "> Bilginin kendisi ayrı ve güvenli bir yoldan iletilir.",
        "",
        f"**Tarih:** {date.today().isoformat()}",
        "",
        "## Nerede ne var",
        "",
    ]

    kayitlar = []
    if tanim.get("sunucu"):
        kayitlar.append(("Sunucu erişimi", tanim["sunucu"], "kasa"))
    if tanim.get("veritabani"):
        kayitlar.append(("Veritabanı", tanim["veritabani"], "kasa"))
    if tanim.get("alan_adi"):
        kayitlar.append(("Alan adı yönetimi", tanim["alan_adi"], "kayıt firması paneli"))

    if tanim.get("kasa_anahtari"):
        kayitlar.append(("Diğer bilgiler", tanim["kasa_anahtari"], "kasa"))

    if kayitlar:
        satirlar += ["| Ne | Hedef | Nerede tutuluyor |",
                     "|----|-------|------------------|"]
        for ne, hedef, nerede in kayitlar:
            satirlar.append(f"| {ne} | {hedef} | {nerede} |")
    else:
        satirlar.append("Tanımda erişim bilgisi kaydı yok.")

    # Kayit olsun olmasin, bilginin nerede durdugu HER ZAMAN yazilir.
    # Bu belgenin varlik sebebi zaten bu kural; kayit bos diye atlanmaz.
    satirlar += [
        "",
        "## Bilgiler nerede duruyor",
        "",
        "Parola, anahtar ve erişim bilgileri **kasada** (şifreli) tutulur.",
        "Kasa parola olmadan açılmaz; bu belgeye hiçbir değer yazılmaz.",
        "",
        "## Teslim yöntemi",
        "",
        "Erişim bilgileri şu yollardan biriyle iletilir:",
        "",
        "1. Yüz yüze ya da telefonla",
        "2. Şifre yöneticisi üzerinden paylaşım",
        "3. Süresi dolan tek kullanımlık bağlantı",
        "",
        "E-posta ya da mesajlaşma uygulamasıyla düz metin olarak gönderilmez.",
        "",
    ]

    return "\n".join(satirlar)


def tutanak_uret(tanim, kok):
    ad = tanim.get("ad", yollar.proje_adi(kok))
    musteri = tanim.get("musteri") or "____________________"

    satirlar = [
        "# Teslim Tutanağı",
        "",
        f"**Proje:** {ad}  ",
        f"**Müşteri:** {musteri}  ",
        f"**Teslim tarihi:** {date.today().isoformat()}  ",
        "**Geliştirici:** {ayarlar.kimlik_satiri(kok)}",
        "",
        "## Teslim edilenler",
        "",
        "- [ ] Çalışan sistem",
        "- [ ] Kullanım kılavuzu",
        "- [ ] Teknik belge",
        "- [ ] Erişim bilgileri (ayrı kanaldan)",
        "- [ ] Kaynak dosyalar",
        "",
    ]

    servisler = tanim.get("servisler", [])
    if servisler:
        satirlar += ["## Kapsam", ""]
        satirlar += [f"- {s.get('ad')}: {s.get('gorev') or s.get('aciklama') or '-'}"
                     for s in servisler]
        satirlar.append("")

    satirlar += [
        "## Kapsam dışı",
        "",
        "Aşağıdakiler bu teslimin kapsamında değildir; ayrıca değerlendirilir:",
        "",
        "- İçerik girişi ve veri taşıma",
        "- Yeni özellik geliştirme",
        "- Üçüncü taraf servis ücretleri (hosting, alan adı, lisans)",
        "- Eğitim ve düzenli bakım",
        "",
        "## Onay",
        "",
        "Yukarıda listelenen işlerin teslim alındığını beyan ederim.",
        "",
        "| | Müşteri | Geliştirici |",
        "|---|---------|-------------|",
        f"| Ad Soyad | | {ayarlar.kimlik(kok).get('gelistirici') or ''} |",
        "| Tarih | | |",
        "| İmza | | |",
        "",
    ]

    return "\n".join(satirlar)


def kvkk_uret(tanim, kok):
    ad = tanim.get("ad", yollar.proje_adi(kok))

    satirlar = [
        f"# {ad} - Kişisel Veri Kontrol Listesi",
        "",
        "Teslimden önce her maddenin cevaplanması gerekir.",
        "Cevabı 'hayır' olan bir madde varsa, bu bilinçli bir karar olmalı.",
        "",
        f"**Tarih:** {date.today().isoformat()}",
        "",
    ]

    for _, soru, aciklama in KVKK_MADDELERI:
        satirlar += [f"## {soru}", "", f"{aciklama}", "",
                     "- [ ] Evet  - [ ] Hayır  - [ ] Uygulanmaz", "",
                     "**Not:**", "", ""]

    satirlar += [
        "---",
        "",
        "Bu liste bir hukuki görüş değildir; unutulmaması gerekenleri hatırlatır.",
        "Kapsamlı değerlendirme için hukuk danışmanına başvurulmalıdır.",
        "",
    ]

    return "\n".join(satirlar)


BELGELER = {
    "kilavuz": ("kullanim-kilavuzu.md", kilavuz_uret),
    "teknik": ("teknik-belge.md", teknik_uret),
    "erisim": ("erisim-bilgileri.md", erisim_uret),
    "tutanak": ("teslim-tutanagi.md", tutanak_uret),
    "kvkk": ("kisisel-veri-kontrol-listesi.md", kvkk_uret),
}


# ---------------------------------------------------------------- komutlar

def komut_hazirla(args):
    kok = Path(yollar.proje_kok())
    tanim = proje.oku(kok)

    if tanim is None:
        print("Proje tanımı yok. Teslim paketi üretilemez.")
        print("Oluştur: python scripts/projeler/proje.py olustur")
        return 1

    hedef = Path(args.hedef) if args.hedef else kok / "_calisma" / "teslim"
    hedef.mkdir(parents=True, exist_ok=True)

    secilenler = args.belge or list(BELGELER)

    print(f"TESLİM PAKETİ - {tanim.get('ad')}")
    print("=" * 62)
    print()

    uretilen = []
    for anahtar in secilenler:
        dosya_adi, uretici = BELGELER[anahtar]
        icerik = uretici(tanim, kok)
        yol = hedef / dosya_adi
        yol.write_text(icerik, encoding="utf-8")
        uretilen.append(yol)
        print(f"  {dosya_adi}")

    # Sır sızıntısı denetimi: teslim belgeleri e-postayla dolaşır
    import re
    supheli = []
    for yol in uretilen:
        icerik = yol.read_text(encoding="utf-8")
        if re.search(r"(?i)(parola|password|sifre)\s*[:=]\s*\S{6,}", icerik):
            supheli.append(yol.name)

    print()
    if supheli:
        print("DİKKAT: Şu belgelerde parola görünümlü içerik var:")
        for ad in supheli:
            print(f"  {ad}")
        print("Teslim belgeleri e-postayla dolaşır; parola içermemeli.")
        return 1

    print(f"{len(uretilen)} belge üretildi: {hedef}")
    print()
    print("Erişim belgesi parola İÇERMEZ; bilgiler ayrı kanaldan iletilir.")
    return 0


def komut_kontrol(args):
    kok = Path(yollar.proje_kok())
    tanim = proje.oku(kok)

    print("TESLİME HAZIR MI")
    print("=" * 62)
    print()

    sorunlar = []

    # Tanım
    if tanim is None:
        print("  [KALDI ] Proje tanımı")
        print("           Tanım olmadan kılavuz ve teknik belge üretilemez.")
        sorunlar.append("tanim")
    else:
        eksik = [a for a in ("gorev", "musteri") if not tanim.get(a)]
        if eksik:
            print("  [KALDI ] Proje tanımı")
            print(f"           Eksik alan: {', '.join(eksik)}")
            sorunlar.append("tanim")
        else:
            print("  [GECTI ] Proje tanımı")

    # Acil görevler
    try:
        sys.path.insert(0, str(SCRIPT_DIZINI))
        import gorev
        acil = [g for g in gorev.suzgecle(acik_olanlar=True)
                if g.get("oncelik") == "acil"
                and g.get("proje") == yollar.proje_adi(kok)]
        if acil:
            print("  [KALDI ] Açık acil görev")
            for g in acil[:3]:
                print(f"           #{g['no']} {g['baslik']}")
            sorunlar.append("gorev")
        else:
            print("  [GECTI ] Açık acil görev yok")
    except ImportError:
        print("  [ATLANDI] Görev kontrolü yapılamadı")

    print()
    if sorunlar:
        print(f"{len(sorunlar)} konu teslimden önce çözülmeli.")
        return 1

    print("Teslim paketi hazırlanabilir:")
    print("  python teslim.py hazirla")
    return 0


def komut_liste(args):
    print("TESLİM PAKETİ İÇERİĞİ")
    print("=" * 62)
    print()

    aciklamalar = {
        "kilavuz": "Kullanım kılavuzu - müşteri ne yapacağını bilsin",
        "teknik": "Teknik belge - başka biri devralabilsin",
        "erisim": "Erişim bilgileri - NEREDE olduğu, kendisi değil",
        "tutanak": "Teslim tutanağı - imzalanacak belge",
        "kvkk": "Kişisel veri kontrol listesi",
    }

    for anahtar, (dosya_adi, _) in BELGELER.items():
        print(f"  {anahtar:<10} {dosya_adi}")
        print(f"             {aciklamalar[anahtar]}")
        print()

    print(f"Kişisel veri listesinde {len(KVKK_MADDELERI)} madde var.")
    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Müşteri teslim paketi")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("hazirla", help="Teslim paketini üret")
    p.add_argument("--hedef")
    p.add_argument("--belge", action="append", choices=list(BELGELER))
    p.set_defaults(islev=komut_hazirla)

    p = alt.add_parser("kontrol", help="Teslime hazır mı")
    p.set_defaults(islev=komut_kontrol)

    p = alt.add_parser("liste", help="Pakette neler var")
    p.set_defaults(islev=komut_liste)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
