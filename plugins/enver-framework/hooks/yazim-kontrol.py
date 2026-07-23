#!/usr/bin/env python3
"""PostToolUse kancası: Türkçe yazım denetimi.

İki yönlü kural (E17):

  1. KIMLIKLERDE TÜRKÇE KARAKTER YASAK
     Değişken, fonksiyon, sınıf ve dosya adlarında o, c, u, g, i, s
     harflerinin Türkçe biçimleri kullanılmaz. Kod her ortamda aynı çalışmalı.

  2. KULLANICI METINLERINDE TÜRKÇE KARAKTER ZORUNLU
     Arayüz yazıları, hata mesajları ve web içeriği tam Türkçe yazılır:
     ö, ç, ü, ğ, ı, ş, İ. "Güncelle" değil "Güncelle".

Bu kanca engellemez, uyarır - düzeltme bağlam gerektirir.

Geliştirici: Enver KOCAK
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

# İçeriğin tamamı kullanıcıya görünen metin sayılan dosyalar.
# .json bilinçli olarak DIŞARIDA: ayar dosyalarında yollar, komutlar ve alan
# adları geçer; bunlar ASCII kalmak zorunda ve metin gibi denetlenirse
# sürekli yanlış uyarı üretir.
METIN_UZANTILARI = {".md", ".txt", ".html", ".htm", ".vue", ".twig"}

# İç geliştirme notları ve üretilmiş dosyalar taranmaz.
# geliştirme-araştırması/ çalışma notudur, kullanıcıya sunulan bir yüzey değil -
# iz-kontrol.py de aynı dizini muaf tutuyor.
TARANMAYAN_DIZINLER = (
    "/node_modules/", "/.git/", "/vendor/", "/dist/", "/build/",
    "/_arsiv/", "/_calisma/", "/gelistirme-arastirmasi/",
)

# Dizeleri ve açıklama satırlarını temizleyen desenler
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

# Kullanıcıya görünen metinlerde sık yapılan eksik yazımlar.
# Anahtar: ASCII biçimi, değer: doğru Türkçe biçimi.
#
# Listeye yalnız ŞU İKİ KOŞULU birden sağlayan kelimeler girer:
#   1. Doğru biçimi ASCII biçimden gerçekten farklı olacak.
#   2. En az dört harf olacak - "aç", "seç", "sil" gibi kısa kökler
#      İngilizce kelimelerin içinde geçiyor ve yanlış uyarı üretiyor.
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

# Türkçe ekli bir dil: "şifreniz", "kullanıcılar", "güncelleme" de yakalanmalı.
# Bu yüzden kökün ardından gelen ek harfleri desene dahil edilir.
EKSIK_DESENI = re.compile(
    r"\b(" + "|".join(sorted(EKSIK_YAZIMLAR, key=len, reverse=True)) + r")([a-z]*)\b",
    re.IGNORECASE,
)

# ÜNSÜZ YUMUŞAMASI
#
# Türkçede c, k, p, t ile biten kelimeler ünlü ile başlayan bir ek aldığında
# yumuşar: sonuç -> sonucu, kayıt -> kaydı, kitap -> kitabı.
#
# Yani "sonucu" YANLIŞ DEĞİL, doğru yazımın ta kendisi. Kök halinde "sonuç"
# yazılması yanlıştır ama ekli halinde yumuşamış biçim beklenir.
#
# Bu ayrımı yapmayan bir denetim, doğru yazılmış metinleri hatalı gösterir.
YUMUSAYAN_SONLAR = ("ç", "k", "p", "t")
UNLULER = "aeıioöuüAEIİOÖUÜ"


def _yumusama_mi(dogru_bicim, ek):
    """Bulunan yazım, ünsüz yumuşaması yüzünden mi böyle görünüyor?"""
    if not ek:
        return False

    if not dogru_bicim.endswith(YUMUSAYAN_SONLAR):
        return False

    return ek[0] in UNLULER


# TÜRKÇE BÜYÜK HARF
#
# Türkçede i ve i harflerinin büyüğü farklıdır:
#     i -> I        (noktasız)
#     i -> I        (noktalı)
#
# Yani "uyarı" kelimesinin büyük hali "UYARI"dir; içinde nokta yoktur.
# İngilizce büyütme kuralı uygulanırsa "UYARI" yanlış görünür, oysa doğrudur.
BUYUTME_ESLEMESI = str.maketrans({
    "ı": "I", "i": "İ", "ç": "Ç", "ğ": "Ğ", "ö": "Ö", "ş": "Ş", "ü": "Ü",
})


def turkce_buyut(metin):
    """Türkçe kurallarına göre büyük harfe çevir."""
    return metin.translate(BUYUTME_ESLEMESI).upper()


def _dogru_buyuk_bicim_mi(bulunan, dogru_bicim):
    """Büyük harfle yazılmış biçim aslında doğru mu?"""
    if not bulunan.isupper():
        return False

    return bulunan == turkce_buyut(dogru_bicim)


# Bu kancanın kendi sözlüğü, doğası gereği ASCII biçimleri içerir;
# kendini taraması anlamsız uyarı üretir.
MUAF_DOSYALAR = {"yazim-kontrol.py"}


def _muaf_mi(dosya_yolu):
    duz = dosya_yolu.replace("\\", "/").lower()

    if Path(duz).name in MUAF_DOSYALAR:
        return True

    return any(parca in duz for parca in TARANMAYAN_DIZINLER)


def _kod_govdesi(icerik):
    """Dize ve açıklamaları çıkar - geriye kimlikler kalır."""
    for desen in DIZE_VE_ACIKLAMA:
        icerik = desen.sub(" ", icerik)
    return icerik


# Kod içindeki her dize kullanıcıya gösterilmez. Sözlük anahtarları, dosya
# adları ve alan adları da dize olarak yazılır ve ASCII kalmak zorundadır
# (örnek: veri.get("açıklama"), "açıklamalar.json").
#
# Ayırt etme kuralı: gösterilen metin ya boşluk içerir ya da büyük harfle
# başlar. Tek kelimelik, küçük harfli dizeler anahtar sayılır ve atlanır.
ANAHTAR_GORUNUMLU = re.compile(r"^[a-z0-9_.\-/\\]+$")

# Yol, kabuk komutu ya da değişken içeren dizeler gösterilen metin değildir.
KOMUT_GORUNUMLU = re.compile(
    r"(^|\s)(python|node|npm|git|bash|sh|psql|mysql|ssh|scp|curl|pip)\s"
    r"|\$\{?[A-Z_]{3,}"
    r"|[/\\][a-z0-9_.\-]+[/\\]"
    r"|\.(py|js|ts|php|sh|ps1|json|md|html|css|sql|jsonl)\b"
    # CSS özel değişkeni ve HTML etiketi: kod, gösterilen metin değil
    r"|--[a-z][a-z0-9-]*\s*:"
    r"|<[a-z]+[\s>/]"
)


# Dize desenleri ham metin üzerinde birbirinden bağımsız çalışır; kod içinde
# geçen tek tırnak ("\"'" gibi) yanlış eşleşip kocaman bir kod parçasını dize
# gibi gösterebiliyor. Kod noktalaması taşıyan parçalar bu yüzden elenir.
KOD_NOKTALAMASI = re.compile(r"[=;{}()\[\]]")

# Düzenli ifade desenleri de dize olarak yazılır ve içinde ASCII kökler geçer
# (örnek: r"pos\b|ödeme|payment"). Bunlar kullanıcıya gösterilmez.
DESEN_GORUNUMLU = re.compile(r"\\[bdswAZ]|\(\?|\|.*\||\[\^|\{\d")


def _gosterilen_metin_mi(ham_dize):
    """Bu dize kullanıcıya gösteriliyor mu, yoksa anahtar ya da kod mu?"""
    icerik = ham_dize.strip("\"'`").strip()

    if not icerik or len(icerik) < 4:
        return False

    # Tek kelimelik küçük harfli dize: sözlük anahtarı ya da alan adı
    if ANAHTAR_GORUNUMLU.match(icerik):
        return False

    # Yol, dosya adı, kabuk komutu ya da ortam değişkeni
    if KOMUT_GORUNUMLU.search(icerik):
        return False

    # Düzenli ifade deseni
    if DESEN_GORUNUMLU.search(icerik):
        return False

    # Çok satırlı bir parça ancak kod noktalaması taşımıyorsa metin sayılır
    if "\n" in icerik and KOD_NOKTALAMASI.search(icerik):
        return False

    return True


def _dizeleri_topla(icerik):
    """Kullanıcıya görünebilecek dize içeriklerini topla."""
    dizeler = []
    for desen in DIZE_VE_ACIKLAMA[:5]:
        for eslesme in desen.finditer(icerik):
            ham = eslesme.group(0)
            if _gosterilen_metin_mi(ham):
                dizeler.append(ham)
    return dizeler


def kimlik_kontrol(dosya_yolu, icerik):
    """Kimliklerde Türkçe karakter var mı?"""
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
    """Dosya ve klasör adında Türkçe karakter var mı?"""
    bagil = dosya_yolu.replace("\\", "/")
    parcalar = [p for p in bagil.split("/") if p]

    return [p for p in parcalar if TURKCE_DESEN.search(p)]


# Bir metin dizesinin içinde görünen her şey kullanıcıya gösterilen yazı değil:
#
#   {müşteri}          biçimlendirme yer tutucusu - değişken adı, koddur
#   `görev`            ters tırnak içinde alan adı
#   'kasa_anahtarı'    tek tırnak içinde alan adı
#
# Bunların hepsi ASCII kalmak zorundadır, denetim dışı bırakılır.
# Kural: kullanıcı metninde bir alan adı anılacaksa tırnak içine alınır.
KOD_PARCASI = re.compile(r"\{[^{}]*\}|`[^`]*`|'[^']*'")


# Yardım metinlerinde komut listesi şu biçimde yazılır:
#
#     özet      Bütün projelerin görev özeti
#     liste     Görevleri göster
#
# Soldaki komut adı ASCII kalmak zorundadır; sağdaki açıklama denetlenir.
KOMUT_LISTESI_SATIRI = re.compile(r"^(\s{2,})([a-z][a-z0-9_-]*)(\s{2,})", re.MULTILINE)


def _kod_parcalarini_cikar(metin):
    """Yer tutucu, tırnaklı ad ve komut adlarını denetim dışı bırak."""
    metin = KOD_PARCASI.sub(" ", metin)
    return KOMUT_LISTESI_SATIRI.sub(r"\1 \3", metin)


def metin_kontrol(dosya_yolu, icerik):
    """Kullanıcı metinlerinde eksik Türkçe karakter var mı?"""
    uzanti = Path(dosya_yolu).suffix.lower()

    if uzanti in KOD_UZANTILARI:
        adaylar = _dizeleri_topla(icerik)
    elif uzanti in METIN_UZANTILARI:
        adaylar = [icerik]
    else:
        return []

    bulunanlar = {}
    for ham_parca in adaylar:
        # Yer tutucular ve tırnaklı adlar koddur; denetim dışı bırakılır
        parca = _kod_parcalarini_cikar(ham_parca)

        for eslesme in EKSIK_DESENI.finditer(parca):
            kelime = eslesme.group(1)
            ek = eslesme.group(2)
            dogrusu = EKSIK_YAZIMLAR[kelime.lower()]

            # Düzeltilecek bir şey yoksa atla (örnek: "tamam" -> "tamam")
            if dogrusu == kelime.lower():
                continue

            # Ünsüz yumuşaması: "sonucu" doğru yazımdır, uyarı verilmez
            if _yumusama_mi(dogrusu, ek):
                continue

            # Türkçe büyük harf: "UYARI", "uyarı" kelimesinin doğru büyük halidir
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
