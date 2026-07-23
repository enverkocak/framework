#!/usr/bin/env python3
"""PreToolUse kancası: Depo gizlilik koruması.

Kural: HER DEPO PRIVATE olacak.
- Yeni depo oluşturulurken --private zorunlu.
- Mevcut bir depoyu public yapma girişimi engellenir.
- Public yapmak gerekiyorsa Enver GitHub arayüzüne girip elle yapar.
"""

import sys
import json
import re

# Yeni depo oluşturma komutu
DEPO_OLUSTUR = re.compile(r"\bgh\s+repo\s+create\b", re.IGNORECASE)

# Görünürlük değiştirme komutu
DEPO_DUZENLE = re.compile(r"\bgh\s+repo\s+edit\b", re.IGNORECASE)

# Public'e çevirme belirtileri
PUBLIC_DESENLERI = [
    re.compile(r"--public\b", re.IGNORECASE),
    re.compile(r"--visibility[= ]+public\b", re.IGNORECASE),
    re.compile(r'"private"\s*:\s*false', re.IGNORECASE),
    re.compile(r"private=false", re.IGNORECASE),
]

# API üzerinden görünürlük değiştirme
API_GORUNURLUK = re.compile(r"\bgh\s+api\b.*\b(visibility|private)\b", re.IGNORECASE)

PRIVATE_VAR = re.compile(r"--private\b", re.IGNORECASE)


def engelle(sebep):
    """İşlemi reddet ve Türkçe gerekçe döndür."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": sebep,
        }
    }


def kontrol_et(komut):
    if not komut:
        return None

    public_istegi = any(desen.search(komut) for desen in PUBLIC_DESENLERI)

    # 1) Açıkça public yapma girişimi
    if public_istegi:
        return engelle(
            "ENGELLENDI - Depo gizlilik kurali\n"
            "\n"
            "Bu komut bir depoyu HERKESE ACIK (public) yapmaya calisiyor.\n"
            "Kural: Butun depolar PRIVATE olacak.\n"
            "\n"
            "Gercekten acmak istiyorsan GitHub arayuzune girip elle ac.\n"
            "Bu islem buradan yapilamaz."
        )

    # 2) Yeni depo oluşturulurken --private yoksa
    if DEPO_OLUSTUR.search(komut) and not PRIVATE_VAR.search(komut):
        return engelle(
            "ENGELLENDI - Depo gizlilik kurali\n"
            "\n"
            "Yeni depo olusturuluyor ama --private bayragi yok.\n"
            "Kural: Butun yeni depolar PRIVATE olarak acilir.\n"
            "\n"
            "Komuta --private ekleyip tekrar dene."
        )

    # 3) API üzerinden görünürlük oynaması - onay iste
    if API_GORUNURLUK.search(komut):
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "ask",
                "permissionDecisionReason": (
                    "DIKKAT - Depo gorunurlugu degistirilmek uzere\n"
                    "\n"
                    "Bu komut API uzerinden depo gorunurlugune dokunuyor.\n"
                    "Ne yaptigini kontrol et, sonra onayla."
                ),
            }
        }

    return None


def main():
    try:
        girdi = json.load(sys.stdin)

        if girdi.get("tool_name", "") != "Bash":
            print(json.dumps({}))
            sys.exit(0)

        komut = girdi.get("tool_input", {}).get("command", "")
        sonuc = kontrol_et(komut)

        print(json.dumps(sonuc if sonuc else {}))

    except Exception as hata:
        print(json.dumps({"systemMessage": f"Gizlilik kancasi hatasi: {hata}"}))

    sys.exit(0)


if __name__ == "__main__":
    main()
