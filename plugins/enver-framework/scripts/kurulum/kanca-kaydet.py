#!/usr/bin/env python3
"""Kancaları ayar dosyasına kaydeder.

Önceki kurulum betikleri kancaları yalnız kopyalıyordu; kaydetmediği için
hiçbiri devreye girmiyordu. Bu betik kayıt işini yapar.

Mevcut ayarlar korunur - sadece eksik kanca girdileri eklenir, hiçbir şey silinmez.

Kullanım:
    python kanca-kaydet.py <kanca-dizini> [ayar-dosyası]

Geliştirici: Enver KOCAK
"""

import json
import sys
from pathlib import Path

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

# Hangi kanca hangi olaya bağlanır.
# Aynı kanca birden çok olaya bağlanabilir (örnek: kasa-koruma).
KANCA_TANIMLARI = [
    # Kabuk komutları
    {"dosya": "sunucu-koruma.py", "olay": "PreToolUse", "eslesme": "Bash"},
    {"dosya": "git-gizlilik-koruma.py", "olay": "PreToolUse", "eslesme": "Bash"},
    {"dosya": "veri-koruma.py", "olay": "PreToolUse", "eslesme": "Bash"},
    {"dosya": "kasa-koruma.py", "olay": "PreToolUse", "eslesme": "Bash"},

    # Dosya yazma
    {"dosya": "veri-koruma.py", "olay": "PreToolUse",
     "eslesme": "Write|Edit|MultiEdit|NotebookEdit"},
    {"dosya": "kasa-koruma.py", "olay": "PreToolUse",
     "eslesme": "Write|Edit|MultiEdit|NotebookEdit"},

    # Dosya okuma
    {"dosya": "kasa-koruma.py", "olay": "PreToolUse", "eslesme": "Read"},

    # Yazma sonrası denetimler
    {"dosya": "iz-kontrol.py", "olay": "PostToolUse", "eslesme": "Write|Edit|MultiEdit"},
    {"dosya": "yazim-kontrol.py", "olay": "PostToolUse", "eslesme": "Write|Edit|MultiEdit"},

    # Oturum kaydı (engellemez, sadece yazar)
    {"dosya": "oturum-kayit.py", "olay": "PostToolUse", "eslesme": "Write|Edit|MultiEdit"},
    {"dosya": "oturum-kayit.py", "olay": "PostToolUse", "eslesme": "Bash"},

    # Açılış brifingi
    {"dosya": "oturum-acilis.py", "olay": "SessionStart", "eslesme": None},

    # Tam yetki modu - istisnalarda karar vermez, korumaları devre dışı bırakmaz
    {"dosya": "tam-yetki.py", "olay": "PreToolUse", "eslesme": "Bash"},
    {"dosya": "tam-yetki.py", "olay": "PreToolUse",
     "eslesme": "Write|Edit|MultiEdit|NotebookEdit"},
    {"dosya": "tam-yetki.py", "olay": "PreToolUse", "eslesme": "Read"},

    # Kalite kapısı - tam yetkide "bitti" demeyi ölçüme bağlar
    {"dosya": "kalite-kapisi.py", "olay": "Stop", "eslesme": None},
]


def ayarlari_oku(yol):
    if not yol.is_file():
        return {}
    try:
        with open(yol, "r", encoding="utf-8") as dosya:
            veri = json.load(dosya)
        return veri if isinstance(veri, dict) else {}
    except (OSError, json.JSONDecodeError) as hata:
        print(f"  UYARI: Mevcut ayarlar okunamadı ({hata}). Yedeklenip yeniden yazılacak.")
        return {}


def komut_uret(kanca_dizini, dosya_adi):
    yol = (Path(kanca_dizini) / dosya_adi).as_posix()
    return f'python "{yol}"'


def girdi_var_mi(kanca_listesi, komut):
    return any(k.get("command") == komut for k in kanca_listesi)


def kaydet(kanca_dizini, ayar_yolu):
    kanca_dizini = Path(kanca_dizini).resolve()
    ayar_yolu = Path(ayar_yolu)

    ayarlar = ayarlari_oku(ayar_yolu)
    kancalar = ayarlar.setdefault("hooks", {})

    eklenen = 0
    zaten_var = 0
    bulunamayan = []

    for tanim in KANCA_TANIMLARI:
        kanca_dosyasi = kanca_dizini / tanim["dosya"]
        if not kanca_dosyasi.is_file():
            bulunamayan.append(tanim["dosya"])
            continue

        komut = komut_uret(kanca_dizini, tanim["dosya"])
        olay_listesi = kancalar.setdefault(tanim["olay"], [])

        # Bazı olaylarda eşleşme yoktur (örnek: SessionStart) - o zaman
        # grup matcher alanı taşımaz.
        eslesme = tanim.get("eslesme")

        grup = None
        for aday in olay_listesi:
            if aday.get("matcher") == eslesme:
                grup = aday
                break

        if grup is None:
            grup = {"hooks": []} if eslesme is None else {"matcher": eslesme, "hooks": []}
            olay_listesi.append(grup)

        ic_liste = grup.setdefault("hooks", [])

        if girdi_var_mi(ic_liste, komut):
            zaten_var += 1
            continue

        ic_liste.append({"type": "command", "command": komut})
        eklenen += 1

    # Yedek al, sonra yaz
    if ayar_yolu.is_file():
        yedek = ayar_yolu.with_suffix(ayar_yolu.suffix + ".yedek")
        yedek.write_text(ayar_yolu.read_text(encoding="utf-8"), encoding="utf-8")

    ayar_yolu.parent.mkdir(parents=True, exist_ok=True)
    with open(ayar_yolu, "w", encoding="utf-8") as dosya:
        json.dump(ayarlar, dosya, ensure_ascii=False, indent=2)
        dosya.write("\n")

    return eklenen, zaten_var, bulunamayan


def main():
    if len(sys.argv) < 2:
        print("Kullanım: python kanca-kaydet.py <kanca-dizini> [ayar-dosyasi]")
        return 1

    kanca_dizini = sys.argv[1]

    if len(sys.argv) > 2:
        ayar_yolu = Path(sys.argv[2])
    else:
        ayar_yolu = Path.home() / ".claude" / "settings.json"

    if not Path(kanca_dizini).is_dir():
        print(f"HATA: Kanca dizini bulunamadı: {kanca_dizini}")
        return 1

    eklenen, zaten_var, bulunamayan = kaydet(kanca_dizini, ayar_yolu)

    print(f"  Ayar dosyası : {ayar_yolu}")
    print(f"  Eklenen      : {eklenen}")
    print(f"  Zaten kayıtlı: {zaten_var}")

    if bulunamayan:
        print(f"  BULUNAMAYAN  : {', '.join(bulunamayan)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
