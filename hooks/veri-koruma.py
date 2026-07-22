#!/usr/bin/env python3
"""PreToolUse kancasi: Veri korumasi.

Iki kural zorlanir:

  1. SILME YASAGI (E7)
     Hicbir veri silinmez. Silme komutlari engellenir, kullanici arsive yonlendirilir.

  2. YIKICI KOMUT KALKANI (T11)
     Geri donusu olmayan komutlar (gecmis silme, zorla gonderme, tablo dusurme,
     disk yazma) once acik onay ister.

Ayrica ana dizine gecici dosya yazilmasi engellenir - calisma alanina yonlendirilir.

Gelistirici: Enver KOCAK
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _ortak_yol as ortak_yol  # noqa: E402

BETIKLER_HAZIR = ortak_yol.hazirla()

if BETIKLER_HAZIR:
    import gerekce
    import yollar
else:
    gerekce = None
    yollar = None


# Komut konumunu yakalayan on ek: satir basi veya ayirac sonrasi
KOMUT_BASI = r"(?:^|[;&|]\s*|\$\(\s*|`\s*|\bsudo\s+|\bthen\s+|\bdo\s+)"


def _desen(govde):
    return re.compile(KOMUT_BASI + govde, re.IGNORECASE | re.MULTILINE)


# --- Silme komutlari: kesin engellenir -------------------------------------

SILME_DESENLERI = [
    (_desen(r"rm\s+(?:-\w+\s+)*"), "rm"),
    (_desen(r"rmdir\b"), "rmdir"),
    (_desen(r"unlink\b"), "unlink"),
    (_desen(r"shred\b"), "shred"),
    (_desen(r"del\s+/"), "del"),
    (_desen(r"erase\b"), "erase"),
    (_desen(r"Remove-Item\b"), "Remove-Item"),
    (_desen(r"rd\s+/s"), "rd /s"),
    (re.compile(r"\bfind\b[^|;&]*\s-delete\b", re.IGNORECASE), "find -delete"),
    (re.compile(r"\bgit\s+clean\b[^|;&]*-\w*f", re.IGNORECASE), "git clean -f"),
]

# Silme sayilmayacak zararsiz kullanimlar
SILME_MUAFIYETLERI = [
    re.compile(r"\brm\s+-?-?help\b", re.IGNORECASE),
    re.compile(r"\bnpm\b|\bpnpm\b|\byarn\b", re.IGNORECASE),
]


# --- Yikici komutlar: acik onay ister --------------------------------------

YIKICI_DESENLER = [
    (re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE),
     "git reset --hard",
     "Kaydedilmemiş bütün değişiklikler geri alınır."),

    (re.compile(r"\bgit\s+push\b[^|;&]*(--force\b|(?<!-)-f\b)", re.IGNORECASE),
     "git push --force",
     "Uzak depodaki geçmişin üzerine yazılır."),

    (re.compile(r"\bgit\s+checkout\s+--\s+\.", re.IGNORECASE),
     "git checkout -- .",
     "Bütün yerel değişiklikler geri alınır."),

    (re.compile(r"\bgit\s+branch\s+-D\b", re.IGNORECASE),
     "git branch -D",
     "Birleştirilmemiş dal zorla silinir."),

    (re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE),
     "DROP",
     "Veritabanı nesnesi kalıcı olarak düşürülür."),

    (re.compile(r"\bTRUNCATE\s+TABLE\b", re.IGNORECASE),
     "TRUNCATE TABLE",
     "Tablodaki bütün satırlar silinir."),

    (re.compile(r"\bDELETE\s+FROM\b(?![^;]*\bWHERE\b)", re.IGNORECASE),
     "WHERE'siz DELETE",
     "Koşul verilmediği için tablodaki bütün satırlar silinir."),

    (re.compile(r"\bmkfs\b|\bformat\s+[a-z]:", re.IGNORECASE),
     "disk biçimlendirme",
     "Disk bölümü biçimlendirilir."),

    (re.compile(r"\bdd\b[^|;&]*\bof=/dev/", re.IGNORECASE),
     "dd of=/dev/",
     "Doğrudan aygıta yazma yapılır."),

    (re.compile(r">\s*/dev/(sd|nvme|hd)", re.IGNORECASE),
     "aygıta yönlendirme",
     "Çıktı doğrudan disk aygıtına yazılır."),

    (re.compile(r"\bchmod\s+(-R\s+)?777\b", re.IGNORECASE),
     "chmod 777",
     "Dosya herkese tam yetkiyle açılır."),
]


def silme_kontrol(komut):
    for muafiyet in SILME_MUAFIYETLERI:
        if muafiyet.search(komut):
            return None

    for desen, ad in SILME_DESENLERI:
        if desen.search(komut):
            return ad
    return None


def yikici_kontrol(komut):
    for desen, ad, etki in YIKICI_DESENLER:
        if desen.search(komut):
            return ad, etki
    return None, None


def bash_kontrol(komut):
    if not komut:
        return None

    silme_adi = silme_kontrol(komut)
    if silme_adi:
        return gerekce.engelle(
            "Silme koruması",
            komut,
            f"Bu komut '{silme_adi}' ile veri siliyor.\n"
            "Kural: Hiçbir veri silinmez. İşi biten her şey notuyla arşivlenir.",
            [
                'Arşivle: python scripts/ortak/arsiv.py <yol> "iş adı" "neden"',
                "Geçici dosyaysa zaten _calisma/ altında olmalı, arşivlenince temizlenir.",
                "Gerçekten silinmesi gerekiyorsa dosya yöneticisinden elle sil.",
            ],
            "Arşivleme silmeye göre daha güvenli: kayıt kalır, geri alınabilir.",
        )

    yikici_adi, etki = yikici_kontrol(komut)
    if yikici_adi:
        return gerekce.onay_iste(
            "Geri dönüşü olmayan işlem",
            komut,
            f"Bu komut '{yikici_adi}' çalıştırıyor.\n{etki}",
            [
                "Ne yaptığını biliyorsan onayla.",
                "Emin değilsen önce yedek al.",
                "Vazgeçmek için reddet.",
            ],
        )

    return None


def yazma_kontrol(dosya_yolu):
    """Ana dizine gecici dosya yazilmasini engelle (E7)."""
    if not dosya_yolu or yollar is None:
        return None

    try:
        kok = yollar.proje_kok(dosya_yolu)
        if not yollar.ana_dizinde_mi(dosya_yolu, kok):
            return None
        if not yollar.gecici_mi(dosya_yolu):
            return None
    except (OSError, ValueError):
        return None

    ad = Path(dosya_yolu).name

    return gerekce.engelle(
        "Ana dizin düzeni",
        f"Ana dizine yazma: {ad}",
        "Geçici ve test amaçlı dosyalar ana dizinde durmaz.\n"
        "Kural: Ana dizin temiz kalır.",
        [
            f"Çalışma alanına yaz: _calisma/{ad}",
            "İşi bitince arşivle, notunu ekle.",
        ],
    )


def main():
    try:
        girdi = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        print(json.dumps({}))
        return

    if not BETIKLER_HAZIR:
        print(json.dumps({
            "systemMessage": "Veri koruma kancasi: ortak betikler bulunamadi, kontrol atlandi."
        }))
        return

    arac = girdi.get("tool_name", "")
    girdiler = girdi.get("tool_input", {})

    sonuc = None

    if arac == "Bash":
        sonuc = bash_kontrol(girdiler.get("command", ""))
    elif arac in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        sonuc = yazma_kontrol(girdiler.get("file_path", ""))

    # ensure_ascii bilincli olarak acik birakildi: Turkce karakterler \u kacisiyla
    # yazilir, boylece konsol kodlamasi ne olursa olsun JSON gecerli kalir.
    print(json.dumps(sonuc if sonuc else {}))


if __name__ == "__main__":
    try:
        main()
    except Exception as hata:  # kanca asla akisi kirmasin
        print(json.dumps({"systemMessage": f"Veri koruma kancasi hatasi: {hata}"}))
    sys.exit(0)
