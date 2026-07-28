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
import shutil
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

# Pazar yerinden kurulan kopyanın kaydı. Çalışan eklenti çoğu makinede
# BURADAKİ kopyadır; depo klonu yalnız geliştirme makinesinde canlıdır.
KURULU_EKLENTILER = Path.home() / ".claude" / "plugins" / "installed_plugins.json"

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


def plugin_manifesti():
    """Çalışan kopyanın plugin.json'u.

    İki farklı düzen var ve sabit bir derinlik ikisini birden tutmuyor:

      depo klonu        <depo>/plugins/enver-framework/scripts/guncelleme.py
                        manifest: <depo>/plugins/enver-framework/.claude-plugin/
      pazar yerinden    <onbellek>/enver-framework/<surum>/scripts/guncelleme.py
                        manifest: <onbellek>/enver-framework/<surum>/.claude-plugin/

    Eskiden yol `parents[2]` ile sabitlenmişti. Depoda doğruydu; pazar
    yerinden kurulumda bir seviye şaşıyor ve dosya bulunamıyordu. Sonuç
    sessiz ve tehlikeliydi: sürüm None okunuyor, karşılaştırma anlamını
    yitiriyor, `var_mi` hiçbir zaman doğru olamıyordu. Yani kurulu kopya
    aylarca geride kalsa da güncelleme bildirimi ÇIKMAZDI.

    Artık derinlik varsayılmaz; yukarı doğru ilk manifest aranır.
    """
    for ata in Path(__file__).resolve().parents:
        yol = ata / ".claude-plugin" / "plugin.json"
        if yol.is_file():
            return yol
    return None


def yerel_surum():
    """Çalışan çerçevenin sürümü."""
    yol = plugin_manifesti()
    return _surum_ayikla(yol.read_text(encoding="utf-8")) if yol else None


def eklenti_adi():
    """Manifestteki eklenti adı. Kurulu kopyayı ararken kullanılır."""
    yol = plugin_manifesti()
    if not yol:
        return None
    try:
        return json.loads(yol.read_text(encoding="utf-8")).get("name")
    except (OSError, json.JSONDecodeError):
        return None


def kurulu_eklenti():
    """Pazar yerinden kurulu kopyanın kaydı. Yoksa None.

    Çoğu makinede ÇALIŞAN kopya budur; depo klonu yalnız geliştirme
    makinesinde canlıdır. Depoyu güncellemek bu kopyayı yenilemez -
    onu ayrıca `claude plugin update` tazeler.
    """
    ad = eklenti_adi()
    if not ad:
        return None

    veri = _guvenli_oku(KURULU_EKLENTILER)
    for anahtar, kayitlar in (veri.get("plugins") or {}).items():
        if anahtar.split("@")[0] != ad:
            continue
        for kayit in kayitlar or []:
            return {
                "anahtar": anahtar,
                "pazar_yeri": anahtar.split("@")[-1],
                "surum": kayit.get("version"),
                "yol": kayit.get("installPath"),
            }
    return None


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
    #
    # Önbellekten dönerken YEREL sürüm yeniden ölçülür. Eskiden kayıtlı
    # değer olduğu gibi dönüyordu: güncelleme yapıldıktan sonra bile
    # "GÜNCELLEME VAR" yazmaya devam ediyordu, çünkü önbellek bir gün
    # boyunca eski yerel sürümü hatırlıyordu. Kullanıcı da güncellemenin
    # işe yaramadığını sanıyordu.
    #
    # Ağ gerektiren şey UZAK sürümdür; yerel sürüm anında okunabilir.
    # Ölçülebilen bir şey önbellekten okunmaz.
    if not zorla and onceki.get("son_kontrol"):
        try:
            son = datetime.fromisoformat(onceki["son_kontrol"])
            yerel = yerel_surum()

            # Yerel sürüm önbellek yazıldığından beri DEĞİŞTİYSE güncelleme
            # yapılmış demektir; o zaman kayıtlı uzak sürüm de eskimiş
            # olabilir ve yeni bir yayını bir gün boyunca kaçırırız.
            # Böyle bir durumda önbellek atlanır, ağa bir kez bakılır.
            #
            # Bu, iki yönlü hatayı da kapatır: güncelledikten sonra
            # "güncelleme var" demeye devam etmek (yanlış uyarı) ve yeni
            # sürümü hiç söylememek (sessiz kalma).
            yerel_degisti = onceki.get("yerel") != yerel

            if simdi - son < YOKLAMA_ARALIGI and not yerel_degisti:
                uzak = onceki.get("uzak")
                var_mi = bool(uzak and yerel
                              and _surum_tuple(uzak) > _surum_tuple(yerel))
                return {
                    "var_mi": var_mi,
                    "yerel": yerel,
                    "uzak": uzak,
                    "degisiklikler": onceki.get("degisiklikler") if var_mi else [],
                }
        except ValueError:
            pass

    sonuc = _canli_kontrol(kaynak)
    if sonuc is None:
        # Ağ yok: eski önbellekteki UZAK sürüm kullanılır, ama karar
        # yeniden verilir. Kayıtlı kararı olduğu gibi döndürmek, güncelleme
        # yapıldıktan sonra ağ da yoksa "GÜNCELLEME VAR" demeyi sürdürürdü.
        if onceki.get("son_kontrol"):
            uzak = onceki.get("uzak")
            yerel = yerel_surum()
            var_mi = bool(uzak and yerel
                          and _surum_tuple(uzak) > _surum_tuple(yerel))
            return {
                "var_mi": var_mi,
                "yerel": yerel,
                "uzak": uzak,
                "degisiklikler": onceki.get("degisiklikler") if var_mi else [],
            }
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


