#!/usr/bin/env python3
"""PostToolUse kancası: Yazılan dosyalarda araç izi kontrolü.

Kural: Kodda, yorumlarda, dokümantasyonda hiçbir araç/üretici izi kalmaz.
Geliştirici bilgisi her zaman: Enver KOCAK

Yazma/düzenleme sonrası dosyayı tarar, iz bulursa uyarı döndürür.
"""

import sys
import json
import os
import re

# Aranacak iz desenleri (büyük/küçük harf duyarsız)
IZ_DESENLERI = [
    r"\bclaude\b",
    r"\banthropic\b",
    r"\bchatgpt\b",
    r"\bopenai\b",
    r"\bcopilot\b",
    r"\byapay zeka\b",
    r"\bartificial intelligence\b",
    r"\bmachine[- ]generated\b",
    r"\bllm\b",
    r"\bgpt-\d",
    r"\bco-authored-by:",
    r"\bgenerated with\b",
]

# Taranmayacak uzantılar (metin olmayan dosyalar)
MUAF_UZANTILAR = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp",
    ".woff", ".woff2", ".ttf", ".eot",
    ".mp3", ".mp4", ".webm",
    ".zip", ".tar", ".gz", ".7z",
    ".lock", ".map", ".pdf",
}

# Taranmayacak dosya adları (framework'un kendi kural dosyaları)
MUAF_DOSYALAR = {"claude.md", "memory.md", "plugin.json", "iz-kontrol.py"}

# Taranmayacak dizin parçaları
MUAF_DIZINLER = ("/.claude/", "/.git/", "/gelistirme-arastirmasi/", "/_arsiv/")

# Depo kökünde bu dosya varsa, o depo tamamen taramadan muaftır.
# Kullanım: framework'un kendi depoları için. MÜŞTERİ PROJELERINE ASLA KONULMAZ.
MUAFIYET_ISARETI = ".iz-muaf"


def depo_muaf_mi(dosya_yolu):
    """Dosyanın bulunduğu depo muafiyet işareti taşıyor mu?

    Dosyadan yukarı doğru çıkarak işaret dosyası aranır.
    """
    dizin = os.path.dirname(os.path.abspath(dosya_yolu))

    while True:
        if os.path.isfile(os.path.join(dizin, MUAFIYET_ISARETI)):
            return True

        ust = os.path.dirname(dizin)
        if ust == dizin:
            return False
        dizin = ust


def muaf_mi(dosya_yolu):
    """Bu dosya taramadan muaf mı?"""
    duz_yol = dosya_yolu.replace("\\", "/").lower()

    if any(parca in duz_yol for parca in MUAF_DIZINLER):
        return True

    if depo_muaf_mi(dosya_yolu):
        return True

    if os.path.splitext(duz_yol)[1] in MUAF_UZANTILAR:
        return True

    if os.path.basename(duz_yol) in MUAF_DOSYALAR:
        return True

    return False


def dosya_tara(dosya_yolu):
    """Dosya içeriğinde iz ara, bulursa uyarı sözlüğü döndür."""
    if not dosya_yolu or not os.path.isfile(dosya_yolu):
        return None

    if muaf_mi(dosya_yolu):
        return None

    try:
        with open(dosya_yolu, "r", encoding="utf-8", errors="ignore") as dosya:
            icerik = dosya.read()
    except OSError:
        return None

    bulunanlar = []
    for desen in IZ_DESENLERI:
        eslesme = re.search(desen, icerik, re.IGNORECASE)
        if eslesme:
            bulunanlar.append(eslesme.group())

    if not bulunanlar:
        return None

    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": (
                "IZ BULUNDU - temizlenmesi gerekiyor\n"
                "\n"
                f"Dosya: {dosya_yolu}\n"
                f"Bulunan ifadeler: {', '.join(sorted(set(bulunanlar)))}\n"
                "\n"
                "Kural: Kodda, yorumlarda ve dokumantasyonda arac izi kalmaz.\n"
                "Gelistirici bilgisi: Enver KOCAK\n"
                "\n"
                "Bu ifadeleri simdi kaldir."
            ),
        }
    }


def main():
    try:
        girdi = json.load(sys.stdin)

        if girdi.get("tool_name", "") not in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
            print(json.dumps({}))
            sys.exit(0)

        dosya_yolu = girdi.get("tool_input", {}).get("file_path", "")
        sonuc = dosya_tara(dosya_yolu)

        print(json.dumps(sonuc if sonuc else {}))

    except Exception as hata:
        print(json.dumps({"systemMessage": f"Iz kontrol kancasi hatasi: {hata}"}))

    sys.exit(0)


if __name__ == "__main__":
    main()
