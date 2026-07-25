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

# Yol MUTLAKLASTIRILIR: gorece yol verilirse (ornegin ".") ust dizin
# hesabi kayiyor ve deneme dosyalari ana dizine dusuyordu.
KOK = (Path(sys.argv[1]).resolve() if len(sys.argv) > 1
       else Path(__file__).resolve().parents[4])
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


print("\n  KOD YORUMUNDA iz - uyarmali")
# Kural 3.2.0'da daraltildi: yalniz yorum satirlari kapsam icinde.
dene("g1.py", "# Generated with Claude\nx = 1\n", True, "Python yorumu")
dene("g2.js", "// Copilot suggested this block\nlet x = 1;\n", True, "JavaScript yorumu")
dene("g3.php", "<?php\n# yapay zeka ile uretildi\n$x = 1;\n", True, "PHP diyez yorumu")
dene("g4.php", "<?php\n// ChatGPT ciktisi\n$x = 1;\n", True, "PHP cift egik yorum")
dene("g5.css", "/* GPT-4 ile uretilen stil */\n.a { color: red; }\n", True, "CSS blok yorumu")
dene("g6.html", "<!-- Co-Authored-By: Claude -->\n<p>merhaba</p>\n", True, "HTML yorumu")
dene("g7.sql", "-- LLM ciktisi\nSELECT 1;\n", True, "SQL yorumu")
dene("g8.py", "x = 1\n# yapay zeka notu\ny = 2\n", True, "kod arasinda yorum")

print("\n  YORUM DISI kullanim - artik sessiz kalmali")
# Belge, duz metin, dize degeri ve komut serbest. Eski kural bunlara
# otuyordu ve calismayi surekli kesiyordu.
dene("s1.md", "Bu belge yapay zeka ile hazirlandi.\n", False, "belge metni")
dene("s2.txt", "Co-Authored-By: Claude <x@y.z>\n", False, "duz metin dosyasi")
dene("s3.py", 'mesaj = "Claude ile uretildi"\n', False, "dize degeri")
dene("s4.json", '{"not": "yapay zeka ciktisi"}\n', False, "JSON alani (yorum yok)")
dene("s5.js", 'const ad = "ChatGPT";\n', False, "JavaScript dize degeri")
dene("s6.md", "# Baslik\n\nGPT-4 karsilastirmasi.\n", False, "belge basligi")

print("\n  Kurulumun kendisi - yorumda bile sessiz kalmali")
dene("m1.py", "# Kurulum: claude plugin install enver-framework\n",
     False, "yorumdaki kurulum komutu")
dene("m2.py", "# Ayar yolu: ~/.claude/settings.json\n", False, "yorumdaki yol")
dene("m3.sh", "# Kok: ${CLAUDE_PLUGIN_ROOT}/hooks\n", False, "yorumdaki ortam degiskeni")
dene("m4.py", "# Depo: D:/Projeler/enver-claude-framework\n", False, "yorumdaki mutlak yol")
dene("m5.md", "claude plugin marketplace add anthropics/claude-plugins-community\n",
     False, "belgede pazar yeri komutu")
dene("m6.js", "// Belge: https://code.claude.com/docs/en/plugins\n",
     False, "yorumdaki belge adresi")

print("\n  Muaf bicim ile gercek iz ayni yorumda - yine uyarmali")
dene("k1.py", "# claude plugin install x  (bu satir Claude tarafindan uretildi)\n",
     True, "yorumda komut + uretici ifadesi")
dene("k2.php", "<?php\n// D:/Projeler/x - Claude Code ile uretildi\n$x=1;\n",
     True, "yorumda yol + uretici ifadesi")

print("\n  Ilgisiz icerik - sessiz kalmali")
dene("i1.py", 'mesaj = "Islem tamamlandi"  # kullaniciya gosterilir\n',
     False, "siradan kod ve yorum")
dene("i2.md", "# Baslik\n\nMusteri siparis listesi.\n", False, "siradan belge")

print()
print(f"  Senaryo sonucu: {gecen} gecti, {kalan} kaldi")
sys.exit(1 if kalan else 0)
