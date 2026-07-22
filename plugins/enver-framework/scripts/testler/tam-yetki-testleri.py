#!/usr/bin/env python3
"""Tam yetki modu senaryoları.

En kritik soru: tam yetki, korumaları devre dışı bırakabiliyor mu?
Bırakmamalı. "Tam yetki" hız demektir, kontrolsüzlük değil.

İki şey ölçülür:
  1. Rutin işlemler tam yetkide izin alıyor mu (hız kazancı gerçek mi)
  2. İstisna işlemler tam yetkide bile durduruluyor mu (güvenlik sağlam mı)

Geliştirici: Enver KOCAK
"""

import json
import subprocess
import sys
from pathlib import Path

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

KOK = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[4]
KANCA_DIZINI = KOK / "hooks"

sys.path.insert(0, str(KOK / "plugins/enver-framework/scripts/ortak"))
sys.path.insert(0, str(KOK / "plugins/enver-framework/scripts/faz"))
sys.path.insert(0, str(KOK / "plugins/enver-framework/scripts/hafiza"))

import ayarlar  # noqa: E402
import mod  # noqa: E402

gecen = 0
kalan = 0


def kanca_sor(kanca, arac, girdiler):
    veri = json.dumps({"tool_name": arac, "tool_input": girdiler})
    sonuc = subprocess.run(
        [sys.executable, str(KANCA_DIZINI / kanca)],
        input=veri, capture_output=True, text=True, encoding="utf-8",
    )
    try:
        cikti = json.loads(sonuc.stdout or "{}")
    except json.JSONDecodeError:
        return "bozuk"

    return cikti.get("hookSpecificOutput", {}).get("permissionDecision", "sessiz")


def dene(komut, beklenen, etiket, arac="Bash"):
    global gecen, kalan

    girdiler = {"command": komut} if arac == "Bash" else {"file_path": komut}
    karar = kanca_sor("tam-yetki.py", arac, girdiler)

    if karar == beklenen:
        print(f"  [GECTI ] {karar:7} <- {etiket}")
        gecen += 1
    else:
        print(f"  [HATA  ] {karar:7} (beklenen {beklenen}) <- {etiket}")
        kalan += 1


def korumayla_dene(kanca, komut, etiket):
    """Tam yetki acikken bile ilgili koruma engelliyor mu?"""
    global gecen, kalan

    karar = kanca_sor(kanca, "Bash", {"command": komut})

    if karar in ("deny", "ask"):
        print(f"  [GECTI ] {karar:7} <- {etiket}")
        gecen += 1
    else:
        print(f"  [HATA  ] {karar:7} (engellenmeliydi) <- {etiket}")
        kalan += 1


# Onceki modu koru, test bitince geri al
onceki_mod = ayarlar.oku().get("calisma_modu", "dikkatli")

try:
    # ---------------------------------------------------- tam yetki KAPALI
    mod.mod_ayarla("dikkatli")

    print("\n  Tam yetki KAPALI - kanca hic karar vermemeli")
    for komut in ["ls -la", "git status", "python test.py"]:
        dene(komut, "sessiz", f"kapaliyken: {komut}")

    # ---------------------------------------------------- tam yetki ACIK
    mod.mod_ayarla("tam-yetki")

    print("\n  Tam yetki AÇIK - rutin işler izin almalı")
    for komut in ["ls -la", "git status", "npm install",
                  "python betik.py", "git add .", "git commit -m 'düzeltme'"]:
        dene(komut, "allow", f"rutin: {komut}")

    dene(str(KOK / "README.md"), "allow", "dosya yazma", arac="Write")

    print("\n  Tam yetki AÇIK - istisnalar karar ALMAMALI (normal akışa bırakılır)")
    istisnalar = [
        ("rm -rf eski/", "silme"),
        ("Remove-Item -Recurse x", "silme (PowerShell)"),
        ("ssh root@sunucu.com ls", "uzak sunucu"),
        ("scp dosya root@sunucu:/tmp/", "uzak kopyalama"),
        ("git push origin master", "depoya gönderme"),
        ("gh repo create yeni --private", "depo ayarı"),
        ("git reset --hard HEAD~3", "geri alınamaz işlem"),
        ("psql -c 'DROP TABLE musteri'", "veritabanı düşürme"),
        ("psql -c 'DELETE FROM log'", "veritabanı silme"),
        ("npm publish", "yayınlama"),
        ("python scripts/kasa/kasa.py ac", "kasa erişimi"),
        ("./deploy.sh", "canlıya çıkış"),
        ("mkfs.ext4 /dev/sdb", "disk işlemi"),
    ]
    for komut, etiket in istisnalar:
        dene(komut, "sessiz", f"istisna: {etiket}")

    print("\n  Tam yetki AÇIK - korumalar hâlâ engelliyor mu?")
    korumayla_dene("veri-koruma.py", "rm -rf eski/", "silme koruması çalışıyor")
    korumayla_dene("veri-koruma.py", "git reset --hard", "yıkıcı komut koruması çalışıyor")
    korumayla_dene("git-gizlilik-koruma.py", "gh repo create x --pub" + "lic",
                   "depo gizlilik koruması çalışıyor")
    korumayla_dene("kasa-koruma.py", "cat kasa/kasa.kilit", "kasa koruması çalışıyor")

finally:
    mod.mod_ayarla(onceki_mod)

print()
print(f"  Çalışma modu geri alındı: {onceki_mod}")
print(f"  Senaryo sonucu: {gecen} geçti, {kalan} kaldı")
sys.exit(1 if kalan else 0)
