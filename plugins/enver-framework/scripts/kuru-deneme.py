#!/usr/bin/env python3
"""Sanal deneme - komutu çalıştırmadan ne olacağını gösterir.

Tahmin yürütmez: komutu gerçek korumalara sorar ve verdikleri kararı raporlar.
Böylece rapor ile gerçek davranış birbirinden ayrılamaz.

Kullanım:
    python kuru-deneme.py "rm -rf eski/"
    python kuru-deneme.py --araç Write --dosya /yol/dosya.tmp

Geliştirici: Enver KOCAK
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI / "ortak"))

import yollar  # noqa: E402

# Sırasıyla sorulacak korumalar
KORUMALAR = [
    ("Müşteri sunucusu koruması", "sunucu-koruma.py"),
    ("Depo gizlilik kuralı", "git-gizlilik-koruma.py"),
    ("Veri koruması", "veri-koruma.py"),
    ("Kasa ve sır koruması", "kasa-koruma.py"),
]

KARAR_ETIKETLERI = {
    "deny": "ENGELLENİR",
    "ask": "ONAY İSTER",
    "allow": "İZİN VERİLİR",
}


def kanca_dizini():
    """Kancaların bulunduğu dizini bul."""
    adaylar = [
        SCRIPT_DIZINI.parent.parent.parent / "hooks",
        Path(yollar.proje_kok()) / "hooks",
    ]
    for aday in adaylar:
        if (aday / "veri-koruma.py").is_file():
            return aday
    return None


def korumaya_sor(kanca_yolu, arac, girdiler):
    """Bir korumaya komutu sor, kararını döndür."""
    veri = json.dumps({"tool_name": arac, "tool_input": girdiler})

    try:
        sonuc = subprocess.run(
            [sys.executable, str(kanca_yolu)],
            input=veri, capture_output=True, text=True,
            encoding="utf-8", timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as hata:
        return "hata", f"Koruma çalıştırılamadı: {hata}"

    try:
        cikti = json.loads(sonuc.stdout or "{}")
    except json.JSONDecodeError:
        return "hata", "Koruma geçersiz çıktı verdi."

    ozel = cikti.get("hookSpecificOutput", {})
    karar = ozel.get("permissionDecision")

    if karar:
        return karar, ozel.get("permissionDecisionReason", "")

    if cikti.get("systemMessage"):
        return "bilgi", cikti["systemMessage"]

    return "gecti", ""


def rapor(arac, girdiler):
    dizin = kanca_dizini()

    satirlar = [
        "SANAL DENEME",
        "=" * 52,
        "",
        "Bu komut ÇALIŞTIRILMADI. Aşağıdaki sonuç, komut gerçekten",
        "çalıştırılsaydı korumaların ne yapacağını gösterir.",
        "",
        f"Araç   : {arac}",
    ]

    for anahtar, deger in girdiler.items():
        satirlar.append(f"{anahtar:7}: {deger}")

    satirlar += ["", "-" * 52, ""]

    if dizin is None:
        satirlar.append("Korumalar bulunamadı - sanal deneme yapılamıyor.")
        return "\n".join(satirlar), 1

    engelleyen = []
    onay_isteyen = []

    for ad, dosya in KORUMALAR:
        kanca = dizin / dosya
        if not kanca.is_file():
            satirlar.append(f"  [ ? ] {ad}: koruma dosyası yok")
            continue

        karar, aciklama = korumaya_sor(kanca, arac, girdiler)

        if karar == "deny":
            engelleyen.append(ad)
            satirlar.append(f"  [DUR] {ad}: {KARAR_ETIKETLERI['deny']}")
        elif karar == "ask":
            onay_isteyen.append(ad)
            satirlar.append(f"  [ ! ] {ad}: {KARAR_ETIKETLERI['ask']}")
        elif karar == "hata":
            satirlar.append(f"  [ x ] {ad}: {aciklama}")
        else:
            satirlar.append(f"  [ok ] {ad}: engel yok")

        if aciklama and karar in ("deny", "ask"):
            satirlar.append("")
            satirlar += [f"        {s}" for s in aciklama.splitlines()]
            satirlar.append("")

    satirlar += ["", "-" * 52, ""]

    if engelleyen:
        satirlar.append(f"SONUÇ: Komut ENGELLENİR. ({', '.join(engelleyen)})")
        kod = 2
    elif onay_isteyen:
        satirlar.append(f"SONUÇ: Komut ONAY İSTER. ({', '.join(onay_isteyen)})")
        kod = 1
    else:
        satirlar.append("SONUÇ: Komut engel görmez, çalışır.")
        kod = 0

    satirlar.append("")
    return "\n".join(satirlar), kod


def main():
    ayristirici = argparse.ArgumentParser(
        description="Komutu çalıştırmadan ne olacağını gösterir")
    ayristirici.add_argument("komut", nargs="?", help="Denenecek kabuk komutu")
    ayristirici.add_argument("--arac", default="Bash",
                             help="Bash, Write, Edit veya Read")
    ayristirici.add_argument("--dosya", help="Write/Edit/Read için dosya yolu")
    ayristirici.add_argument("--icerik", help="Write/Edit için yazılacak içerik")

    args = ayristirici.parse_args()

    if args.arac == "Bash":
        if not args.komut:
            ayristirici.error("Bash için komut vermelisin.")
        girdiler = {"command": args.komut}
    else:
        if not args.dosya:
            ayristirici.error(f"{args.arac} için --dosya vermelisin.")
        girdiler = {"file_path": args.dosya}
        if args.icerik:
            girdiler["content"] = args.icerik

    metin, kod = rapor(args.arac, girdiler)
    print(metin)
    return kod


if __name__ == "__main__":
    sys.exit(main())
