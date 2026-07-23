#!/usr/bin/env python3
"""Komut rehberini otomatik üretir.

Komut, ajan, beceri ve kanca dosyalarını tarar; her birinin
başlığını ve açıklamasını çıkarıp tek bir rehber metni oluşturur.

Elle liste tutulmaz - dosyalar değişince rehber kendiliğinden güncellenir.

Geliştirici: Enver KOCAK
"""

import json
import re
import sys
from pathlib import Path

# Windows konsolu varsayılan olarak UTF-8 değil; Türkçe karakterler bozulmasın.
for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI / "ortak"))

import ayarlar  # noqa: E402
import metin  # noqa: E402

PLUGIN_KOK = SCRIPT_DIZINI.parent
FRAMEWORK_KOK = PLUGIN_KOK.parent.parent

# Üretilen dosyalar komut ya da ajan değildir; rehbere girmemeli.
# proje-index.py her klasöre İÇİNDEKİLER.md yazıyor ve bunlar
# commands/ ile agents/ altına da düşüyor.
URETILEN_DOSYALAR = {"ICINDEKILER.md", "INDEX.md"}


def uretilmis_mi(yol):
    return yol.name in URETILEN_DOSYALAR


# Komutların hangi kategoriye girdiği. Listede olmayan "Diğer"e düşer.
KATEGORILER = {
    "Genel": ["index", "panel", "framework-ayarlari"],
    "Süreç ve durum": ["durum-kaydet", "faz-kontrol", "proje-baslat"],
    "Kod ve depo": ["git-islemleri", "dokumantasyon", "temizlik", "toplu-islemler"],
    "Sunucu ve veri": ["db-yonetimi", "log-izle", "backup", "monitoring"],
    "Kontrol ve güvenlik": ["guvenlik-tara", "web-kontrol", "canli-kontrol"],
}


def on_bilgi_ayikla(icerik):
    """Markdown dosyasının başındaki YAML on bilgisini sözlük olarak döndür."""
    eslesme = re.match(r"^---\s*\n(.*?)\n---\s*\n", icerik, re.DOTALL)
    if not eslesme:
        return {}

    sonuc = {}
    for satir in eslesme.group(1).splitlines():
        if ":" in satir and not satir.startswith((" ", "-", "#")):
            ad, _, deger = satir.partition(":")
            sonuc[ad.strip()] = deger.strip().strip("\"'")
    return sonuc


def aciklama_bul(yol):
    """Dosyanın açıklamasını bul: önce on bilgi, sonra ilk anlamlı satır."""
    try:
        icerik = yol.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""

    on_bilgi = on_bilgi_ayikla(icerik)
    for anahtar in ("description", "aciklama"):
        if on_bilgi.get(anahtar):
            return on_bilgi[anahtar]

    govde = re.sub(r"^---\s*\n.*?\n---\s*\n", "", icerik, flags=re.DOTALL)
    for satir in govde.splitlines():
        temiz = satir.strip()
        if temiz and not temiz.startswith(("#", "`", "|", ">", "-", "*")):
            return temiz[:140]

    return ""


def kategori_bul(ad):
    for kategori, adlar in KATEGORILER.items():
        if ad in adlar:
            return kategori
    return "Diğer"


def komutlari_tara():
    dizin = PLUGIN_KOK / "commands"
    if not dizin.is_dir():
        return []

    return [
        {
            "ad": yol.stem,
            "aciklama": aciklama_bul(yol),
            "kategori": kategori_bul(yol.stem),
        }
        for yol in sorted(dizin.glob("*.md"))
        if not uretilmis_mi(yol)
    ]


def becerileri_tara():
    dizin = PLUGIN_KOK / "skills"
    if not dizin.is_dir():
        return []

    sonuc = []
    for beceri_dizini in sorted(dizin.iterdir()):
        dosya = beceri_dizini / "SKILL.md"
        if dosya.is_file():
            sonuc.append({
                "ad": beceri_dizini.name,
                "aciklama": aciklama_bul(dosya),
            })
    return sonuc


