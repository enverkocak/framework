#!/usr/bin/env python3
"""Türkçe yazım denetimi senaryoları.

Kancanın iki işi doğru yapması gerekiyor:
  1. Gerçek kural ihlallerini yakalamak
  2. Sözlük anahtarı, dosya adı gibi ASCII kalmak zorunda olan dizeleri
     kullanıcı metni sanıp gereksiz uyarı üretmemek

İkincisi birincisi kadar önemli: sürekli yanlış uyaran bir denetim
bir süre sonra hiç okunmaz.

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
KANCA = KOK / "plugins" / "enver-framework" / "hooks" / "yazim-kontrol.py"

# Muaf dizinlerin dışında bir yer seçilir, yoksa kanca zaten sessiz kalır
DENEME_DIZINI = KOK.parent / "_yazim-denemeleri"
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


print("\n  Kimlikte Türkçe karakter - uyarmalı")
dene("k1.py", "def kullanıcı_getir():\n    return 1\n", True, "fonksiyon adında ı")
dene("k2.py", "ödeme_tutarı = 100\n", True, "değişken adında ö ve ı")
dene("k3.js", "const müşteriListesi = [];\n", True, "değişken adında ü")

print("\n  Kimlik temiz - sessiz kalmalı")
dene("t1.py", 'def kullanici_getir():\n    """Kullanıcıyı getirir."""\n    return "Başarılı"\n',
     False, "ASCII kimlik, Türkçe belge metni")
dene("t2.js", "const musteriListesi = [];  // Müşteri listesi\n",
     False, "ASCII kimlik, Türkçe yorum")

print("\n  Arayüz metninde eksik Türkçe - uyarmalı")
dene("e1.html", "<button>Guncelle</button>\n", True, "düğme yazısı")
dene("e2.html", "<p>Sifrenizi giriniz</p>\n", True, "ekli kelime (Sifrenizi)")
dene("e3.py", 'mesaj = "Islem basarili oldu"\n', True, "dize içinde cümle")
dene("e4.md", "# Baslik\n\nKullanicilar listesi.\n", True, "belgede eksik yazım")

print("\n  Arayüz metni doğru - sessiz kalmalı")
dene("d1.html", "<button>Güncelle</button>\n<p>Şifrenizi giriniz</p>\n", False, "tam Türkçe arayüz")
dene("d2.py", 'mesaj = "İşlem başarılı oldu"\n', False, "tam Türkçe dize")
dene("d3.md", "# Başlık\n\nKullanıcı girişi yapıldı.\n", False, "tam Türkçe belge")

print("\n  Anahtar ve dosya adları - sessiz kalmalı (yanlış uyarı üretmemeli)")
dene("a1.py", 'deger = veri.get("aciklama")\nad = kayit["baslik"]\n',
     False, "sözlük anahtarı olarak aciklama/baslik")
dene("a2.py", 'DOSYA = "aciklamalar.json"\nYOL = "hafiza/durum.md"\n',
     False, "dosya adı ve yol")
dene("a3.py", 'alanlar = ["kullanici", "sifre", "musteri"]\n',
     False, "veri alanı adları listesi")
dene("a4.js", 'const t = { baslik: "x", aciklama: "y" };\n',
     False, "nesne alan adları")

print("\n  Komut ve yol içeren dizeler - sessiz kalmalı")
dene("c1.py", 'komut = "python hooks/oturum-kayit.py"\n', False, "betik çağrısı")
dene("c2.py", 'yol = "$CLAUDE_PROJECT_DIR/hooks/oturum-kayit.py"\n', False, "ortam değişkenli yol")
dene("c3.py", 'yedek = "komutlar-2026-07-21.jsonl"\n', False, "üretilen dosya adı")
dene("c4.json", '{"komut": "python hooks/oturum-kayit.py"}\n', False, "ayar dosyası")

print("\n  Yer tutucu ve tırnaklı alan adları - sessiz kalmalı")
dene("p1.py", 'print(f"Proje: {musteri} - {gorev}")\n', False, "biçimlendirme yer tutucusu")
dene("p2.py", 'print("Doldurulacak alanlar: `gorev`, `musteri`")\n', False, "ters tırnakta alan adı")
dene("p3.py", "print('Alan adı: kasa_anahtari')\n", False, "tek tırnakta alan adı")
dene("p4.py", 'print(f"Müşteri: {tanim.get(\'musteri\')}")\n', False, "yer tutucu içinde erişim")

print("\n  Yer tutucu dışındaki metin denetlenmeli")
dene("p5.py", 'print(f"Musteri bilgisi: {ad}")\n', True, "yer tutucu dışında eksik yazım")

print("\n  Düzenli ifade desenleri - sessiz kalmalı")
dene("r1.py", 'DESEN = r"pos\\b|odeme|payment"\n', False, "düzenli ifade deseni")
dene("r2.py", 'AYIR = re.compile(r"(?i)musteri|siparis")\n', False, "derlenen desen")

print("\n  Ünsüz yumuşaması - doğru yazım, sessiz kalmalı")
dene("u1.md", "Ölçüm sonucu belli oldu.\n", False, "sonuç + u = sonucu")
dene("u2.md", "İşlem sonucuna göre karar verildi.\n", False, "sonucuna")
dene("u3.md", "Kaydı sildik, sonuca ulaştık.\n", False, "sonuca")

print("\n  Kök hâlinde eksik yazım - hâlâ uyarmalı")
dene("u4.md", "Islem sonuc verdi.\n", True, "ekiz kök: sonuc")

print("\n  Türkçe büyük harf - doğru yazım, sessiz kalmalı")
dene("b1.md", "UYARI: İşlem tamamlanamadı.\n", False, "UYARI (ı büyüğü I)")
dene("b2.md", "KULLANICI GİRİŞİ\n", False, "KULLANICI (ı büyüğü I)")
dene("b3.md", "BAŞLIK ve AÇIKLAMA\n", False, "BAŞLIK, AÇIKLAMA")

print("\n  Büyük harfte eksik Türkçe - hâlâ uyarmalı")
dene("b4.md", "BASLIK ve ACIKLAMA\n", True, "BASLIK (ş eksik)")

print("\n  Yabancı dil - sessiz kalmalı")
dene("y1.html", "<p>Search the archive and select an item.</p>\n", False, "İngilizce metin")
dene("y2.py", 'komut = "git status --porcelain"\n', False, "kabuk komutu")

print()
print(f"  Senaryo sonucu: {gecen} geçti, {kalan} kaldı")
sys.exit(1 if kalan else 0)
