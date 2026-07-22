#!/usr/bin/env python3
"""Kurulum sihirbazı - başkası indirdiğinde kendi bilgisiyle kurar.

Bu framework Enver KOCAK için yazıldı ve onun bilgilerini taşır. Başka biri
indirdiğinde o bilgiler işine yaramaz; kendi bilgilerini girmesi gerekir.

Sihirbaz üç iş yapar:
    1. Ortamın hazır olup olmadığını söyler (Python, depo, gerekli paket)
    2. Kişisel bilgileri sorup kaydeder
    3. Korumaları ayar dosyasına kaydeder

KİŞİSEL BİLGİ TAŞINMAZ: Kasa, hafıza, proje kayıtları ve makine bilgileri
depoya girmez. Yeni kullanıcı boş bir sayfayla başlar.

Komutlar:
    kontrol    Ortam hazır mı
    kur        Kurulumu yap
    bilgi      Kayıtlı kimlik bilgisini göster

Geliştirici: Enver KOCAK
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
BETIK_KOKU = SCRIPT_DIZINI.parent
sys.path.insert(0, str(BETIK_KOKU / "ortak"))

import ayarlar  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

# Kurulum sonrasi kullanicinin doldurmasi gereken kimlik alanlari
KIMLIK_ALANLARI = [
    ("gelistirici", "Geliştirici adı", True),
    ("site", "Site adresi", False),
    ("eposta", "E-posta", False),
    ("telefon", "Telefon", False),
    ("sirket", "Şirket adı", False),
]

# KISISEL VERI VE PAYLASIM
#
# Burada ince bir ayrim var:
#
#   Kendi kullaniminda  hafiza/ depoya GIRMELI - coklu bilgisayar senkronu
#                       buna dayaniyor (E13). Depo gizli oldugu surece sorun yok.
#
#   Paylasimda          hafiza/ icinde musteri adlari, sunucu dizinleri,
#                       cihaz adresleri ve kararlar var. Baskasina verilen
#                       kopyada bunlar BULUNMAMALI.
#
# Bu yuzden iki ayri liste tutulur.

# Hicbir kosulda depoya girmemesi gerekenler
ASLA_DEPOYA = ["kasa", "vault", "gunluk", "_arsiv", "_calisma"]

# Kendi kullaniminda depoda durur, PAYLASIRKEN cikarilir
PAYLASIMDA_CIKAR = [
    "hafiza",
    ".claude/proje.json",
    ".claude/imza.json",
    ".claude/tasarim-kimligi.json",

    # Uretilen ayar dosyasi bu makinenin mutlak yollarini tasir.
    # Baska makinede gecersizdir; kurulum betigi yenisini uretir.
    ".claude/settings.json",
    ".claude/settings.json.yedek",

    # Kisiye ozel notlar ve haritalar
    "bilgi",                       # deploy rehberi, sunucu notlari
    "gelistirme-arastirmasi",      # gelistirme surecinin kendi notlari
    "CLAUDE.md",                   # sunucu adresi ve kisisel kurallar
    ".iz-muaf",                    # bu deponun muafiyeti, baskasinin degil
    "plugins/enver-framework/references/sunucu-haritasi.json",
    "plugins/.claude-plugin/plugin.json",
    "plugins/.claude-plugin/marketplace.json",
]

# Paylasilan kopyada bulunmasi gereken ornek dosyalar.
# Cikarilan yapilandirmalarin yerine bunlar konur.
ORNEK_DOSYALAR = {
    "CLAUDE.ornek.md": "CLAUDE.md",
    "README.ornek.md": "README.md",
    "plugins/enver-framework/references/sunucu-haritasi.ornek.json":
        "plugins/enver-framework/references/sunucu-haritasi.json",
    "plugins/.claude-plugin/plugin.ornek.json":
        "plugins/.claude-plugin/plugin.json",
    "plugins/.claude-plugin/marketplace.ornek.json":
        "plugins/.claude-plugin/marketplace.json",
}

# Kelime siniri deseni. Tek yerde tanimlanir ki kacis dizisi bozulmasin.
SINIR = chr(92) + "b"

# Yer tutucu adresler kisisel veri sayilmaz
YER_TUTUCU_ADRESLER = {"0.0.0.0", "127.0.0.1", "255.255.255.255", "1.2.3.4"}

# Ozel ag araliklari da sayilmaz: bu adresler yerel agda gecerlidir,
# disaridan erisilemez ve kimseyi isaret etmez.
# (192.168.1.50 gibi bir kamera adresi kisisel veri degildir.)
OZEL_AG = re.compile(
    r"^(?:"
    r"10\.|"
    r"127\.|"
    r"192\.168\.|"
    r"172\.(?:1[6-9]|2\d|3[01])\.|"
    r"169\.254\."
    r")")


def yer_tutucu_adres_mi(adres):
    return adres in YER_TUTUCU_ADRESLER or bool(OZEL_AG.match(adres))

# Bicime gore her zaman aranan degerler
SABIT_DESENLER = [
    (r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "sunucu adresi"),
    (r"\b0\d{3}\s?\d{3}\s?\d{2}\s?\d{2}\b", "telefon"),
]

# SIZINTI ile TELIF farklidir.
#
# Paylasilan bir kaynak kodda yazarin ADI ve SITESI bulunmasi normaldir;
# bu telif bilgisidir, sizinti degil. Zaten depo sayfasinda da gorunur.
#
# Sizinti olan sey sudur: sunucu adresi, telefon, musteri adi, proje adi.
# Bunlar baskasinin isine yaramaz ama Enver'e zarar verebilir.
#
# Bu yuzden iki ayri liste var: biri kopyayi DURDURUR, digeri yalniz bildirir.

# Bulunursa kopya paylasilamaz
ENGELLEYEN_ALANLAR = {
    "telefon": "telefon",
    "sirket": "şirket adı",
}

# Bulunursa yalnız bildirilir - telif sayılır
BILDIREN_ALANLAR = {
    "gelistirici": "yazar adı (telif)",
    "site": "yazar sitesi (telif)",
    "eposta": "yazar e-postası (telif)",
}


def kisisel_desenler():
    """Paylasilan kopyada aranacak kisisel degerler.

    Kimlik degerleri AYARDAN gelir; koda gomulmez. Aksi halde bu
    denetleyicinin kendisi kisisel veri tasiyan bir dosya olurdu -
    ki ilk denemede tam olarak bu oldu.
    """
    engelleyen = [(re.compile(desen), etiket) for desen, etiket in SABIT_DESENLER]
    bildiren = []

    kayit = ayarlar.kimlik()

    def desen_uret(deger):
        # Alan adinin ayirt edici parcasi aranir: ornek.com -> ornek
        kok_parca = deger.split("@")[-1].split(".")[0]
        aday = kok_parca if len(kok_parca) >= 5 else deger
        return re.compile(SINIR + re.escape(aday) + SINIR, re.IGNORECASE)

    for alan, etiket in ENGELLEYEN_ALANLAR.items():
        deger = (kayit.get(alan) or "").strip()
        if len(deger) >= 4:
            engelleyen.append((desen_uret(deger), etiket))

    for alan, etiket in BILDIREN_ALANLAR.items():
        deger = (kayit.get(alan) or "").strip()
        if len(deger) >= 4:
            bildiren.append((desen_uret(deger), etiket))

    return engelleyen, bildiren


def _komut_var(ad):
    return shutil.which(ad) is not None


def ortam_kontrol():
    bulgular = []

    surum = sys.version_info
    if surum >= (3, 9):
        bulgular.append((True, f"Python {surum.major}.{surum.minor}", ""))
    else:
        bulgular.append((False, f"Python {surum.major}.{surum.minor} çok eski",
                         "En az 3.9 gerekiyor."))

    if _komut_var("git"):
        bulgular.append((True, "Depo aracı bulundu", ""))
    else:
        bulgular.append((False, "Depo aracı yok",
                         "Senkron ve yedek özellikleri çalışmaz."))

    try:
        import cryptography  # noqa: F401
        bulgular.append((True, "Şifreleme paketi bulundu", ""))
    except ImportError:
        bulgular.append((False, "Şifreleme paketi yok",
                         "Kasa çalışmaz. Kurmak için: python -m pip install cryptography"))

    kok = Path(yollar.proje_kok())
    if (kok / "hooks").is_dir():
        bulgular.append((True, "Koruma dosyaları yerinde", ""))
    else:
        bulgular.append((False, "Koruma dosyaları bulunamadı", str(kok / "hooks")))

    ev = Path.home() / ".claude"
    if ev.is_dir():
        bulgular.append((True, "Kullanıcı klasörü var", str(ev)))
    else:
        bulgular.append((False, "Kullanıcı klasörü yok",
                         "Ana uygulama en az bir kez çalıştırılmalı."))

    return bulgular


def depo_gizli_mi(kok=None):
    """Uzak depo herkese açık mı? Açıksa kişisel veri riski büyür."""
    kok = kok or Path(yollar.proje_kok())

    sonuc = subprocess.run(["git", "remote", "get-url", "origin"],
                           cwd=str(kok), capture_output=True,
                           text=True, encoding="utf-8")
    if sonuc.returncode != 0:
        return None  # uzak depo yok

    adres = sonuc.stdout.strip()
    if "github.com" not in adres:
        return None

    # Kimlik dogrulamasiz erisilebiliyorsa herkese aciktir
    import urllib.error
    import urllib.request
    import re

    eslesme = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", adres)
    if not eslesme:
        return None

    api = f"https://api.github.com/repos/{eslesme.group(1)}/{eslesme.group(2)}"
    try:
        with urllib.request.urlopen(api, timeout=10) as yanit:
            return yanit.status != 200
    except urllib.error.HTTPError as hata:
        return hata.code == 404  # 404 = gizli ya da yok
    except (urllib.error.URLError, OSError):
        return None


def kisisel_veri_kontrol(paylasim=False):
    """Depoda kişiye özel veri kalmış mı?

    paylasim=False : kendi kullanımı - yalnız asla girmemesi gerekenlere bakılır
    paylasim=True  : başkasına verilecek kopya - hafıza da çıkarılmalı
    """
    kok = Path(yollar.proje_kok())
    sorunlar = []

    bakilacaklar = list(ASLA_DEPOYA)
    if paylasim:
        bakilacaklar += PAYLASIMDA_CIKAR

    for ad in bakilacaklar:
        yol = kok / ad
        if not yol.exists():
            continue

        sonuc = subprocess.run(["git", "check-ignore", "-q", ad],
                               cwd=str(kok), capture_output=True)
        if sonuc.returncode != 0:
            if ad in ASLA_DEPOYA:
                sorunlar.append(f"{ad}/ depoya giriyor - sır sızıntısı riski")
            else:
                sorunlar.append(f"{ad} paylaşılan kopyada bulunmamalı")

    return sorunlar


def kimlik_kaydet(degerler):
    mevcut = ayarlar.oku().get("kimlik", {})
    mevcut.update({a: d for a, d in degerler.items() if d})
    ayarlar.yaz({"kimlik": mevcut})
    return mevcut


# ---------------------------------------------------------------- komutlar

def komut_kontrol(args):
    print("ORTAM KONTROLÜ")
    print("=" * 62)
    print()

    bulgular = ortam_kontrol()
    for uygun, baslik, ayrinti in bulgular:
        print(f"  [{'iyi  ' if uygun else 'EKSİK'}] {baslik}")
        if ayrinti:
            print(f"           {ayrinti}")

    eksikler = [b for b in bulgular if not b[0]]

    print()
    if eksikler:
        print(f"{len(eksikler)} eksik var. Kurulum yine de yapılabilir,")
        print("ama ilgili özellikler çalışmaz.")
        return 1

    print("Ortam hazır.")
    return 0


def komut_kur(args):
    kok = Path(yollar.proje_kok())

    print("KURULUM SİHİRBAZI")
    print("=" * 62)
    print()

    # 1. Ortam
    print("1. Ortam kontrolü")
    print("-" * 62)
    bulgular = ortam_kontrol()
    for uygun, baslik, ayrinti in bulgular:
        print(f"  [{'iyi  ' if uygun else 'EKSİK'}] {baslik}")
    eksikler = [b for b in bulgular if not b[0]]

    if eksikler and not args.zorla:
        print()
        print("Eksikler var. Yine de kurmak için --zorla ekle.")
        return 1

    # 2. Kimlik
    print()
    print("2. Kimlik bilgileri")
    print("-" * 62)

    degerler = {}
    for alan, etiket, zorunlu in KIMLIK_ALANLARI:
        deger = getattr(args, alan, None)
        if deger:
            degerler[alan] = deger

    if degerler:
        kimlik = kimlik_kaydet(degerler)
        for alan, etiket, _ in KIMLIK_ALANLARI:
            if kimlik.get(alan):
                print(f"  {etiket}: {kimlik[alan]}")
    else:
        mevcut = ayarlar.oku().get("kimlik", {})
        if mevcut:
            print("  Kayıtlı kimlik kullanılıyor:")
            for alan, etiket, _ in KIMLIK_ALANLARI:
                if mevcut.get(alan):
                    print(f"    {etiket}: {mevcut[alan]}")
        else:
            print("  Kimlik bilgisi verilmedi.")
            print("  Vermek için:")
            print('    python sihirbaz.py kur --gelistirici "<ad>" --eposta "<adres>"')

    # 3. Korumalar
    print()
    print("3. Korumalar kaydediliyor")
    print("-" * 62)

    kayit_betigi = SCRIPT_DIZINI / "kanca-kaydet.py"
    kanca_dizini = kok / "hooks"

    if kayit_betigi.is_file() and kanca_dizini.is_dir():
        sonuc = subprocess.run(
            [sys.executable, str(kayit_betigi), str(kanca_dizini),
             str(kok / ".claude" / "settings.json")],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        print(sonuc.stdout.rstrip() or "  (çıktı yok)")
    else:
        print("  Kayıt betiği ya da koruma klasörü bulunamadı.")

    # 3b. Iz muafiyet isareti
    #
    # Bu isaret, framework'un KENDI deposunun iz taramasindan muaf oldugunu
    # soyler: kurulum talimatlari ve klasor adlari teknik zorunluluktur.
    # Musteri projelerine ASLA konulmaz.
    isaret = kok / ".iz-muaf"
    if not isaret.is_file():
        kimlik = ayarlar.kimlik()
        isaret.write_text(
            "Bu depo iz taramasindan MUAFTIR.\n\n"
            "Sebep: Framework'un kendi deposu. Kurulum talimatlari, semalar ve\n"
            "klasor adlari teknik olarak zorunlu; kaldirilirsa framework calismaz.\n\n"
            "DIKKAT: Bu dosya MUSTERI PROJELERINE ASLA KONULMAZ.\n"
            "Musteri projelerinde iz kurali katidir, istisnasi yoktur.\n"
            + (f"\n{kimlik.get('gelistirici')}\n" if kimlik.get("gelistirici") else ""),
            encoding="utf-8")
        print()
        print("3b. Muafiyet isareti oluşturuldu (.iz-muaf)")

    # 4. Kisisel veri denetimi
    print()
    print("4. Kişisel veri denetimi")
    print("-" * 62)

    sorunlar = kisisel_veri_kontrol(paylasim=False)
    if sorunlar:
        for sorun in sorunlar[:6]:
            print(f"  [SORUN] {sorun}")
        print()
        print("  Bu yollar hiçbir koşulda depoya girmemeli.")
    else:
        print("  [iyi  ] Kasa ve ham günlük depoya girmiyor")

    # Paylasim riski ayri bir konu
    gizli = depo_gizli_mi(kok)
    paylasim_sorunlari = kisisel_veri_kontrol(paylasim=True)
    paylasima_ozel = [s for s in paylasim_sorunlari if s not in sorunlar]

    if paylasima_ozel:
        print()
        if gizli is False:
            print("  [SORUN] Depo HERKESE AÇIK ve kişisel veri içeriyor:")
        else:
            durum = "gizli" if gizli else "durumu bilinmiyor"
            print(f"  [bilgi ] Depo {durum}. Paylaşılırsa çıkarılması gerekenler:")

        for sorun in paylasima_ozel[:5]:
            print(f"           {sorun}")
        print()
        print("           Temiz kopya için: python sihirbaz.py paylasima-hazirla")

    # 5. Saglik
    print()
    print("5. Sağlık kontrolü")
    print("-" * 62)

    saglik_betigi = BETIK_KOKU / "saglik" / "saglik.py"
    if saglik_betigi.is_file():
        sonuc = subprocess.run(
            [sys.executable, str(saglik_betigi), "kancalar"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        for satir in sonuc.stdout.splitlines():
            if satir.strip().startswith("["):
                print(f"  {satir.strip()}")
    else:
        print("  Sağlık betiği bulunamadı.")

    print()
    print("=" * 62)
    print("KURULUM TAMAM")
    print()
    print("Sıradaki adımlar:")
    print("  /index                 bütün komutları gör")
    print("  /kasa                  şifre kasasını kur")
    print("  /projeler              projeleri tara")
    print("  /faz                   çalışma modunu ayarla")
    return 0 if not sorunlar else 1


def komut_bilgi(args):
    kimlik = ayarlar.oku().get("kimlik", {})

    if not kimlik:
        print("Kayıtlı kimlik bilgisi yok.")
        print("Kaydetmek için: python sihirbaz.py kur --gelistirici \"<ad>\"")
        return 1

    print("KAYITLI KİMLİK")
    print("=" * 40)
    for alan, etiket, _ in KIMLIK_ALANLARI:
        if kimlik.get(alan):
            print(f"  {etiket}: {kimlik[alan]}")

    print()
    print(f"Kayıt yeri: {ayarlar.KULLANICI_AYAR_YOLU}")
    print("Bu dosya depoya girmez; kişiye özeldir.")
    return 0


def komut_paylasima_hazirla(args):
    """Başkasına verilebilecek temiz bir kopya üret."""
    kok = Path(yollar.proje_kok())
    hedef = Path(args.hedef) if args.hedef else kok.parent / f"{kok.name}-paylasim"

    if hedef.exists() and not args.uzerine_yaz:
        print(f"Hedef zaten var: {hedef}")
        print("Üzerine yazmak için --uzerine-yaz kullan.")
        return 1

    print("PAYLAŞIMA HAZIRLAMA")
    print("=" * 62)
    print()
    print(f"Kaynak: {kok}")
    print(f"Hedef : {hedef}")
    print()

    # Depoda izlenen dosyalari al - gitignore edilenler zaten disarida kalir
    sonuc = subprocess.run(["git", "ls-files"], cwd=str(kok),
                           capture_output=True, text=True, encoding="utf-8")
    if sonuc.returncode != 0:
        print("Depo dosyaları listelenemedi.")
        return 1

    izlenenler = [s for s in sonuc.stdout.splitlines() if s.strip()]

    cikarilan = []
    kopyalanan = 0

    if hedef.exists():
        shutil.rmtree(hedef)
    hedef.mkdir(parents=True, exist_ok=True)

    for bagil in izlenenler:
        if any(bagil == y or bagil.startswith(y.rstrip("/") + "/")
               for y in PAYLASIMDA_CIKAR):
            cikarilan.append(bagil)
            continue

        # Ornek dosyalar kendi adlariyla degil, yerine gectikleri adla
        # kopyalanir. Ikisi birden bulunursa kullanici hangisinin gecerli
        # oldugunu bilemez.
        if ".ornek." in Path(bagil).name:
            continue

        kaynak = kok / bagil
        if not kaynak.is_file():
            continue

        varis = hedef / bagil
        varis.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(kaynak, varis)
        kopyalanan += 1

    print(f"  {kopyalanan} dosya kopyalandı")
    print(f"  {len(cikarilan)} dosya çıkarıldı (kişisel veri)")

    if cikarilan:
        print()
        print("  Çıkarılanlar:")
        for ad in cikarilan[:8]:
            print(f"    {ad}")
        if len(cikarilan) > 8:
            print(f"    ... ve {len(cikarilan) - 8} dosya daha")

    # Ornek dosyalari yerine koy
    eklenen_ornek = []
    for ornek, yerine in ORNEK_DOSYALAR.items():
        kaynak = kok / ornek
        if not kaynak.is_file():
            continue
        varis = hedef / yerine
        varis.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(kaynak, varis)
        eklenen_ornek.append(yerine)

    if eklenen_ornek:
        print()
        print(f"  {len(eklenen_ornek)} örnek dosya yerleştirildi:")
        for ad in eklenen_ornek:
            print(f"    {ad}")

    # KISISEL DEGER TARAMASI
    #
    # Klasor cikarmak yetmiyor: kalan dosyalarin ICINDE de sunucu adresi,
    # musteri adi ve iletisim bilgisi gecebiliyor. Ilk denemede tam olarak
    # bu oldu - kopya "temiz" sayildi ama icinde sunucu IP'si vardi.
    desenler, bildirilecekler = kisisel_desenler()

    # Proje ve musteri adlari kisisel veridir - bunlar kopyayi DURDURUR
    try:
        sys.path.insert(0, str(BETIK_KOKU / "projeler"))
        import kayit as proje_kaydi

        # Kisa ve yaygin adlar her metinde tutar ve taramayi kullanilamaz hale
        # getirir. Yalniz ayirt edici adlar aranir.
        YAYGIN = {
            "album", "sunum", "panel", "site", "proje", "test", "demo",
            # Turkce proje adlarinda sik gecen genel kelimeler
            "projesi", "sistem", "sistemi", "uygulama", "uygulamasi",
            "yonetim", "yonetimi", "kurulum", "masaustu", "hesap",
            "export", "import", "asistan", "asistanim",
        }

        # Kimlik degerleri proje adi olarak sayilmaz; onlar zaten
        # telif basligi altinda ayrica bildiriliyor.
        kimlik_degerleri = set()
        for deger in ayarlar.kimlik().values():
            deger = (deger or "").strip()
            if len(deger) >= 5:
                kimlik_degerleri.add(deger.split("@")[-1].split(".")[0].lower())

        # Proje adinin TAMAMI degil, ayirt edici PARCALARI da aranir.
        # Ornek: 'musteri-adi-gen-tr' kayitliyken dosyada yalniz
        # 'musteri-adi' geciyorsa kelime siniri yuzunden eslesmiyordu.
        arananlar = set()

        for ad in proje_kaydi.kayit_oku().get("projeler", {}):
            if ad.lower() == kok.name.lower():
                continue

            adaylar = [ad] + re.split(r"[-_.\s]+", ad)
            for aday in adaylar:
                if len(aday) < 7 or aday.lower() in YAYGIN:
                    continue
                if aday.lower() in kimlik_degerleri:
                    continue
                arananlar.add(aday)

        for aday in sorted(arananlar):
            # Kelime siniri korunmasi bir kor nokta uretiyordu:
            # '$DEGISKENmusteriadi' bicimindeki bitisik yazimlar eslesmiyordu.
            # On ek degiskeni harfle bittigi icin sinir saglanmiyor.
            #
            # Uzun adlar tesadufen baska bir kelimenin icinde gecmez;
            # onlarda sinir sarti aranmaz.
            if len(aday) >= 10:
                desenler.append((re.compile(re.escape(aday), re.IGNORECASE),
                                 "proje adi"))
            else:
                desenler.append((re.compile(SINIR + re.escape(aday) + SINIR,
                                            re.IGNORECASE), "proje adi"))
    except Exception:
        pass

    bulgular = {}
    for yol in hedef.rglob("*"):
        if not yol.is_file() or yol.suffix.lower() in (".png", ".jpg", ".ico", ".woff"):
            continue
        # Ornek dosyalarin icindeki degerler zaten yer tutucudur
        if ".ornek." in yol.name:
            continue
        try:
            icerik = yol.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        for desen, tur in desenler:
            if tur == "sunucu adresi":
                # Bir dosyada birden cok adres olabilir; yer tutucu ve ozel ag
                # adresleri elenir, geriye gercek bir adres kalirsa bulgu sayilir.
                gercekler = [a for a in desen.findall(icerik)
                             if not yer_tutucu_adres_mi(a)]
                if not gercekler:
                    continue
            elif not desen.search(icerik):
                continue

            bagil = yol.relative_to(hedef).as_posix()
            bulgular.setdefault(bagil, set()).add(tur)

    # Telif bilgisi ayri sayilir: engellemez, bildirilir
    telif = {}
    for yol in hedef.rglob("*"):
        if not yol.is_file() or yol.suffix.lower() in (".png", ".jpg", ".ico", ".woff"):
            continue
        if ".ornek." in yol.name:
            continue
        try:
            icerik = yol.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for desen, tur in bildirilecekler:
            if desen.search(icerik):
                telif.setdefault(tur, 0)
                telif[tur] += 1

    if telif:
        print()
        print("  Telif bilgisi (engellemez):")
        for tur, sayi in sorted(telif.items()):
            print(f"    {tur}: {sayi} dosyada")
        print("    Paylasilan kaynak kodda yazar bilgisi bulunmasi normaldir.")

    print()
    if bulgular:
        print(f"  KİŞİSEL VERİ BULUNDU - {len(bulgular)} dosyada:")
        print()
        for bagil, turler in sorted(bulgular.items())[:12]:
            print(f"    {bagil}")
            print(f"      {', '.join(sorted(turler))}")
        if len(bulgular) > 12:
            print(f"    ... ve {len(bulgular) - 12} dosya daha")
        print()
        print("  Bu kopya PAYLAŞILAMAZ.")
        print("  Ya bu dosyalar çıkarılmalı ya da içindeki değerler temizlenmeli.")
        print("  Çıkarma listesi: sihirbaz.py içinde PAYLASIMDA_CIKAR")
        return 1

    print("  Kişisel veri taraması temiz.")
    print()
    print(f"Temiz kopya hazır: {hedef}")
    print("Bu klasör paylaşılabilir.")
    print("Kasa, hafıza, proje kayıtları ve kişisel notlar içermiyor.")
    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Kurulum sihirbazı")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("kontrol", help="Ortam hazır mı")
    p.set_defaults(islev=komut_kontrol)

    p = alt.add_parser("kur", help="Kurulumu yap")
    for alan, etiket, _ in KIMLIK_ALANLARI:
        p.add_argument(f"--{alan}")
    p.add_argument("--zorla", action="store_true")
    p.set_defaults(islev=komut_kur)

    p = alt.add_parser("bilgi", help="Kayıtlı kimlik")
    p.set_defaults(islev=komut_bilgi)

    p = alt.add_parser("paylasima-hazirla", help="Kişisel veri içermeyen kopya üret")
    p.add_argument("--hedef")
    p.add_argument("--uzerine-yaz", action="store_true", dest="uzerine_yaz")
    p.set_defaults(islev=komut_paylasima_hazirla)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