def pazar_geride_mi():
    """Pazar yerinden kurulu kopya, çalışan koddan eski mi?

    İki sürüm ayrı yaşayabiliyor: depo klonu güncellenir ama çalışan
    eklenti pazar yeri önbelleğinde eski kalır. Bunu ölçen bir şey yoktu;
    fark günlerce görünmedi.
    """
    kurulu = kurulu_eklenti()
    if not kurulu or not kurulu.get("surum"):
        return None
    yerel = yerel_surum()
    if not yerel:
        return None
    if _surum_tuple(kurulu["surum"]) >= _surum_tuple(yerel):
        return None
    return {"kurulu": kurulu["surum"], "calisan": yerel,
            "anahtar": kurulu["anahtar"]}


def banner():
    """Açılış brifingine eklenecek kısa bildirim. Güncelleme yoksa boş."""
    try:
        durum = kontrol()
        geride = pazar_geride_mi()
    except Exception:
        return ""

    if geride and not (durum and durum.get("var_mi")):
        return ("PAZAR YERI KOPYASI GERIDE: "
                f"{geride['kurulu']} → {geride['calisan']}\n"
                "  Calisan eklenti eski surumde. Tek komut:  /guncelle")

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


def guncelleme_yolu():
    """Bu makinede güncelleme hangi yoldan yapılmalı?

    'pazar' — eklenti pazar yerinden kurulmuş. Çalışan kopya önbellekte
              durur; onu yalnız `claude plugin update` tazeler.
    'klon'  — çerçeve depo klonundan kurulmuş; git pull + kurulum.

    Ayrım şart: pazar yerinden kurulu bir makinede klon kurulumunu da
    çalıştırmak `~/.claude/plugins/` altına İKİNCİ, paralel bir kurulum
    bırakır. İki kopya aynı komutları ve kancaları taşır; hangisinin
    canlı olduğu belirsizleşir. Üstelik klon, herkese açık depo değil
    özel geliştirme deposu olabilir - o zaman kurulum, paylaşılmaması
    gereken bir kopyayı yayar.
    """
    return "pazar" if kurulu_eklenti() else "klon"


