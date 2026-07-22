#!/usr/bin/env python3
"""PostToolUse kancasi: Turkce yazim denetimi.

Iki yonlu kural (E17):

  1. KIMLIKLERDE TURKCE KARAKTER YASAK
     Degisken, fonksiyon, sinif ve dosya adlarinda o, c, u, g, i, s
     harflerinin Turkce bicimleri kullanilmaz. Kod her ortamda ayni calismali.

  2. KULLANICI METINLERINDE TURKCE KARAKTER ZORUNLU
     Arayuz yazilari, hata mesajlari ve web icerigi tam Turkce yazilir:
     ö, ç, ü, ğ, ı, ş, İ. "Guncelle" degil "Güncelle".

Bu kanca engellemez, uyarir - duzeltme baglam gerektirir.

Gelistirici: Enver KOCAK
"""

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _ortak_yol as ortak_yol  # noqa: E402

BETIKLER_HAZIR = ortak_yol.hazirla()

if BETIKLER_HAZIR:
    import gerekce
else:
    gerekce = None

TURKCE_HARFLER = "çğıöşüÇĞİÖŞÜ"
TURKCE_DESEN = re.compile(f"[{TURKCE_HARFLER}]")

KOD_UZANTILARI = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".php", ".java", ".cs",
    ".go", ".rb", ".rs", ".c", ".cpp", ".h", ".sh", ".ps1", ".sql",
}

# Icerigin tamami kullaniciya gorunen metin sayilan dosyalar.
# .json bilincli olarak DISARIDA: ayar dosyalarinda yollar, komutlar ve alan
# adlari gecer; bunlar ASCII kalmak zorunda ve metin gibi denetlenirse
# surekli yanlis uyari uretir.
METIN_UZANTILARI = {".md", ".txt", ".html", ".htm", ".vue", ".twig"}

# Ic gelistirme notlari ve uretilmis dosyalar taranmaz.
# gelistirme-arastirmasi/ calisma notudur, kullaniciya sunulan bir yuzey degil -
# iz-kontrol.py de ayni dizini muaf tutuyor.
TARANMAYAN_DIZINLER = (
    "/node_modules/", "/.git/", "/vendor/", "/dist/", "/build/",
    "/_arsiv/", "/_calisma/", "/gelistirme-arastirmasi/",
)

# Dizeleri ve aciklama satirlarini temizleyen desenler
DIZE_VE_ACIKLAMA = [
    re.compile(r'"""[\s\S]*?"""'),
    re.compile(r"'''[\s\S]*?'''"),
    re.compile(r'"(?:\\.|[^"\\])*"'),
    re.compile(r"'(?:\\.|[^'\\])*'"),
    re.compile(r"`(?:\\.|[^`\\])*`"),
    re.compile(r"//[^\n]*"),
    re.compile(r"#[^\n]*"),
    re.compile(r"/\*[\s\S]*?\*/"),
    re.compile(r"<!--[\s\S]*?-->"),
]

# Kullaniciya gorunen metinlerde sik yapilan eksik yazimlar.
# Anahtar: ASCII bicimi, deger: dogru Turkce bicimi.
#
# Listeye yalniz SU IKI KOSULU birden saglayan kelimeler girer:
#   1. Dogru bicimi ASCII bicimden gercekten farkli olacak.
#   2. En az dort harf olacak - "ac", "sec", "sil" gibi kisa kokler
#      Ingilizce kelimelerin icinde geciyor ve yanlis uyari uretiyor.
EKSIK_YAZIMLAR = {
    "guncelle": "güncelle", "gonder": "gönder", "goruntule": "görüntüle",
    "duzenle": "düzenle", "degistir": "değiştir", "olustur": "oluştur",
    "sifre": "şifre", "giris": "giriş", "cikis": "çıkış", "kullanici": "kullanıcı",
    "basarili": "başarılı", "basarisiz": "başarısız", "uyari": "uyarı",
    "yukle": "yükle", "musteri": "müşteri", "urun": "ürün",
    "siparis": "sipariş", "odeme": "ödeme", "guvenlik": "güvenlik",
    "gecmis": "geçmiş", "duzen": "düzen", "ozet": "özet",
    "iletisim": "iletişim", "hakkimizda": "hakkımızda", "sozlesme": "sözleşme",
    "kayit": "kayıt", "aciklama": "açıklama", "baslik": "başlık",
    "goster": "göster", "yukleniyor": "yükleniyor", "lutfen": "lütfen",
    "tesekkur": "teşekkür", "sonuc": "sonuç", "gorev": "görev",
    "olcu": "ölçü", "surum": "sürüm", "bolum": "bölüm",
}

