#!/usr/bin/env python3
"""Sağlık kontrolü - framework gerçekten çalışıyor mu?

Bu betiğin varlık sebebi somut bir olaydır: korumalar aylarca yazılıydı ama
ayar dosyasına kaydedilmedikleri için **hiçbiri çalışmıyordu**. Kimse fark
etmedi, çünkü kimse bakmadı.

Artık bakılıyor. Kontroller:

    kancalar    Korumalar kayıtlı mı VE gerçekten tepki veriyor mu
    betikler    Betikler çalışabiliyor mu
    hafıza      Hafıza yazılabiliyor, okunabiliyor mu
    kasa        Kasa kurulu mu, kilitli mi
    çakışma     İki şey aynı işi mi yapıyor
    dil         Dil dosyaları eksiksiz mi
    düzen       Klasör düzeni bozulmuş mu

"Kayıtlı" ile "çalışıyor" farklı şeylerdir. Bu betik ikisini de ölçer:
her korumaya gerçek bir girdi verilir ve beklenen kararı verip vermediğine
bakılır.

Komutlar:
    bak        Bütün kontrolleri çalıştır
    kancalar   Yalnız koruma kontrolü
    çakışma    Yalnız çakışma denetimi
    istatistik Ne kullanılıyor, ne kullanılmıyor

Geliştirici: Enver KOCAK
"""

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
BETIK_KOKU = SCRIPT_DIZINI.parent
sys.path.insert(0, str(BETIK_KOKU / "ortak"))
sys.path.insert(0, str(BETIK_KOKU / "hafiza"))

import hafiza  # noqa: E402
import yollar  # noqa: E402

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

IYI = "iyi"
UYARI = "uyari"
BOZUK = "bozuk"

ISARETLER = {IYI: "[ iyi  ]", UYARI: "[uyari ]", BOZUK: "[BOZUK ]"}

# Her koruma için: (dosya, araç, girdi, beklenen karar)
# Beklenen karar gerçekleşmezse koruma yazılıydı ama ÇALIŞMIYOR demektir.
KORUMA_OLCUMLERI = [
    ("veri-koruma.py", "Bash", {"command": "rm -rf ornek-klasor"}, "deny",
     "Silme engellenmiyor"),
    ("veri-koruma.py", "Bash", {"command": "git reset --hard"}, "ask",
     "Yikici komutta onay istenmiyor"),
    ("veri-koruma.py", "Bash", {"command": "git status"}, None,
     "Zararsiz komut engelleniyor"),
    ("kasa-koruma.py", "Read", {"file_path": "kasa/kasa.kilit"}, "deny",
     "Kasa dosyasi okunabiliyor"),
    ("git-gizlilik-koruma.py", "Bash", {"command": "gh repo create x --pub" + "lic"},
     "deny", "Herkese acik depo engellenmiyor"),
    # Sunucu adresi HARITADAN alınır; koda gömülmez.
    # Bu betik paylaşılan kopyada da bulunacağı için kişisel değer taşıyamaz.
    ("sunucu-koruma.py", "Bash", "SUNUCU_OLCUMU", "deny",
     "Baska musteri dizini engellenmiyor"),
]

# Aynı işi yapabilecek dosya adları - çakışma belirtisi
CAKISMA_ESIKLERI = 0.9


def _kanca_dizini():
    return Path(yollar.proje_kok()) / "hooks"


def _ayar_yolu():
    return Path(yollar.proje_kok()) / ".claude" / "settings.json"


def _sunucu_olcumu():
    """Sunucu korumasını sınamak için haritadan bir adres al."""
    try:
        sys.path.insert(0, str(BETIK_KOKU / "ortak"))
        import sunucu_harita
        adresler = sunucu_harita.adresler()
        kokler = sunucu_harita.korunan_kokler()
    except Exception:
        return None

    if not adresler or not kokler:
        return None

    return {"command": f"ssh root@{adresler[0]} ls {kokler[0]}baska-site.example/"}