def komut_yap():
    """Güncellemeyi uygula.

    Pazar yerinden kurulu makinede yalnız o kopya tazelenir. Depo
    klonundan kurulu makinede git pull + kurulum çalışır. Sonunda
    '/reload-plugins' gerekir - onu yapan istemci (Claude Code), bu betik
    değil, o yüzden yalnız hatırlatılır.
    """
    if guncelleme_yolu() == "pazar":
        kurulu = kurulu_eklenti()
        print(f"Kurulum kaynagi: pazar yeri ({kurulu['anahtar']})")
        print(f"Kurulu surum   : {kurulu['surum']}")
        print()
        sonuc = pazar_yerini_tazele()
        if sonuc == "elle":
            return 1
        try:
            DURUM_DOSYASI.unlink()
        except OSError:
            pass
        print()
        print("Guncelleme tamam. Son adim (bunu sen calistir): /reload-plugins")
        print("Depo klonuna dokunulmadi; pazar yerinden kurulu kopya tazelendi.")
        return 0

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
    if sonuc.returncode != 0:
        print("Kurulum hata verdi. Yukarıdaki çıktıya bak.")
        return 1

    # Yeni sürüm kuruldu; önbelleği temizle ki banner bir daha çıkmasın.
    try:
        DURUM_DOSYASI.unlink()
    except OSError:
        pass

    print("Güncelleme tamam. Son adım (bunu sen çalıştır): /reload-plugins")
    return 0


def pazar_yerini_tazele():
    """Pazar yerinden kurulu kopyayı da yenile.

    Depoyu çekmek ve kurulumu koşturmak `~/.claude/plugins/` altına yazar.
    Ama eklenti pazar yerinden kurulduysa ÇALIŞAN kopya orası değil,
    `~/.claude/plugins/cache/<eklenti>/<surum>/` altındaki kopyadır.
    Bu adım olmadan güncelleme "bitti" der, kullanıcı eski sürümde kalır -
    tam olarak böyle oldu: depo günlerce 3.3.4 iken çalışan eklenti
    3.2.9'da kaldı ve hiçbir şey haber vermedi.

    Dönüş: 'yapildi' | 'elle' | 'yok'
    """
    kurulu = kurulu_eklenti()
    if not kurulu:
        return "yok"

    print()
    print(f"[3/3] Pazar yeri kopyasi yenileniyor ({kurulu['surum']})...")

    claude = shutil.which("claude")
    if not claude:
        print("  'claude' komutu bulunamadi. Elle:")
        print(f"    claude plugin marketplace update {kurulu['pazar_yeri']}")
        print(f"    claude plugin update {kurulu['anahtar']}")
        return "elle"

    for arg in (["plugin", "marketplace", "update", kurulu["pazar_yeri"]],
                ["plugin", "update", kurulu["anahtar"]]):
        try:
            sonuc = subprocess.run([claude, *arg], timeout=180,
                                   capture_output=True, text=True,
                                   encoding="utf-8", errors="replace")
        except (OSError, subprocess.TimeoutExpired) as hata:
            print(f"  Calistirilamadi: {hata}")
            return "elle"
        if sonuc.returncode != 0:
            print(f"  Hata: {(sonuc.stderr or sonuc.stdout).strip()[:200]}")
            return "elle"
        son_satir = [s for s in (sonuc.stdout or "").splitlines() if s.strip()]
        if son_satir:
            print("  " + son_satir[-1].strip())

    return "yapildi"


def komut_kontrol():
    durum = kontrol(zorla=True)

    # Kurulu kopya ayrıca yazılır. "Çerçeve güncel" demek yetmiyordu:
    # o cümle depo klonunu anlatıyor, kullanıcının çalıştırdığı kopyayı
    # değil. İkisi ayrı sürümde olabilir ve tam olarak öyle oldu.
    kurulu = kurulu_eklenti()
    if kurulu:
        print(f"Pazar yeri kopyasi : {kurulu['surum']}  ({kurulu['anahtar']})")
    print(f"Calisan kod        : {yerel_surum()}")

    geride = pazar_geride_mi()
    if geride:
        print("UYARI: Calisan eklenti geride. Tazelemek icin: /guncelle")

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