def ajanlari_tara():
    dizin = PLUGIN_KOK / "agents"
    if not dizin.is_dir():
        return []

    return [
        {"ad": yol.stem, "aciklama": aciklama_bul(yol)}
        for yol in sorted(dizin.glob("*.md"))
        if not uretilmis_mi(yol)
    ]


def kancalari_tara():
    dizin = PLUGIN_KOK / "hooks"
    if not dizin.is_dir():
        return []

    sonuc = []
    for yol in sorted(dizin.glob("*.py")):
        # Alt çizgiyle başlayanlar yardımcı modül, koruma değil
        if yol.name.startswith("_"):
            continue
        try:
            icerik = yol.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        belge = re.search(r'"""(.*?)"""', icerik, re.DOTALL)
        aciklama = ""
        if belge:
            satirlar = [s.strip() for s in belge.group(1).strip().splitlines() if s.strip()]
            if satirlar:
                aciklama = satirlar[0]
                if len(satirlar) > 1 and not aciklama.endswith("."):
                    aciklama = satirlar[1]

        sonuc.append({"ad": yol.name, "aciklama": aciklama})
    return sonuc


def rehber_uret():
    komutlar = komutlari_tara()
    beceriler = becerileri_tara()
    ajanlar = ajanlari_tara()
    kancalar = kancalari_tara()

    satirlar = [
        f"# {metin.al('index.baslik')}",
        "",
        f"_{metin.al('index.altbaslik')}_",
        "",
        f"**{metin.al('genel.gelistirici')}:** {ayarlar.kimlik_satiri()}",
        "",
        "---",
        "",
        f"## {metin.al('index.komutlar')} ({len(komutlar)})",
        "",
    ]

    sirali_kategoriler = list(KATEGORILER.keys()) + ["Diğer"]
    for kategori in sirali_kategoriler:
        grup = [k for k in komutlar if k["kategori"] == kategori]
        if not grup:
            continue

        satirlar += [
            f"### {kategori}",
            "",
            f"| Komut | {metin.al('index.aciklama')} |",
            "|-------|-----------|",
        ]
        satirlar += [f"| `/{k['ad']}` | {k['aciklama']} |" for k in grup]
        satirlar.append("")

    if beceriler:
        satirlar += [
            f"## Beceriler ({len(beceriler)})",
            "",
            f"| Beceri | {metin.al('index.aciklama')} |",
            "|--------|-----------|",
        ]
        satirlar += [f"| `{b['ad']}` | {b['aciklama']} |" for b in beceriler]
        satirlar.append("")

    if ajanlar:
        satirlar += [
            f"## {metin.al('index.ajanlar')} ({len(ajanlar)})",
            "",
            f"| Ajan | {metin.al('index.aciklama')} |",
            "|------|-----------|",
        ]
        satirlar += [f"| `{a['ad']}` | {a['aciklama']} |" for a in ajanlar]
        satirlar.append("")

    if kancalar:
        satirlar += [
            f"## {metin.al('index.korumalar')} ({len(kancalar)})",
            "",
            f"| Koruma | {metin.al('index.aciklama')} |",
            "|--------|-----------|",
        ]
        satirlar += [f"| `{k['ad']}` | {k['aciklama']} |" for k in kancalar]
        satirlar.append("")

    satirlar += [
        "---",
        "",
        f"**{metin.al('index.toplam')}:** {len(komutlar)} komut · {len(beceriler)} beceri · "
        f"{len(ajanlar)} ajan · {len(kancalar)} koruma",
        "",
    ]

    return "\n".join(satirlar)


def main():
    if "--json" in sys.argv:
        print(json.dumps({
            "komutlar": komutlari_tara(),
            "beceriler": becerileri_tara(),
            "ajanlar": ajanlari_tara(),
            "kancalar": kancalari_tara(),
        }, ensure_ascii=False, indent=2))
        return 0

    print(rehber_uret())
    return 0


if __name__ == "__main__":
    sys.exit(main())