def _kanca_sor(dosya, arac, girdiler):
    yol = _kanca_dizini() / dosya
    if not yol.is_file():
        return "dosya-yok", ""

    veri = json.dumps({"tool_name": arac, "tool_input": girdiler})

    try:
        sonuc = subprocess.run(
            [sys.executable, str(yol)], input=veri,
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as hata:
        return "calismadi", str(hata)

    try:
        cikti = json.loads(sonuc.stdout or "{}")
    except json.JSONDecodeError:
        return "bozuk-cikti", (sonuc.stdout or "")[:120]

    return cikti.get("hookSpecificOutput", {}).get("permissionDecision"), ""


# ---------------------------------------------------------------- kontroller

def kancalari_kontrol():
    bulgular = []

    # 1. Ayar dosyasında kayıtlı mı
    ayar = _ayar_yolu()
    if not ayar.is_file():
        bulgular.append((BOZUK, "Ayar dosyası yok",
                         "Korumalar kayıtlı değil; hiçbiri çalışmıyor olabilir. "
                         "Kaydetmek için: scripts/kurulum/kanca-kaydet.py"))
        return bulgular

    try:
        veri = json.loads(ayar.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        bulgular.append((BOZUK, "Ayar dosyası okunamıyor", str(ayar)))
        return bulgular

    kayitli = json.dumps(veri)
    beklenen_kancalar = {dosya for dosya, *_ in KORUMA_OLCUMLERI}

    for dosya in sorted(beklenen_kancalar):
        if dosya not in kayitli:
            bulgular.append((BOZUK, f"{dosya} ayar dosyasında KAYITLI DEĞİL",
                             "Yazılmış ama devrede değil - en tehlikeli durum."))

    # 2. Gerçekten tepki veriyor mu
    for dosya, arac, girdiler, beklenen, hata_mesaji in KORUMA_OLCUMLERI:
        if girdiler == "SUNUCU_OLCUMU":
            girdiler = _sunucu_olcumu()
            if girdiler is None:
                bulgular.append((UYARI, "Sunucu korumasi olculemedi",
                                 "Haritada sunucu tanimli degil."))
                continue

        karar, ayrinti = _kanca_sor(dosya, arac, girdiler)

        if karar in ("dosya-yok", "calismadi", "bozuk-cikti"):
            bulgular.append((BOZUK, f"{dosya} çalışmıyor ({karar})", ayrinti))
            continue

        if karar != beklenen:
            bulgular.append((BOZUK, f"{dosya}: {hata_mesaji}",
                             f"beklenen: {beklenen or 'karar yok'}, "
                             f"gelen: {karar or 'karar yok'}"))

    if not bulgular:
        bulgular.append((IYI, f"{len(KORUMA_OLCUMLERI)} koruma ölçümü geçti",
                         "Korumalar hem kayıtlı hem çalışıyor."))

    return bulgular


def betikleri_kontrol():
    bulgular = []
    bozuk = []

    for yol in sorted(BETIK_KOKU.rglob("*.py")):
        if "__pycache__" in yol.as_posix():
            continue
        try:
            import ast
            ast.parse(yol.read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, OSError) as hata:
            bozuk.append((yol.relative_to(BETIK_KOKU).as_posix(), str(hata)[:60]))

    if bozuk:
        for ad, hata in bozuk[:8]:
            bulgular.append((BOZUK, f"Betik bozuk: {ad}", hata))
    else:
        sayi = sum(1 for y in BETIK_KOKU.rglob("*.py")
                   if "__pycache__" not in y.as_posix())
        bulgular.append((IYI, f"{sayi} betiğin sözdizimi geçerli", ""))

    return bulgular


def hafizayi_kontrol():
    bulgular = []
    kok = yollar.proje_kok()

    try:
        deneme = hafiza.hafiza_dizini(kok) / ".saglik-denemesi"
        deneme.write_text("deneme", encoding="utf-8")
        okunan = deneme.read_text(encoding="utf-8")
        deneme.unlink()
        if okunan != "deneme":
            raise OSError("okunan içerik farklı")
        bulgular.append((IYI, "Hafıza yazılabiliyor ve okunabiliyor", ""))
    except OSError as hata:
        bulgular.append((BOZUK, "Hafızaya yazılamıyor", str(hata)))

    # Önemli hafıza dosyaları
    beklenenler = [
        ("durum.md", "Nerede kaldık kaydı"),
        ("makineler.json", "Makine kayıtları"),
        ("faz-plani.json", "Faz planı"),
    ]
    for dosya, aciklama in beklenenler:
        yol = hafiza.hafiza_dosyasi(dosya, kok)
        if not yol.is_file():
            bulgular.append((UYARI, f"{dosya} yok", aciklama))

    # Günlük depoya girmemeli
    import subprocess as alt_surec
    for yol, girmemeli in ((".", False),):
        pass

    sonuc = alt_surec.run(["git", "check-ignore", "-q", "gunluk"],
                          cwd=str(kok), capture_output=True)
    if sonuc.returncode != 0:
        bulgular.append((BOZUK, "Ham günlük depoya giriyor",
                         "gunluk/ makineye özeldir, depoya girmemeli."))

    sonuc = alt_surec.run(["git", "check-ignore", "-q", "hafiza"],
                          cwd=str(kok), capture_output=True)
    if sonuc.returncode == 0:
        bulgular.append((BOZUK, "Hafıza depoya GİRMİYOR",
                         "hafiza/ senkron olmalı; girmezse makineler ayrışır."))

    return bulgular


def kasayi_kontrol():
    bulgular = []
    kok = Path(yollar.proje_kok())

    kasa_dosyasi = kok / "kasa" / "kasa.kilit"
    duz_kasa = kok / "vault"

    if not kasa_dosyasi.is_file():
        bulgular.append((UYARI, "Kasa kurulu değil",
                         "Şifreler koruma altında değil. Kurmak için: kasa.py kur"))
    else:
        ham = kasa_dosyasi.read_text(encoding="utf-8", errors="ignore")
        if not ham.startswith("ENVER-KASA"):
            bulgular.append((BOZUK, "Kasa dosyası tanınmıyor", ""))
        else:
            bulgular.append((IYI, "Kasa kurulu ve biçimi doğru", ""))

    if duz_kasa.is_dir() and any(duz_kasa.glob("*.md")):
        bulgular.append((UYARI, "Düz metin kasa klasörü duruyor",
                         "vault/ içeriği kasaya alınıp arşivlenmeli."))

    import subprocess as alt_surec
    for hedef in ("kasa", "vault"):
        sonuc = alt_surec.run(["git", "check-ignore", "-q", hedef],
                              cwd=str(kok), capture_output=True)
        if sonuc.returncode != 0 and (kok / hedef).exists():
            bulgular.append((BOZUK, f"{hedef}/ depoya giriyor",
                             "Sır sızıntısı riski."))

    return bulgular


def cakismayi_kontrol():
    """İki şey aynı işi mi yapıyor?"""
    bulgular = []
    kok = Path(yollar.proje_kok())

    # 1. Aynı adlı komut dosyaları
    komut_dizini = kok / "plugins" / "enver-framework" / "commands"
    if komut_dizini.is_dir():
        adlar = Counter(y.stem.lower() for y in komut_dizini.glob("*.md"))
        for ad, sayi in adlar.items():
            if sayi > 1:
                bulgular.append((BOZUK, f"'{ad}' komutu {sayi} kez tanımlı", ""))

    # 2. Büyük/küçük harf çakışması (Windows'ta veri kaybına yol açar)
    for dizin in (kok, komut_dizini):
        if not dizin.is_dir():
            continue
        adlar = Counter(y.name.lower() for y in dizin.iterdir() if y.is_file())
        for ad, sayi in adlar.items():
            if sayi > 1:
                bulgular.append((BOZUK,
                                 f"Harf farkıyla çakışan dosya: {ad}",
                                 f"{dizin.name}/ içinde. Windows'ta veri kaybına yol açar."))

    # 3. Aynı açıklamaya sahip komutlar
    if komut_dizini.is_dir():
        aciklamalar = {}
        for yol in komut_dizini.glob("*.md"):
            icerik = yol.read_text(encoding="utf-8", errors="ignore")
            import re
            eslesme = re.search(r"^description:\s*(.+)$", icerik, re.MULTILINE)
            if eslesme:
                aciklama = eslesme.group(1).strip()[:60]
                aciklamalar.setdefault(aciklama, []).append(yol.stem)

        for aciklama, komutlar in aciklamalar.items():
            if len(komutlar) > 1:
                bulgular.append((UYARI,
                                 f"Aynı açıklamayı taşıyan komutlar: {', '.join(komutlar)}",
                                 "Biri gereksiz olabilir."))

    if not bulgular:
        bulgular.append((IYI, "Çakışma bulunamadı", ""))

    return bulgular


def dili_kontrol():
    bulgular = []
    diller_dizini = BETIK_KOKU.parent / "diller"

    if not diller_dizini.is_dir():
        bulgular.append((BOZUK, "Dil klasörü yok", ""))
        return bulgular

    dosyalar = sorted(diller_dizini.glob("*.json"))
    if not dosyalar:
        bulgular.append((BOZUK, "Dil dosyası yok", ""))
        return bulgular

    def anahtarlar(sozluk, on=""):
        toplam = set()
        for anahtar, deger in sozluk.items():
            tam = f"{on}.{anahtar}" if on else anahtar
            toplam.add(tam)
            if isinstance(deger, dict):
                toplam |= anahtarlar(deger, tam)
        return toplam

    temel = None
    temel_anahtarlar = set()

    for yol in dosyalar:
        try:
            veri = json.loads(yol.read_text(encoding="utf-8"))
        except json.JSONDecodeError as hata:
            bulgular.append((BOZUK, f"{yol.name} bozuk", str(hata)[:60]))
            continue

        if temel is None:
            temel = yol.stem
            temel_anahtarlar = anahtarlar(veri)
            continue

        kendi = anahtarlar(veri)
        eksik = temel_anahtarlar - kendi
        fazla = kendi - temel_anahtarlar

        if eksik:
            bulgular.append((BOZUK, f"{yol.name} eksik anahtar taşıyor ({len(eksik)})",
                             ", ".join(sorted(eksik)[:5])))
        if fazla:
            bulgular.append((UYARI, f"{yol.name} fazladan anahtar taşıyor ({len(fazla)})",
                             ", ".join(sorted(fazla)[:5])))

    if not any(d[0] == BOZUK for d in bulgular):
        bulgular.append((IYI, f"{len(dosyalar)} dil dosyası tutarlı",
                         ", ".join(y.stem for y in dosyalar)))

    return bulgular


def duzeni_kontrol():
    bulgular = []
    kok = Path(yollar.proje_kok())

    duzen_yolu = BETIK_KOKU.parent / "references" / "dizin-duzeni.json"
    if not duzen_yolu.is_file():
        bulgular.append((UYARI, "Dizin düzeni tanımı yok", ""))
        return bulgular

    try:
        duzen = json.loads(duzen_yolu.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        bulgular.append((BOZUK, "Dizin düzeni tanımı bozuk", ""))
        return bulgular

    beklenen = set(duzen.get("kalici", {})) | set(duzen.get("uretilen", {}))
    fazla = [y.name for y in kok.iterdir() if y.name not in beklenen]

    if fazla:
        bulgular.append((UYARI, f"Ana dizinde beklenmeyen {len(fazla)} öğe",
                         ", ".join(fazla[:6])))
    else:
        bulgular.append((IYI, "Ana dizin düzeni tanıma uygun", ""))

    return bulgular


KONTROLLER = [
    ("kancalar", "Korumalar", kancalari_kontrol),
    ("betikler", "Betikler", betikleri_kontrol),
    ("hafiza", "Hafıza", hafizayi_kontrol),
    ("kasa", "Kasa", kasayi_kontrol),
    ("cakisma", "Çakışma", cakismayi_kontrol),
    ("dil", "Dil dosyaları", dili_kontrol),
    ("duzen", "Klasör düzeni", duzeni_kontrol),
]


# ---------------------------------------------------------------- komutlar

def _yazdir(bulgular):
    for durum, baslik, ayrinti in bulgular:
        print(f"    {ISARETLER[durum]} {baslik}")
        if ayrinti:
            print(f"             {ayrinti}")


def komut_bak(args):
    print("SAĞLIK KONTROLÜ")
    print("=" * 70)

    secilenler = args.kontrol or [k for k, _, _ in KONTROLLER]
    sayilar = Counter()

    for anahtar, baslik, islev in KONTROLLER:
        if anahtar not in secilenler:
            continue

        print()
        print(f"  {baslik}")
        print("  " + "-" * 66)

        try:
            bulgular = islev()
        except Exception as hata:
            bulgular = [(BOZUK, f"Kontrol çalıştırılamadı: {hata}", "")]

        _yazdir(bulgular)
        for durum, _, _ in bulgular:
            sayilar[durum] += 1

    print()
    print("=" * 70)
    print(f"{sayilar[IYI]} iyi · {sayilar[UYARI]} uyarı · {sayilar[BOZUK]} bozuk")

    if sayilar[BOZUK]:
        print()
        print("BOZUK bulgular framework'ün bir parçasının ÇALIŞMADIĞINI gösterir.")
        print("Yazılmış ama devrede olmayan bir koruma, hiç olmayan korumadan tehlikelidir:")
        print("var sanılır, güvenilir, ama korumaz.")
        return 1

    if sayilar[UYARI]:
        return 0

    print()
    print("Framework sağlıklı.")
    return 0


def komut_kancalar(args):
    print("KORUMA KONTROLÜ")
    print("=" * 70)
    print()
    bulgular = kancalari_kontrol()
    _yazdir(bulgular)
    return 1 if any(d[0] == BOZUK for d in bulgular) else 0


def komut_cakisma(args):
    print("ÇAKIŞMA DENETİMİ")
    print("=" * 70)
    print()
    bulgular = cakismayi_kontrol()
    _yazdir(bulgular)
    return 1 if any(d[0] == BOZUK for d in bulgular) else 0


def komut_istatistik(args):
    """Ne var, ne kullanılıyor?"""
    kok = Path(yollar.proje_kok())
    eklenti = kok / "plugins" / "enver-framework"

    sayilar = {
        "komut": len(list((eklenti / "commands").glob("*.md")))
        if (eklenti / "commands").is_dir() else 0,
        "beceri": len([y for y in (eklenti / "skills").iterdir()
                       if (y / "SKILL.md").is_file()])
        if (eklenti / "skills").is_dir() else 0,
        "ajan": len(list((eklenti / "agents").glob("*.md")))
        if (eklenti / "agents").is_dir() else 0,
        "koruma": len([y for y in (kok / "hooks").glob("*.py")
                       if not y.name.startswith("_")])
        if (kok / "hooks").is_dir() else 0,
        "betik": len([y for y in (eklenti / "scripts").rglob("*.py")
                      if "__pycache__" not in y.as_posix()]),
        "test": len(list((eklenti / "scripts" / "testler").glob("*")))
        if (eklenti / "scripts" / "testler").is_dir() else 0,
    }

    print("FRAMEWORK İSTATİSTİĞİ")
    print("=" * 50)
    for ad, sayi in sayilar.items():
        print(f"  {ad:<12} {sayi:>4}")

    # Hafızadan kullanım izleri
    gunluk = hafiza.gunluk_dizini(kok, olustur=False) / hafiza.KOMUT_KAYDI
    kayitlar = hafiza.satirlari_oku(gunluk)

    if kayitlar:
        araclar = Counter()
        for kayit in kayitlar:
            if kayit.get("tur") == "komut":
                ilk = str(kayit.get("ozet", "")).split()
                if ilk:
                    araclar[ilk[0]] += 1

        print()
        print(f"Kayıtlı oturum olayı: {len(kayitlar)}")
        if araclar:
            print("En çok kullanılan komutlar:")
            for ad, sayi in araclar.most_common(8):
                print(f"  {ad:<16} {sayi}")

    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Sağlık kontrolü")
    alt = ayristirici.add_subparsers(dest="komut", required=True)

    p = alt.add_parser("bak", help="Bütün kontroller")
    p.add_argument("--kontrol", action="append",
                   choices=[k for k, _, _ in KONTROLLER])
    p.set_defaults(islev=komut_bak)

    p = alt.add_parser("kancalar", help="Yalnız koruma kontrolü")
    p.set_defaults(islev=komut_kancalar)

    p = alt.add_parser("cakisma", help="Yalnız çakışma denetimi")
    p.set_defaults(islev=komut_cakisma)

    p = alt.add_parser("istatistik", help="Ne var, ne kullanılıyor")
    p.set_defaults(islev=komut_istatistik)

    args = ayristirici.parse_args()
    return args.islev(args)


if __name__ == "__main__":
    sys.exit(main())
