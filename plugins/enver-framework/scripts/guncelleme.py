#!/usr/bin/env python3
"""Güncelleme kontrolü - uzakta yeni sürüm var mı bakar.

Nasıl çalışır:
  1. Kurulumda kaydedilen klon dizinini bulur (~/.claude/enver/kurulum-bilgisi.json).
     Bulamazsa, çalışan çerçevenin kendisi bir depo mu diye yukarı doğru bakar.
  2. Günde en fazla bir kez uzak depoyu yoklar (git fetch). Sonuç önbelleğe
     yazılır; her oturumda ağ trafiği olmaz.
  3. Kurulu sürümü uzak sürümle karşılaştırır. Uzak daha yeniyse bildirir.

Hiçbir şeyi kendiliğinden güncellemez - sadece haber verir. Güncelleme
kullanıcının kararıdır: '/guncelle' ya da 'guncelleme.py yap'.

Ağ yoksa, klon bulunamazsa ya da git yoksa sessizce boş döner; oturum
açılışı asla tıkanmaz.

Geliştirici: Enver KOCAK
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

for _akis in (sys.stdout, sys.stderr):
    if hasattr(_akis, "reconfigure"):
        _akis.reconfigure(encoding="utf-8", errors="replace")

ENVER_DIZINI = Path.home() / ".claude" / "enver"
KURULUM_BILGISI = ENVER_DIZINI / "kurulum-bilgisi.json"
DURUM_DOSYASI = ENVER_DIZINI / "guncelle-durum.json"

# Günde bir kez yeter; daha sık yoklamak ağ trafiği demek.
YOKLAMA_ARALIGI = timedelta(hours=24)

# git fetch'in en fazla bekleyeceği süre. Ağ yavaşsa oturumu bekletmesin.
FETCH_ZAMAN_ASIMI = 8


def _guvenli_oku(yol):
    try:
        return json.loads(yol.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _git(kaynak, *arg, zaman_asimi=5):
    """Klon dizininde bir git komutu çalıştır. Hata olursa None döndür."""
    try:
        sonuc = subprocess.run(
            ["git", "-C", str(kaynak), *arg],
            capture_output=True, text=True, encoding="utf-8",
            timeout=zaman_asimi,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if sonuc.returncode != 0:
        return None
    return sonuc.stdout.strip()


def klon_dizini():
    """Depo klonunun yerini bul.

    Önce kurulumun kaydettiği yola bakar. Yoksa çalışan betiğin kendisi
    bir depo içinde mi diye yukarı çıkar (geliştirme düzeni için).
    """
    kayit = _guvenli_oku(KURULUM_BILGISI).get("kaynak_dizin")
    if kayit and (Path(kayit) / ".git").is_dir():
        return Path(kayit)

    # Geliştirme düzeni: betik zaten deponun içindeyse .git'i yukarıda bul.
    for ata in Path(__file__).resolve().parents:
        if (ata / ".git").is_dir():
            return ata
    return None


def _surum_ayikla(metin):
    """plugin.json metninden sürüm numarasını çek."""
    try:
        return json.loads(metin).get("version")
    except (json.JSONDecodeError, AttributeError):
        return None


def _surum_tuple(s):
    """'2.12.0' -> (2, 12, 0). Karşılaştırma için."""
    try:
        return tuple(int(p) for p in str(s).split("."))
    except (ValueError, AttributeError):
        return ()


def yerel_surum():
    """Çalışan çerçevenin sürümü."""
    yol = Path(__file__).resolve().parents[2] / ".claude-plugin" / "plugin.json"
    return _surum_ayikla(yol.read_text(encoding="utf-8")) if yol.is_file() else None


def _canli_kontrol(kaynak):
    """Uzağı yokla, kurulu sürümle karşılaştır. Ağ gerektirir."""
    # Fetch başarısızsa (ağ yok) sessizce çık.
    if _git(kaynak, "fetch", "--quiet", zaman_asimi=FETCH_ZAMAN_ASIMI) is None:
        return None

    ust = _git(kaynak, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if not ust:
        return None

    uzak_plugin = _git(kaynak, "show", f"{ust}:plugins/.claude-plugin/plugin.json")
    uzak = _surum_ayikla(uzak_plugin) if uzak_plugin else None
    yerel = yerel_surum()

    var_mi = bool(uzak and yerel and _surum_tuple(uzak) > _surum_tuple(yerel))

    # "Ne değişti": gelen commit başlıkları
    degisiklikler = []
    if var_mi:
        kayit = _git(kaynak, "log", "--format=%s", f"HEAD..{ust}")
        if kayit:
            degisiklikler = [s for s in kayit.splitlines() if s.strip()][:3]

    return {
        "var_mi": var_mi,
        "yerel": yerel,
        "uzak": uzak,
        "degisiklikler": degisiklikler,
    }


def kontrol(zorla=False):
    """Güncelleme durumu. Günde bir kez ağ yoklar, arası önbellekten okur.

    Dönüş: {var_mi, yerel, uzak, degisiklikler} ya da None (kontrol edilemedi).
    """
    kaynak = klon_dizini()
    if kaynak is None:
        return None

    onceki = _guvenli_oku(DURUM_DOSYASI)
    simdi = datetime.now()

    # Önbellek taze mi?
    if not zorla and onceki.get("son_kontrol"):
        try:
            son = datetime.fromisoformat(onceki["son_kontrol"])
            if simdi - son < YOKLAMA_ARALIGI:
                return {k: onceki.get(k) for k in
                        ("var_mi", "yerel", "uzak", "degisiklikler")}
        except ValueError:
            pass

    sonuc = _canli_kontrol(kaynak)
    if sonuc is None:
        # Ağ yok: eski önbellek varsa onu koru, yoksa sessiz.
        if onceki.get("son_kontrol"):
            return {k: onceki.get(k) for k in
                    ("var_mi", "yerel", "uzak", "degisiklikler")}
        return None

    # Sonucu önbelleğe yaz (zaman damgasıyla)
    try:
        ENVER_DIZINI.mkdir(parents=True, exist_ok=True)
        kayit = dict(sonuc)
        kayit["son_kontrol"] = simdi.isoformat(timespec="seconds")
        DURUM_DOSYASI.write_text(
            json.dumps(kayit, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass

    return sonuc


def banner():
    """Açılış brifingine eklenecek kısa bildirim. Güncelleme yoksa boş."""
    try:
        durum = kontrol()
    except Exception:
        return ""
    if not durum or not durum.get("var_mi"):
        return ""

    satirlar = [
        f"GÜNCELLEME VAR: {durum.get('yerel')} → {durum.get('uzak')}",
    ]
    degis = durum.get("degisiklikler") or []
    if degis:
        satirlar.append("  Ne değişti:")
        for d in degis:
            satirlar.append(f"    - {d}")
    satirlar.append("  Güncellemek için tek komut:  /guncelle")
    satirlar.append("  (Kapatmak istersen bu bildirimi yok say; bir şey bozulmaz.)")
    return "\n".join(satirlar)


def komut_yap():
    """Güncellemeyi uygula: git pull + kurulumu tekrar çalıştır.

    Baştan sona kendisi yürütür; kullanıcı tek komutla günceller. Sonunda
    '/reload-plugins' gerekir - onu yapan istemci (Claude Code), bu betik
    değil, o yüzden yalnız hatırlatılır.
    """
    kaynak = klon_dizini()
    if kaynak is None:
        print("Klon dizini bulunamadı. Elle güncelle:")
        print("  cd <framework klasörü> ; git pull ; ./guncelle.sh")
        return 1

    print(f"Kaynak: {kaynak}")
    print("[1/2] Depodan güncelleme alınıyor...")
    cikti = _git(kaynak, "pull", "--ff-only", zaman_asimi=60)
    if cikti is None:
        print("UYARI: Güncelleme alınamadı. Sebep genelde biri:")
        print("  - Ağ yok")
        print("  - Yerel değişiklik var (git durumunu kontrol et)")
        return 1
    print("  " + (cikti or "Zaten güncel."))

    print("[2/2] Dosyalar yenileniyor (kurulum)...")
    kurulum = kaynak / ("kurulum.ps1" if sys.platform == "win32" else "kurulum.sh")
    if not kurulum.is_file():
        print(f"Kurulum betiği bulunamadı: {kurulum}")
        return 1

    if sys.platform == "win32":
        cagri = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(kurulum)]
    else:
        cagri = ["bash", str(kurulum)]

    try:
        sonuc = subprocess.run(cagri, cwd=str(kaynak), timeout=180)
    except (OSError, subprocess.TimeoutExpired) as hata:
        print(f"Kurulum çalıştırılamadı: {hata}")
        return 1

    print()
    if sonuc.returncode == 0:
        # Yeni sürüm kuruldu; önbelleği temizle ki banner bir daha çıkmasın.
        try:
            DURUM_DOSYASI.unlink()
        except OSError:
            pass
        print("Güncelleme tamam. Son adım (bunu sen çalıştır): /reload-plugins")
        return 0

    print("Kurulum hata verdi. Yukarıdaki çıktıya bak.")
    return 1


def komut_kontrol():
    durum = kontrol(zorla=True)
    if durum is None:
        print("Güncelleme kontrol edilemedi (klon bulunamadı ya da ağ yok).")
        return 0
    if durum.get("var_mi"):
        print(f"Güncelleme var: {durum.get('yerel')} → {durum.get('uzak')}")
        for d in durum.get("degisiklikler") or []:
            print(f"  - {d}")
        print("Güncellemek için: /guncelle")
    else:
        print(f"Çerçeve güncel: {durum.get('yerel')}")
    return 0


def main():
    ayristirici = argparse.ArgumentParser(description="Güncelleme kontrolü")
    ayristirici.add_argument("komut", nargs="?", default="kontrol",
                             choices=["kontrol", "yap", "banner"])
    args = ayristirici.parse_args()

    if args.komut == "yap":
        return komut_yap()
    if args.komut == "banner":
        print(banner())
        return 0
    return komut_kontrol()


if __name__ == "__main__":
    sys.exit(main())