# Turkce ekli bir dil: "sifreniz", "kullanicilar", "guncelleme" de yakalanmali.
# Bu yuzden kokun ardindan gelen ek harfleri desene dahil edilir.
EKSIK_DESENI = re.compile(
    r"\b(" + "|".join(sorted(EKSIK_YAZIMLAR, key=len, reverse=True)) + r")([a-z]*)\b",
    re.IGNORECASE,
)

# UNSUZ YUMUSAMASI
#
# Turkcede c, k, p, t ile biten kelimeler unlu ile baslayan bir ek aldiginda
# yumusar: sonuc -> sonucu, kayit -> kaydi, kitap -> kitabi.
#
# Yani "sonucu" YANLIS DEGIL, dogru yazimin ta kendisi. Kok halinde "sonuc"
# yazilmasi yanlistir ama ekli halinde yumusamis bicim beklenir.
#
# Bu ayrimi yapmayan bir denetim, dogru yazilmis metinleri hatali gosterir.
YUMUSAYAN_SONLAR = ("ç", "k", "p", "t")
UNLULER = "aeıioöuüAEIİOÖUÜ"


def _yumusama_mi(dogru_bicim, ek):
    """Bulunan yazim, unsuz yumusamasi yuzunden mi boyle gorunuyor?"""
    if not ek:
        return False

    if not dogru_bicim.endswith(YUMUSAYAN_SONLAR):
        return False

    return ek[0] in UNLULER


# TURKCE BUYUK HARF
#
# Turkcede i ve i harflerinin buyugu farklidir:
#     i -> I        (noktasiz)
#     i -> I        (noktali)
#
# Yani "uyari" kelimesinin buyuk hali "UYARI"dir; icinde nokta yoktur.
# Ingilizce buyutme kurali uygulanirsa "UYARI" yanlis gorunur, oysa dogrudur.
BUYUTME_ESLEMESI = str.maketrans({
    "ı": "I", "i": "İ", "ç": "Ç", "ğ": "Ğ", "ö": "Ö", "ş": "Ş", "ü": "Ü",
})


def turkce_buyut(metin):
    """Turkce kurallarina gore buyuk harfe cevir."""
    return metin.translate(BUYUTME_ESLEMESI).upper()


def _dogru_buyuk_bicim_mi(bulunan, dogru_bicim):
    """Buyuk harfle yazilmis bicim aslinda dogru mu?"""
    if not bulunan.isupper():
        return False

    return bulunan == turkce_buyut(dogru_bicim)


# Bu kancanin kendi sozlugu, dogasi geregi ASCII bicimleri icerir;
# kendini taramasi anlamsiz uyari uretir.
MUAF_DOSYALAR = {"yazim-kontrol.py"}


def _muaf_mi(dosya_yolu):
    duz = dosya_yolu.replace("\\", "/").lower()

    if Path(duz).name in MUAF_DOSYALAR:
        return True

    return any(parca in duz for parca in TARANMAYAN_DIZINLER)


def _kod_govdesi(icerik):
    """Dize ve aciklamalari cikar - geriye kimlikler kalir."""
    for desen in DIZE_VE_ACIKLAMA:
        icerik = desen.sub(" ", icerik)
    return icerik


# Kod icindeki her dize kullaniciya gosterilmez. Sozluk anahtarlari, dosya
# adlari ve alan adlari da dize olarak yazilir ve ASCII kalmak zorundadir
# (ornek: veri.get("aciklama"), "aciklamalar.json").
#
# Ayirt etme kurali: gosterilen metin ya bosluk icerir ya da buyuk harfle
# baslar. Tek kelimelik, kucuk harfli dizeler anahtar sayilir ve atlanir.
ANAHTAR_GORUNUMLU = re.compile(r"^[a-z0-9_.\-/\\]+$")

