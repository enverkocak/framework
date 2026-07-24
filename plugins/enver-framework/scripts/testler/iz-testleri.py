#!/usr/bin/env python3
"""Araç izi denetimi senaryoları.

Kancanın iki işi doğru yapması gerekiyor:
  1. Gerçek izi yakalamak - "üreten araç" bilgisi hiçbir yerde kalmaz
  2. Kurulumun kendisi olan kullanımları iz sanmamak

İkincisi birincisi kadar önemli: çerçeve bir eklenti, kurulum belgesinde
komutun, ayar yolunda dizinin, kancada ortam değişkeninin adı geçmek
zorunda. Bunlara öten bir denetim bir süre sonra hiç okunmaz - ve asıl
yakalaması gereken satırı da o gürültünün içinde kaçırır.

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
KANCA = KOK / "plugins" / "enver-framework" / "hooks" / "iz-kontrol.py"

# Depo kökünde .iz-muaf var; muafiyet işaretinin ULAŞAMAYACAĞI bir yer seçilir,
# yoksa kanca zaten sessiz kalır ve senaryolar bir şey ölçmez.
DENEME_DIZINI = Path(__file__).resolve().parents[5] / "_iz-denemeleri"
DENEME_DIZINI.mkdir(parents=True, exist_ok=True)

gecen = 0
kalan = 0


def dene(ad, icerik, uyari_bekleniyor, aciklama):
    global gecen, kalan

    yol = DENEME_DIZINI / ad
    yol.write_text(icerik, encoding="utf-8")

    veri = json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(yol)}})
    sonuc = subprocess.run(
        [sys.executable, str(KANCA)], input=veri,
        capture_output=True, text=True, encoding="utf-8",
    )

    try:
        cikti = json.loads(sonuc.stdout or "{}")
    except json.JSONDecodeError:
        print(f"  [HATA  ] bozuk çıktı <- {aciklama}")
        kalan += 1
        return

    uyardi = "additionalContext" in cikti.get("hookSpecificOutput", {})
    durum = "uyardı" if uyardi else "sessiz"

    if uyardi == uyari_bekleniyor:
        print(f"  [GECTI ] {durum:7} <- {aciklama}")
        gecen += 1
    else:
        print(f"  [HATA  ] {durum:7} (beklenen {'uyardı' if uyari_bekleniyor else 'sessiz'})"
              f" <- {aciklama}")
        kalan += 1


print("\n  Gerçek iz - uyarmalı")
dene("g1.py", "# Generated with Claude\nx = 1\n", True, "üretici satırı")
dene("g2.txt", "Co-Authored-By: Claude <noreply@anthropic.com>\n", True, "ortak yazar satırı")
dene("g3.md", "Bu belge yapay zeka ile hazırlandı.\n", True, "yapay zeka ifadesi")
dene("g4.py", "# ChatGPT ile üretilen yardımcı\n", True, "başka araç adı")
dene("g5.js", "// Copilot suggested this block\n", True, "Copilot")
dene("g6.md", "Model olarak GPT-4 kullanıldı.\n", True, "model adı")
dene("g7.py", "# LLM cikti ayristirici\n", True, "LLM kısaltması")

print("\n  Kurulumun kendisi - sessiz kalmalı")
dene("m1.md", "claude plugin install enver-framework@enver-framework\n",
     False, "kurulum komutu")
dene("m2.md", "claude plugin marketplace add anthropics/claude-plugins-community\n",
     False, "pazar yeri komutu + depo adı")
dene("m3.json", '{"komut": "python ${CLAUDE_PLUGIN_ROOT}/hooks/veri-koruma.py"}\n',
     False, "ortam değişkeni")
dene("m4.py", 'YOL = "~/.claude/vault/index.md"\n', False, "ayar dizini yolu")
dene("m5.md", "Kurallar CLAUDE.md dosyasına yazılır.\n", False, "kural dosyasının adı")
dene("m6.md", "Belge: https://code.claude.com/docs/en/plugins\n", False, "belge adresi")
dene("m7.md", "Onaylanınca @claude-community altında görünür.\n", False, "pazar yeri etiketi")
dene("m8.sh", 'curl -s https://raw.githubusercontent.com/anthropics/claude-plugins-community/main/x.json\n',
     False, "katalog adresi")

print("\n  Muaf biçim ile gerçek iz aynı satırda - yine uyarmalı")
dene("k1.md", "claude plugin install x  # bu satir Claude tarafindan uretildi\n",
     True, "komut + üretici ifadesi aynı satırda")

print("\n  İlgisiz içerik - sessiz kalmalı")
dene("i1.py", 'mesaj = "İşlem tamamlandı"\n', False, "sıradan Türkçe kod")
dene("i2.md", "# Başlık\n\nMüşteri sipariş listesi.\n", False, "sıradan belge")

print()
print(f"  Senaryo sonucu: {gecen} geçti, {kalan} kaldı")
sys.exit(1 if kalan else 0)
