#!/usr/bin/env python3
"""Kurulum ve güncelleme betiği senaryoları.

Bu iki betik yalnız ilk günde değil, HER güncellemede çalışır. Sessizce
bozulurlarsa kullanıcı eski sürümde kalır ve bunu fark etmez. Ölçülenler:

  YARIDA KESİLME   Kaynakta olmayan bir klasör yüzünden kurulum durur.
                   Herkese açık sürümde kasa ve bilgi deposu YOKTUR;
                   koşulsuz kopyalama "set -e" ile kurulumu eklenti hiç
                   kopyalanmadan kesiyordu.
  SESSİZ KAYIP     Kullanıcının kendi kurallarını işlediği CLAUDE.md
                   yedeksiz eziliyordu.
  YANLIŞ DAL       Güncelleme sabit "origin master" çekiyordu; açık depo
                   "main" dalında, yani güncelleme hiç gelmiyordu.

Kurulum gerçekten çalıştırılır ama kum havuzunda: HOME geçici bir dizine
çevrilir, gerçek ~/.claude'a dokunulmaz.

Geliştirici: Enver KOCAK
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

for _akis in (sys.stdout, sys.stderr):
    if hasattr(_akis, "reconfigure"):
        _akis.reconfigure(encoding="utf-8", errors="replace")

KOK = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 \
    else Path(__file__).resolve().parents[4]

gecen = 0
kalan = 0


def olc(aciklama, kosul, ayrinti=""):
    global gecen, kalan
    if kosul:
        print(f"  [GECTI ] {aciklama}")
        gecen += 1
    else:
        print(f"  [HATA  ] {aciklama}" + (f" - {ayrinti}" if ayrinti else ""))
        kalan += 1
    return bool(kosul)


def _kabuk():
    """Çalışan bir bash bul. Yoksa canlı kurulum ölçülemez."""
    yol = shutil.which("bash")
    if not yol:
        return None
    try:
        sonuc = subprocess.run([yol, "-c", "echo tamam"],
                               capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return yol if sonuc.returncode == 0 else None


def _kum_kaynak(dizin, kurallar="yeni kurallar\n"):
    """Kurulumun kopyalayacağı sahte kaynak ağacı.

    Kasa (vault) ve bilgi deposu BİLEREK yok: herkese açık sürümdeki
    durum budur, ölçülmek istenen de tam bu.
    """
    kaynak = Path(dizin) / "kaynak"
    (kaynak / "sablonlar").mkdir(parents=True)
    (kaynak / "plugins" / "enver-framework" / "commands").mkdir(parents=True)
    (kaynak / "plugins" / ".claude-plugin").mkdir(parents=True)

    (kaynak / "CLAUDE.md").write_text(kurallar, encoding="utf-8")
    (kaynak / "sablonlar" / "ornek.md").write_text("sablon\n", encoding="utf-8")
    (kaynak / "plugins" / "enver-framework" / "commands" / "panel.md").write_text(
        "komut\n", encoding="utf-8")
    (kaynak / "plugins" / ".claude-plugin" / "marketplace.json").write_text(
        '{"name": "enver-framework"}\n', encoding="utf-8")

    shutil.copy2(KOK / "kurulum.sh", kaynak / "kurulum.sh")
    return kaynak


def _kur(bash, kaynak, ev):
    """Kurulumu kum havuzundaki HOME ile çalıştır."""
    ortam = dict(os.environ)
    # MSYS/Git Bash ters bölüyü yolda sevmez; ileri bölüye çevrilir.
    ortam["HOME"] = str(ev).replace("\\", "/")
    return subprocess.run([bash, str(kaynak / "kurulum.sh")],
                          cwd=str(kaynak), env=ortam,
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)


print("KURULUM VE GUNCELLEME SENARYOLARI")
print("-" * 52)

# ---------------------------------------------------------------- canlı kurulum

bash = _kabuk()

print("\n  Yarida kesilme - eksik klasor kurulumu durdurmamali")
if bash is None:
    print("  [ATLA  ] Calisan bash yok; canli kurulum olculemedi")
else:
    with tempfile.TemporaryDirectory() as gecici:
        kaynak = _kum_kaynak(gecici)
        ev = Path(gecici) / "ev"
        (ev / ".claude").mkdir(parents=True)

        sonuc = _kur(bash, kaynak, ev)
        hedef = ev / ".claude"

        olc("Kasa ve bilgi deposu yokken kurulum tamamlaniyor",
            sonuc.returncode == 0,
            f"cikis kodu {sonuc.returncode}: {sonuc.stderr.strip()[:120]}")
        olc("Eksik kaynak atlandi diye bildiriliyor",
            "atlandi" in sonuc.stdout)
        olc("Eklenti gercekten kopyalandi",
            (hedef / "plugins" / "enver-framework" / "commands" / "panel.md").is_file(),
            "kopyalama eksik klasorde kesilmis")
        olc("Pazar yeri dosyasi kopyalandi",
            (hedef / "plugins" / ".claude-plugin" / "marketplace.json").is_file())
        olc("Sablonlar kopyalandi",
            (hedef / "sablonlar" / "ornek.md").is_file())

    print("\n  Sessiz kayip - kullanicinin kurallari yedeksiz ezilmemeli")
    with tempfile.TemporaryDirectory() as gecici:
        kaynak = _kum_kaynak(gecici)
        ev = Path(gecici) / "ev"
        (ev / ".claude").mkdir(parents=True)

        eski = "benim kendi kurallarim\n"
        (ev / ".claude" / "CLAUDE.md").write_text(eski, encoding="utf-8")

        sonuc = _kur(bash, kaynak, ev)
        yedekler = sorted((ev / ".claude" / "enver" / "yedek").glob("CLAUDE.*.md")) \
            if (ev / ".claude" / "enver" / "yedek").is_dir() else []

        olc("Onceki CLAUDE.md yedeklendi", len(yedekler) == 1,
            f"{len(yedekler)} yedek bulundu")
        if yedekler:
            olc("Yedek ESKI icerigi tasiyor",
                yedekler[0].read_text(encoding="utf-8") == eski)
        olc("Yeni surum yerine gecti",
            (ev / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
            == "yeni kurallar\n")

    print("\n  Gereksiz yedek - ayni dosya icin cop uretilmemeli")
    with tempfile.TemporaryDirectory() as gecici:
        kaynak = _kum_kaynak(gecici)
        ev = Path(gecici) / "ev"
        (ev / ".claude").mkdir(parents=True)
        (ev / ".claude" / "CLAUDE.md").write_text("yeni kurallar\n", encoding="utf-8")

        _kur(bash, kaynak, ev)
        yedek_dizin = ev / ".claude" / "enver" / "yedek"
        yedekler = list(yedek_dizin.glob("CLAUDE.*.md")) if yedek_dizin.is_dir() else []

        olc("Icerik ayniysa yedek alinmiyor", not yedekler,
            f"{len(yedekler)} gereksiz yedek")

# --------------------------------------------------------- canlı kurulum (ps1)

# Windows tarafı ayrı bir betik; aynı davranışı orada da ölçmek gerekir.
# Metinde "yedek alıyor mu" diye bakmak yetmez, çalıştığı görülmeli.
if sys.platform == "win32":
    print("\n  Windows kurulumu - ayni davranis")
    kabuk = shutil.which("powershell") or shutil.which("pwsh")
    if kabuk is None:
        print("  [ATLA  ] PowerShell bulunamadi")
    else:
        with tempfile.TemporaryDirectory() as gecici:
            kaynak = _kum_kaynak(gecici)
            shutil.copy2(KOK / "kurulum.ps1", kaynak / "kurulum.ps1")
            ev = Path(gecici) / "ev"
            (ev / ".claude").mkdir(parents=True)

            eski = "benim kendi kurallarim\n"
            (ev / ".claude" / "CLAUDE.md").write_text(eski, encoding="utf-8")

            ortam = dict(os.environ)
            # Kurulum hedefi USERPROFILE'dan cozulur; kum havuzuna cevrilir.
            ortam["USERPROFILE"] = str(ev)

            sonuc = subprocess.run(
                [kabuk, "-ExecutionPolicy", "Bypass", "-File",
                 str(kaynak / "kurulum.ps1")],
                cwd=str(kaynak), env=ortam, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=180)

            yedek_dizin = ev / ".claude" / "enver" / "yedek"
            yedekler = sorted(yedek_dizin.glob("CLAUDE.*.md")) \
                if yedek_dizin.is_dir() else []

            olc("kurulum.ps1 eksik klasorde durmuyor", sonuc.returncode == 0,
                f"cikis kodu {sonuc.returncode}")
            olc("kurulum.ps1 eklentiyi kopyaliyor",
                (ev / ".claude" / "plugins" / "enver-framework" /
                 "commands" / "panel.md").is_file())
            olc("kurulum.ps1 onceki kurallari yedekliyor", len(yedekler) == 1,
                f"{len(yedekler)} yedek bulundu")
            if yedekler:
                olc("Yedek ESKI icerigi tasiyor (ps1)",
                    yedekler[0].read_text(encoding="utf-8").strip() == eski.strip())

# ------------------------------------------------------------ güncelleme betiği

print("\n  Yanlis dal - guncelleme sabit dal adi cekmemeli")

guncelle_sh = (KOK / "guncelle.sh").read_text(encoding="utf-8")

# Yalnız çalışan satırlar ölçülür. Açıklama satırında "origin master"
# geçmesi hata değil, o hatanın niye düzeltildiğinin anlatısıdır.
guncelle_kod = "\n".join(s for s in guncelle_sh.splitlines()
                         if not s.lstrip().startswith("#"))

olc("guncelle.sh sabit dal adi yazmiyor",
    "origin master" not in guncelle_kod and "origin main" not in guncelle_kod,
    "sabit dal adi var; farkli dalda calismaz")
olc("Takip edilen dal cekiliyor (--ff-only)",
    "git pull --ff-only" in guncelle_sh)
olc("Kopyalama listesi tekrarlanmiyor, kurulum cagriliyor",
    "kurulum.sh" in guncelle_sh and "$CLAUDE_DIR" not in guncelle_sh,
    "guncelle.sh kendi kopyalama listesini tutuyor; kurulumla ayrisir")

# ------------------------------------------------------------- iki taraf ayni

print("\n  Iki isletim sistemi ayni davranmali")

kurulum_sh = (KOK / "kurulum.sh").read_text(encoding="utf-8")
kurulum_ps1 = (KOK / "kurulum.ps1").read_text(encoding="utf-8")

olc("kurulum.sh eksik kaynagi atliyor", "atlandi (kaynak yok)" in kurulum_sh)
olc("kurulum.ps1 eksik kaynagi atliyor", "atlandi (kaynak yok)" in kurulum_ps1)
olc("kurulum.sh kurallari yedekliyor", "yedekle_kurallar" in kurulum_sh)
olc("kurulum.ps1 kurallari yedekliyor", "YedekleKurallar" in kurulum_ps1)

# Yedek, kopyalamadan ONCE calismali; sonra calisirsa yeni dosyayi yedekler.
olc("Yedek, uzerine yazmadan once aliniyor (sh)",
    kurulum_sh.index("yedekle_kurallar\n")
    < kurulum_sh.index('cp "$REPO_DIR/CLAUDE.md"'))
olc("Yedek, uzerine yazmadan once aliniyor (ps1)",
    kurulum_ps1.index("\nYedekleKurallar\n")
    < kurulum_ps1.index('Kopyala "Kurallar dosyasi"'))

# --------------------------------------------------------------------- belge

print("\n  Belge - eski surumden gecis yazili olmali")

for ad in ("KURULUM-KILAVUZU.md", "KURULUM-KILAVUZU.en.md"):
    metin = (KOK / ad).read_text(encoding="utf-8")
    olc(f"{ad} gecis bolumu iceriyor",
        "marketplace update" in metin and "kurulum-bilgisi.json" in metin)

print()
print(f"  Senaryo sonucu: {gecen} gecti, {kalan} kaldi")
sys.exit(1 if kalan else 0)