# Yol, kabuk komutu ya da degisken iceren dizeler gosterilen metin degildir.
KOMUT_GORUNUMLU = re.compile(
    r"(^|\s)(python|node|npm|git|bash|sh|psql|mysql|ssh|scp|curl|pip)\s"
    r"|\$\{?[A-Z_]{3,}"
    r"|[/\\][a-z0-9_.\-]+[/\\]"
    r"|\.(py|js|ts|php|sh|ps1|json|md|html|css|sql|jsonl)\b"
    # CSS ozel degiskeni ve HTML etiketi: kod, gosterilen metin degil
    r"|--[a-z][a-z0-9-]*\s*:"
    r"|<[a-z]+[\s>/]"
)


# Dize desenleri ham metin uzerinde birbirinden bagimsiz calisir; kod icinde
# gecen tek tirnak ("\"'" gibi) yanlis eslesip kocaman bir kod parcasini dize
# gibi gosterebiliyor. Kod noktalamasi tasiyan parcalar bu yuzden elenir.
KOD_NOKTALAMASI = re.compile(r"[=;{}()\[\]]")

# Duzenli ifade desenleri de dize olarak yazilir ve icinde ASCII kokler gecer
# (ornek: r"pos\b|odeme|payment"). Bunlar kullaniciya gosterilmez.
DESEN_GORUNUMLU = re.compile(r"\\[bdswAZ]|\(\?|\|.*\||\[\^|\{\d")


def _gosterilen_metin_mi(ham_dize):
    """Bu dize kullaniciya gosteriliyor mu, yoksa anahtar ya da kod mu?"""
    icerik = ham_dize.strip("\"'`").strip()

    if not icerik or len(icerik) < 4:
        return False

    # Tek kelimelik kucuk harfli dize: sozluk anahtari ya da alan adi
    if ANAHTAR_GORUNUMLU.match(icerik):
        return False

    # Yol, dosya adi, kabuk komutu ya da ortam degiskeni
    if KOMUT_GORUNUMLU.search(icerik):
        return False

    # Duzenli ifade deseni
    if DESEN_GORUNUMLU.search(icerik):
        return False

    # Cok satirli bir parca ancak kod noktalamasi tasimiyorsa metin sayilir
    if "\n" in icerik and KOD_NOKTALAMASI.search(icerik):
        return False

    return True


def _dizeleri_topla(icerik):
    """Kullaniciya gorunebilecek dize iceriklerini topla."""
    dizeler = []
    for desen in DIZE_VE_ACIKLAMA[:5]:
        for eslesme in desen.finditer(icerik):
            ham = eslesme.group(0)
            if _gosterilen_metin_mi(ham):
                dizeler.append(ham)
    return dizeler


def kimlik_kontrol(dosya_yolu, icerik):
    """Kimliklerde Turkce karakter var mi?"""
    uzanti = Path(dosya_yolu).suffix.lower()
    if uzanti not in KOD_UZANTILARI:
        return []

    govde = _kod_govdesi(icerik)

    bulunanlar = []
    for satir_no, satir in enumerate(govde.splitlines(), 1):
        if TURKCE_DESEN.search(satir):
            temiz = satir.strip()
            if temiz:
                bulunanlar.append((satir_no, temiz[:70]))

    return bulunanlar[:5]


def dosya_adi_kontrol(dosya_yolu):
    """Dosya ve klasor adinda Turkce karakter var mi?"""
    bagil = dosya_yolu.replace("\\", "/")
    parcalar = [p for p in bagil.split("/") if p]

    return [p for p in parcalar if TURKCE_DESEN.search(p)]


# Bir metin dizesinin icinde gorunen her sey kullaniciya gosterilen yazi degil:
#
#   {musteri}          bicimlendirme yer tutucusu - degisken adi, koddur
#   `gorev`            ters tirnak icinde alan adi
#   'kasa_anahtari'    tek tirnak icinde alan adi
#
# Bunlarin hepsi ASCII kalmak zorundadir, denetim disi birakilir.
# Kural: kullanici metninde bir alan adi anilacaksa tirnak icine alinir.
KOD_PARCASI = re.compile(r"\{[^{}]*\}|`[^`]*`|'[^']*'")


# Yardim metinlerinde komut listesi su bicimde yazilir:
#
#     ozet      Butun projelerin gorev ozeti
#     liste     Gorevleri goster
#
# Soldaki komut adi ASCII kalmak zorundadir; sagdaki aciklama denetlenir.
KOMUT_LISTESI_SATIRI = re.compile(r"^(\s{2,})([a-z][a-z0-9_-]*)(\s{2,})", re.MULTILINE)


