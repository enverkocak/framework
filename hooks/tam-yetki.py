#!/usr/bin/env python3
"""PreToolUse kancası: Tam yetki modu.

Tam yetki açıkken faz bitene kadar izin sorulmaz; iş kesintisiz akar.
Faz bittiğinde durulur ve tek seferde rapor verilir.

TAM YETKİ, HIZ DEMEKTİR - KONTROLSÜZLÜK DEĞİL.

Bu modda bile durduran işlemler:
  - Kasa parolası istenmesi
  - Silme girişimi
  - Başka müşteri dizinine erişim
  - Canlı ortama çıkış
  - Depo görünürlüğünü değiştirme

Bu kanca bu istisnalarda **karar vermez**, sessiz kalır; kararı ilgili
koruma verir. Böylece tam yetki hiçbir korumayı devre dışı bırakamaz.

Reddetme her zaman izin vermeye üstündür: bu kanca "izin ver" dese bile
başka bir koruma "engelle" derse işlem durur.

Geliştirici: Enver KOCAK
"""

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _ortak_yol as ortak_yol  # noqa: E402

BETIKLER_HAZIR = ortak_yol.hazirla()

if BETIKLER_HAZIR:
    try:
        import ayarlar
        import yollar
    except ImportError:
        ayarlar = yollar = None
else:
    ayarlar = yollar = None


# Tam yetki modunda bile karar verilmeyecek işlemler.
# Bu desenlerden biri tuttuğunda kanca sessiz kalır ve normal izin
# akışı işler; ilgili koruma ne diyorsa o olur.
ISTISNALAR = [
    # Kasa
    (re.compile(r"kasa[/\\]kasa\.py|kasa\.kilit|kasa-oturum", re.IGNORECASE),
     "kasa erişimi"),

    # Silme
    (re.compile(r"(?:^|[;&|]\s*)(rm|rmdir|del|erase|shred|unlink|Remove-Item)\b",
                re.IGNORECASE | re.MULTILINE), "silme girişimi"),
    (re.compile(r"\bgit\s+clean\b[^|;&]*-\w*f", re.IGNORECASE), "silme girişimi"),
    (re.compile(r"\bfind\b[^|;&]*\s-delete\b", re.IGNORECASE), "silme girişimi"),

    # Uzak sunucu
    (re.compile(r"\b(ssh|scp|sftp|rsync)\b", re.IGNORECASE), "uzak sunucu erişimi"),

    # Canlıya çıkış
    (re.compile(r"\b(deploy|publish|release)\b", re.IGNORECASE), "canlıya çıkış"),
    (re.compile(r"\bgit\s+push\b", re.IGNORECASE), "depoya gönderme"),
    (re.compile(r"\bnpm\s+publish\b|\bdocker\s+push\b", re.IGNORECASE), "yayınlama"),

    # Depo görünürlüğü
    (re.compile(r"\bgh\s+repo\b", re.IGNORECASE), "depo ayarı"),

    # Geri dönüşü olmayan işlemler
    (re.compile(r"\bgit\s+reset\s+--hard\b", re.IGNORECASE), "geri alınamaz işlem"),
    (re.compile(r"\bDROP\s+(TABLE|DATABASE|SCHEMA)\b", re.IGNORECASE), "veritabanı işlemi"),
    (re.compile(r"\bTRUNCATE\s+TABLE\b", re.IGNORECASE), "veritabanı işlemi"),
    (re.compile(r"\bDELETE\s+FROM\b", re.IGNORECASE), "veritabanı işlemi"),
    (re.compile(r"\bmkfs\b|\bformat\s+[a-z]:", re.IGNORECASE), "disk işlemi"),

    # Ödeme ve kimlik
    (re.compile(r"\b(payment|checkout|invoice|fatura|odeme)\b", re.IGNORECASE),
     "ödeme işlemi"),
]


def istisna_mi(metin):
    """Bu işlem tam yetki modunda bile ayrı değerlendirilmeli mi?"""
    if not metin:
        return None

    for desen, ad in ISTISNALAR:
        if desen.search(str(metin)):
            return ad
    return None


def tam_yetki_acik_mi(kok=None):
    if ayarlar is None:
        return False
    return bool(ayarlar.oku(kok).get("tam_yetki"))


def main():
    try:
        girdi = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        print(json.dumps({}))
        return

    if not BETIKLER_HAZIR or ayarlar is None:
        print(json.dumps({}))
        return

    try:
        kok = yollar.proje_kok()
    except Exception:
        kok = None

    if not tam_yetki_acik_mi(kok):
        print(json.dumps({}))
        return

    girdiler = girdi.get("tool_input", {})

    # İncelenecek metin: komut ya da dosya yolu
    incelenecek = " ".join(str(deger) for deger in (
        girdiler.get("command"),
        girdiler.get("file_path"),
        girdiler.get("url"),
    ) if deger)

    ad = istisna_mi(incelenecek)

    if ad:
        # Karar verme; normal izin akışına birak
        print(json.dumps({}))
        return

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": (
                "Tam yetki modu acik - faz bitene kadar izin sorulmuyor.\n"
                "Kapatmak icin: python scripts/faz/mod.py dikkatli"
            ),
        }
    }))


if __name__ == "__main__":
    try:
        main()
    except Exception as hata:
        # Kanca cokerse tam yetki kendiliginden devre disi kalir - guvenli taraf
        print(json.dumps({"systemMessage": f"Tam yetki kancasi hatasi: {hata}"}))
    sys.exit(0)
