#!/usr/bin/env python3
"""Koruma senaryoları - bütün kancaların davranışını tek yerden doğrular.

Test verileri bilinçli olarak bu dosyanın içinde tutulur. Kabuk komutuna
gömülürse korumalar test komutunun kendisini engelliyor.

Kullanım:
    python koruma-testleri.py [proje-kökü]

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

# Sunucu adresi ve korunan kök HARITADAN okunur; teste gömülmez.
# Bu dosya paylaşılan kopyada da bulunacağı için kişisel değer taşıyamaz.
def _harita():
    yol = KOK / "plugins" / "enver-framework" / "references" / "sunucu-haritasi.json"
    try:
        veri = json.loads(yol.read_text(encoding="utf-8"))
        sunucu = veri["sunucular"][0]
        # İzinli bir dizin de haritadan alınır; testte proje adı gömülmez
        izinli = sunucu["projeler"][0]["dizin"]
        return sunucu["adres"], veri["korunan_kok_dizinler"][0], izinli
    except (OSError, json.JSONDecodeError, KeyError, IndexError):
        return "0.0.0.0", "/var/www/vhosts/", "/var/www/vhosts/ornek.com/"


ADRES, VHOST, IZINLI_DIZIN = _harita()

gecen = 0
kalan = 0


def dene(kanca, arac, girdiler, beklenen, etiket):
    global gecen, kalan

    veri = json.dumps({"tool_name": arac, "tool_input": girdiler})
    sonuc = subprocess.run(
        [sys.executable, str(KANCA_DIZINI / kanca)],
        input=veri, capture_output=True, text=True, encoding="utf-8",
    )

    try:
        cikti = json.loads(sonuc.stdout or "{}")
    except json.JSONDecodeError:
        print(f"  [HATA  ] bozuk çıktı <- {etiket}")
        kalan += 1
        return

    ozel = cikti.get("hookSpecificOutput", {})
    karar = ozel.get("permissionDecision")

    if karar is None:
        karar = "uyari" if "additionalContext" in ozel else "gecti"

    if karar == beklenen:
        print(f"  [GECTI ] {karar:6} <- {etiket}")
        gecen += 1
    else:
        print(f"  [HATA  ] {karar:6} (beklenen {beklenen}) <- {etiket}")
        kalan += 1


def baslik(metin):
    print(f"\n  {metin}")


# ---------------------------------------------------------- veri koruması

baslik("Silme yasağı (E7)")
for komut in ["rm -rf eski/", "rmdir bos/", "del /f x.txt",
              "Remove-Item -Recurse eski", "git clean -fd",
              "find . -name '*.tmp' -delete", "shred gizli.txt"]:
    dene("veri-koruma.py", "Bash", {"command": komut}, "deny", f"silme: {komut[:34]}")

baslik("Yıkıcı komut kalkanı (T11)")
for komut in ["git reset --hard HEAD~3", "git push --force origin master",
              "psql -c 'DROP TABLE musteri'", "mysql -e 'TRUNCATE TABLE log'",
              "psql -c 'DELETE FROM kayit'", "chmod -R 777 /var/www"]:
    dene("veri-koruma.py", "Bash", {"command": komut}, "ask", f"yıkıcı: {komut[:34]}")

baslik("Zararsız komutlar geçmeli")
for komut in ["npm install", "git status", "ls -la", "chmod 755 x.sh",
              "psql -c 'DELETE FROM log WHERE tarih < now()'", "git commit -m 'form'"]:
    dene("veri-koruma.py", "Bash", {"command": komut}, "gecti", f"zararsız: {komut[:34]}")

baslik("Ana dizin düzeni (E7)")
dene("veri-koruma.py", "Write", {"file_path": str(KOK / "test-deneme.tmp")},
     "deny", "ana dizine geçici dosya")
dene("veri-koruma.py", "Write", {"file_path": str(KOK / "README.md")},
     "gecti", "ana dizine kalıcı dosya")
dene("veri-koruma.py", "Write", {"file_path": str(KOK / "_calisma" / "test-deneme.tmp")},
     "gecti", "çalışma alanına geçici dosya")

# ---------------------------------------------------------- kasa koruması

baslik("Kasa erişimi (E1)")
dene("kasa-koruma.py", "Read", {"file_path": str(KOK / "kasa" / "kasa.kilit")},
     "deny", "kasa dosyasını okuma")
dene("kasa-koruma.py", "Read", {"file_path": str(KOK / "vault" / "sunucu.md")},
     "deny", "düz metin kasa okuma")
dene("kasa-koruma.py", "Bash", {"command": "cat kasa/kasa.kilit"},
     "deny", "kasayı ekrana dökme")
dene("kasa-koruma.py", "Bash", {"command": "python scripts/kasa/kasa.py oku a.md"},
     "gecti", "kasa betiğiyle okuma")
dene("kasa-koruma.py", "Read", {"file_path": str(KOK / "README.md")},
     "gecti", "sıradan dosya okuma")

baslik("Sır sızıntısı (T12)")
dene("kasa-koruma.py", "Write",
     {"file_path": "ayar.py", "content": "ANAHTAR = 'sk-abcdefghij1234567890KLMNOPqrstuv'"},
     "deny", "gizli API anahtarı")
dene("kasa-koruma.py", "Write",
     {"file_path": "ayar.py", "content": "T = 'ghp_aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789'"},
     "deny", "depo erişim jetonu")
dene("kasa-koruma.py", "Write",
     {"file_path": "k.pem", "content": "-----BEGIN RSA PRIVATE KEY-----\nMIIE"},
     "deny", "özel anahtar bloğu")
dene("kasa-koruma.py", "Write",
     {"file_path": "db.php", "content": "$password = 'Hn3!kQ92zLmXpW4a';"},
     "deny", "koda gömülü parola")
dene("kasa-koruma.py", "Write",
     {"file_path": "ornek.env", "content": "API_KEY='degistirin-buraya'"},
     "gecti", "yer tutucu değer")
dene("kasa-koruma.py", "Write",
     {"file_path": "ayar.py", "content": "ANAHTAR = os.environ['API_KEY']"},
     "gecti", "ortam değişkeni")

# ---------------------------------------------------------- sunucu koruması

baslik("Müşteri sunucusu koruması (E3)")
dene("sunucu-koruma.py", "Bash",
     {"command": f"ssh root@{ADRES} 'rm -rf {VHOST}baska-musteri.com/'"},
     "deny", "başka müşteri dizini")
dene("sunucu-koruma.py", "Bash",
     {"command": f"scp x.zip root@{ADRES}:{VHOST}baska-musteri.com/httpdocs/"},
     "deny", "başka siteye kopyalama")
dene("sunucu-koruma.py", "Bash",
     {"command": f"ssh root@{ADRES} 'ls {IZINLI_DIZIN}'"},
     "gecti", "izinli proje dizini")
dene("sunucu-koruma.py", "Bash", {"command": f"scp log.txt root@{ADRES}:/tmp/"},
     "gecti", "ortak izinli dizin")
dene("sunucu-koruma.py", "Bash", {"command": "git status"},
     "gecti", "sunucuyla ilgisiz komut")

# ---------------------------------------------------------- depo gizliliği

baslik("Depo gizlilik kuralı")
dene("git-gizlilik-koruma.py", "Bash", {"command": "gh repo create yeni --pub" + "lic"},
     "deny", "herkese açık depo")
dene("git-gizlilik-koruma.py", "Bash", {"command": "gh repo create yeni"},
     "deny", "gizlilik bayrağı yok")
dene("git-gizlilik-koruma.py", "Bash", {"command": "gh repo create yeni --private"},
     "gecti", "gizli depo")

# ---------------------------------------------------------- sonuç

print()
print(f"  Senaryo sonucu: {gecen} geçti, {kalan} kaldı")
sys.exit(1 if kalan else 0)