def _kod_parcalarini_cikar(metin):
    """Yer tutucu, tirnakli ad ve komut adlarini denetim disi birak."""
    metin = KOD_PARCASI.sub(" ", metin)
    return KOMUT_LISTESI_SATIRI.sub(r"\1 \3", metin)


def metin_kontrol(dosya_yolu, icerik):
    """Kullanici metinlerinde eksik Turkce karakter var mi?"""
    uzanti = Path(dosya_yolu).suffix.lower()

    if uzanti in KOD_UZANTILARI:
        adaylar = _dizeleri_topla(icerik)
    elif uzanti in METIN_UZANTILARI:
        adaylar = [icerik]
    else:
        return []

    bulunanlar = {}
    for ham_parca in adaylar:
        # Yer tutucular ve tirnakli adlar koddur; denetim disi birakilir
        parca = _kod_parcalarini_cikar(ham_parca)

        for eslesme in EKSIK_DESENI.finditer(parca):
            kelime = eslesme.group(1)
            ek = eslesme.group(2)
            dogrusu = EKSIK_YAZIMLAR[kelime.lower()]

            # Duzeltilecek bir sey yoksa atla (ornek: "tamam" -> "tamam")
            if dogrusu == kelime.lower():
                continue

            # Unsuz yumusamasi: "sonucu" dogru yazimdir, uyari verilmez
            if _yumusama_mi(dogrusu, ek):
                continue

            # Turkce buyuk harf: "UYARI", "uyari" kelimesinin dogru buyuk halidir
            if _dogru_buyuk_bicim_mi(kelime + ek, dogrusu):
                continue

            bulunanlar[kelime] = dogrusu
            if len(bulunanlar) >= 6:
                return list(bulunanlar.items())

    return list(bulunanlar.items())


def main():
    try:
        girdi = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        print(json.dumps({}))
        return

    if not BETIKLER_HAZIR:
        print(json.dumps({}))
        return

    if girdi.get("tool_name", "") not in ("Write", "Edit", "MultiEdit"):
        print(json.dumps({}))
        return

    dosya_yolu = girdi.get("tool_input", {}).get("file_path", "")

    if not dosya_yolu or _muaf_mi(dosya_yolu) or not os.path.isfile(dosya_yolu):
        print(json.dumps({}))
        return

    try:
        icerik = Path(dosya_yolu).read_text(encoding="utf-8", errors="ignore")
    except OSError:
        print(json.dumps({}))
        return

    bolumler = []

    kotu_adlar = dosya_adi_kontrol(dosya_yolu)
    if kotu_adlar:
        bolumler.append(
            "Dosya veya klasör adında Türkçe karakter var: " + ", ".join(kotu_adlar) +
            "\nKural: Dosya ve klasör adlarında ASCII kullanılır."
        )

    kimlikler = kimlik_kontrol(dosya_yolu, icerik)
    if kimlikler:
        satirlar = "\n".join(f"    satır {no}: {parca}" for no, parca in kimlikler)
        bolumler.append(
            "Kod içinde (dize ve açıklama dışında) Türkçe karakter var:\n" + satirlar +
            "\nKural: Değişken, fonksiyon ve sınıf adlarında ASCII kullanılır."
        )

    eksikler = metin_kontrol(dosya_yolu, icerik)
    if eksikler:
        satirlar = "\n".join(f"    {yanlis} → {dogru}" for yanlis, dogru in eksikler)
        bolumler.append(
            "Kullanıcıya görünen metinlerde eksik Türkçe karakter olabilir:\n" + satirlar +
            "\nKural: Arayüz metinleri tam Türkçe yazılır (ö, ç, ü, ğ, ı, ş, İ)."
        )

    if not bolumler:
        print(json.dumps({}))
        return

    sonuc = gerekce.uyar(
        "Türkçe yazım kuralı",
        f"Dosya: {dosya_yolu}\n\n" + "\n\n".join(bolumler),
        "Kimlikleri ASCII'ye çevir, kullanıcı metinlerini tam Türkçe yaz.",
    )
    print(json.dumps(sonuc))


if __name__ == "__main__":
    try:
        main()
    except Exception as hata:
        print(json.dumps({"systemMessage": f"Yazim kontrol kancasi hatasi: {hata}"}))
    sys.exit(0)
