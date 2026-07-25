#!/usr/bin/env python3
"""PostToolUse kancası: Kod yorumlarında araç izi kontrolü.

KURAL (3.2.0'da daraltıldı)
Araç izi YALNIZ **kod yorum satırlarında** yasaktır. Belge, düz metin,
dize değeri, komut ve yol serbesttir.

Neden daraltıldı: eski kural dosyanın tamamını tarıyordu ve çalışmayı
sürekli kesiyordu - bir kurulum komutu, bir dosya yolu, bir belge cümlesi
uyarı üretiyordu. Sürekli yanlış öten bir denetim okunmaz hale gelir; asıl
yakalaması gereken satırı da o gürültünün içinde kaçırır.

Geriye kalan kural nettir ve savunulabilir: teslim edilen kaynak kodun
yorum satırlarında üretici izi bulunmaz. Yorum, kodu yazanın sesidir;
orada başka bir ad geçmez.

Geliştirici bilgisi her zaman: Enver KOCAK
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

# Kurulumun kendisi olan kullanımlar iz değildir.
#
# Çerçeve bir eklenti; kurulum belgesinde `claude plugin install`, ayar
# yolunda `~/.claude/settings.json`, kancada `${CLAUDE_PLUGIN_ROOT}` geçmek
# zorunda. Bunları iz sayan bir denetim her kurulum belgesinde öter, bir
# süre sonra da hiç okunmaz - asıl yakalaması gereken "generated with ..."
# satırını da o gürültünün içinde kaybeder.
#
# Muafiyet YALNIZ makine biçimlerini kapsar: yol, ortam değişkeni, komut,
# paket adı, adres. Düz metinde geçen ürün adı ("Claude Code ile üretildi")
# muaf DEĞİLDİR - asıl kural odur.
MUAF_BAGLAMLAR = [
    r"[\w./~-]*\.claude\b[\w./-]*",          # ~/.claude, .claude/settings.json
    r"\bclaude\.md\b",                        # CLAUDE.md - kural dosyasının adı
    r"\bCLAUDE_[A-Z0-9_]+\b",                 # ${CLAUDE_PLUGIN_ROOT}
    r"\bclaude[-_]plugins?[\w-]*",            # claude-plugin, claude-plugins-community
    r"\bclaude\s+plugins?\b",                 # `claude plugin install ...` komutu
    r"\bclaude[-_]code[-_][\w-]+",            # claude-code-plugin gibi etiketler
    r"\b[\w-]*\.?claude\.(?:ai|com)\b[\w./?=&#%-]*",   # claude.ai, code.claude.com
    r"\banthropics?\.com\b[\w./?=&#%-]*",
    r"\banthropics/[\w.-]+",                  # anthropics/claude-plugins-community
    r"@claude[-_][\w-]+",                     # @claude-community

    # Dosya yolu içindeki klasör adı. Çerçevenin çalışma deposu
    # "enver-claude-framework" adını taşıyor; her mutlak yol yazan betik
    # ve her kurulum belgesi bu adı geçirmek zorunda. Yol bir makine
    # biçimidir, iz değildir.
    #
    # Eşleşme için EĞİK ÇİZGİ şartı vardır: "claude" ya bir yol
    # parçasından sonra ya da öncesinde gelmeli. Böylece düz metindeki
    # ürün adı ("... ile üretildi") muafiyete giremez - aynı satırda yol
    # bulunsa bile, çünkü boşluk yol deseninde yer almaz.
    r"[\w.:~-]+[\\/][\w.:~\\/-]*claude[\w.:~\\/-]*",   # D:/Projeler/enver-claude-...
    r"[\w.:~-]*claude[\w.:~-]*[\\/][\w.:~\\/-]*",      # enver-claude-framework/plugins
]

MUAF_BAGLAM_DESENI = re.compile("|".join(MUAF_BAGLAMLAR), re.IGNORECASE)

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


# Hangi uzantıda yorum nasıl yazılır.
# ( satır yorumu işaretleri , blok yorumu (başlangıç, bitiş) çiftleri )
YORUM_BICIMLERI = {
    ".py": (("#",), ()),
    ".sh": (("#",), ()),
    ".bash": (("#",), ()),
    ".ps1": (("#",), (("<#", "#>"),)),
    ".rb": (("#",), ()),
    ".yml": (("#",), ()),
    ".yaml": (("#",), ()),
    ".toml": (("#",), ()),
    ".conf": (("#",), ()),
    ".ini": ((";", "#"), ()),
    ".sql": (("--",), (("/*", "*/"),)),
    ".js": (("//",), (("/*", "*/"),)),
    ".mjs": (("//",), (("/*", "*/"),)),
    ".cjs": (("//",), (("/*", "*/"),)),
    ".ts": (("//",), (("/*", "*/"),)),
    ".jsx": (("//",), (("/*", "*/"),)),
    ".tsx": (("//",), (("/*", "*/"),)),
    ".css": ((), (("/*", "*/"),)),
    ".scss": (("//",), (("/*", "*/"),)),
    ".php": (("//", "#"), (("/*", "*/"),)),
    ".c": (("//",), (("/*", "*/"),)),
    ".h": (("//",), (("/*", "*/"),)),
    ".cpp": (("//",), (("/*", "*/"),)),
    ".cs": (("//",), (("/*", "*/"),)),
    ".java": (("//",), (("/*", "*/"),)),
    ".go": (("//",), (("/*", "*/"),)),
    ".rs": (("//",), (("/*", "*/"),)),
    ".kt": (("//",), (("/*", "*/"),)),
    ".swift": (("//",), (("/*", "*/"),)),
    ".html": ((), (("<!--", "-->"),)),
    ".htm": ((), (("<!--", "-->"),)),
    ".xml": ((), (("<!--", "-->"),)),
    ".vue": (("//",), (("/*", "*/"), ("<!--", "-->"))),
}


def yorum_parcalari(icerik, uzanti):
    """Dosyadaki yorum metinlerini (satır numarasıyla) çıkar.

    Yalnız yorumlar döner. Dize değerleri, kodun kendisi ve düz metin
    dışarıda kalır - kural artık yalnız yorumları kapsıyor.

    Basit bir tarayıcıdır: dize içindeki `//` gibi durumları ayırt etmez.
    Bu yönde yanılırsa FAZLA yakalar, az değil; iz denetiminde güvenli
    taraf budur.
    """
    bicim = YORUM_BICIMLERI.get(uzanti)
    if not bicim:
        return []

    satir_isaretleri, blok_ciftleri = bicim
    parcalar = []
    acik_blok = None

    for numara, satir in enumerate(icerik.splitlines(), 1):
        kalan = satir

        while kalan:
            if acik_blok:
                bitis = acik_blok[1]
                yer = kalan.find(bitis)
                if yer == -1:
                    parcalar.append((numara, kalan, satir))
                    kalan = ""
                else:
                    parcalar.append((numara, kalan[:yer], satir))
                    kalan = kalan[yer + len(bitis):]
                    acik_blok = None
                continue

            # En yakın yorum başlangıcı hangisi?
            en_yakin = None
            for isaret in satir_isaretleri:
                yer = kalan.find(isaret)
                if yer != -1 and (en_yakin is None or yer < en_yakin[0]):
                    en_yakin = (yer, isaret, None)
            for cift in blok_ciftleri:
                yer = kalan.find(cift[0])
                if yer != -1 and (en_yakin is None or yer < en_yakin[0]):
                    en_yakin = (yer, cift[0], cift)

            if en_yakin is None:
                break

            yer, isaret, cift = en_yakin
            kalan = kalan[yer + len(isaret):]

            if cift is None:          # satır sonuna kadar yorum
                parcalar.append((numara, kalan, satir))
                kalan = ""
            else:                     # blok yorumu başladı
                acik_blok = cift

    return parcalar


def dosya_tara(dosya_yolu):
    """Dosyanın YORUM satırlarında iz ara, bulursa uyarı döndür."""
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
    yerler = []

    # YALNIZ yorumlara bakılır. Kodun kendisi, dize değerleri, belge metni
    # ve komutlar kapsam dışıdır - kural 3.2.0'da buraya daraltıldı.
    uzanti = os.path.splitext(dosya_yolu.lower())[1]

    # Muaf biçimler yorumdan çıkarıldıktan SONRA aranır: bir yorum kurulum
    # yolunu ya da komutunu anlatıyor olabilir, bu iz değildir.
    for numara, yorum, tam_satir in yorum_parcalari(icerik, uzanti):
        kalan = MUAF_BAGLAM_DESENI.sub(" ", yorum)

        for desen in IZ_DESENLERI:
            eslesme = re.search(desen, kalan, re.IGNORECASE)
            if eslesme:
                bulunanlar.append(eslesme.group())
                if len(yerler) < 5:
                    yerler.append(f"satir {numara}: {tam_satir.strip()[:80]}")
                break

    if not bulunanlar:
        return None

    mesaj = (
        "IZ BULUNDU - kod yorumunda arac adi geciyor\n"
        "\n"
        f"Dosya: {dosya_yolu}\n"
        f"Bulunan ifadeler: {', '.join(sorted(set(bulunanlar)))}\n"
    )

    if yerler:
        mesaj += "".join(f"  {yer}\n" for yer in yerler)

    mesaj += (
        "\n"
        "Kural: Kod YORUM satirlarinda arac izi bulunmaz.\n"
        "Gelistirici bilgisi: Enver KOCAK\n"
        "\n"
        "Belge, duz metin, dize degeri, komut ve yol SERBESTTIR; denetim\n"
        "onlara bakmaz. Uyari geldiyse ifade bir yorum satirindadir.\n"
        "\n"
        "Yorumu kendi sozlerinle yaz."
    )

    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": mesaj,
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
