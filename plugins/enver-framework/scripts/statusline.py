#!/usr/bin/env python3
"""Durum satırı - ekranın altında sabit duran özet.

Gösterilenler:
    proje · makine · aktif faz · kasa durumu · kullanılan jeton

Makine adının görünmesi bilinçli: birden çok bilgisayarda çalışılıyor,
"hangi makinedeyim" sorusu her an cevaplı olmalı.

Girdi olarak oturum bilgisi bekler (standart girdiden JSON).
Bilgi gelmezse eksik alanlar sessizce atlanır - durum satırı asla hata vermez.

Geliştirici: Enver KOCAK
"""

import json
import os
import sys
import time
from pathlib import Path

SCRIPT_DIZINI = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIZINI / "ortak"))
sys.path.insert(0, str(SCRIPT_DIZINI / "hafiza"))
sys.path.insert(0, str(SCRIPT_DIZINI / "senkron"))

for akis in (sys.stdout, sys.stderr):
    if hasattr(akis, "reconfigure"):
        akis.reconfigure(encoding="utf-8", errors="replace")

AYIRAC = "  ·  "


def _oturum_bilgisi():
    """Standart girdiden oturum bilgisini oku."""
    if sys.stdin.isatty():
        return {}
    try:
        return json.loads(sys.stdin.read() or "{}")
    except (json.JSONDecodeError, ValueError):
        return {}


def _proje_koku(bilgi):
    calisma = (bilgi.get("workspace") or {}).get("project_dir")
    return calisma or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _proje_adi(kok):
    try:
        import yollar
        return yollar.proje_adi(yollar.proje_kok(kok))
    except Exception:
        return Path(kok).name


def _makine_adi(kok):
    try:
        import makine
        kayit = makine.bu_makine(kok)
        if kayit:
            return kayit.get("ad")
        return makine.kimlik().split("/")[0]
    except Exception:
        return None


def _aktif_faz(kok):
    """Aktif fazı MOTORUN kaydından oku.

    Eskiden bir belgedeki "Siradaki:" başlığı okunuyordu. Belge değişince
    gösterge sessizce boşaldı - faz planı belgede değil, motorun kaydında
    durur. Tek doğruluk kaynağı hafiza/faz-plani.json.
    """
    plan = Path(kok) / "hafiza" / "faz-plani.json"
    if not plan.is_file():
        return None

    try:
        veri = json.loads(plan.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None

    fazlar = veri.get("fazlar") or []
    for faz in fazlar:
        if faz.get("durum") in ("aktif", "devam", "basladi"):
            return f"Faz {faz.get('no')}: {faz.get('ad', '')}".strip()[:34]

    if fazlar and all(f.get("durum") == "tamamlandi" for f in fazlar):
        return f"{len(fazlar)} faz bitti"
    return None


def _kasa_durumu():
    """Kasa açık mı kilitli mi, kalan süre ne kadar."""
    oturum_yolu = Path.home() / ".claude" / "enver" / "kasa-oturum.json"
    if not oturum_yolu.is_file():
        return "kasa kilitli"

    try:
        veri = json.loads(oturum_yolu.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return "kasa kilitli"

    kalan = veri.get("bitis", 0) - time.time()
    if kalan <= 0:
        return "kasa kilitli"

    return f"kasa AÇIK ({int(kalan / 60)} dk)"


def _kisalt(sayi):
    """1390526 -> 1.4M, 311199 -> 311k"""
    if sayi >= 1_000_000:
        return f"{sayi / 1_000_000:.1f}M"
    if sayi >= 1_000:
        return f"{sayi / 1_000:.0f}k"
    return str(sayi)


def _jeton_sayaci(bilgi):
    """Oturumda kullanılan jeton ve şu anki bağlam doluluğu.

    NEDEN ÖNBELLEK OKUMASI SAYILMIYOR
    Her turda aynı bağlam önbellekten yeniden okunur; bu oturumda 74 milyon
    jetonluk okuma, 1,4 milyonluk gerçek tüketime karşılık geliyordu.
    "76M" yazan bir sayaç doğru değil, yanıltıcıdır - aynı içeriği tekrar
    tekrar sayar. Gösterilen sayı YENİ işlenen jetondur: girdi + önbelleğe
    yazılan + üretilen.

    Bağlam ayrı gösterilir: "ne kadar harcadım" ile "ne kadar doldu"
    farklı sorulardır.

    Sayım artımlıdır. Kayıt dosyası büyüyen bir günlüktür; her çizimde
    baştan okunsa durum satırı yavaşlar. Son okunan konum ve o ana kadarki
    toplam saklanır, yalnız yeni satırlar işlenir.
    """
    kayit = bilgi.get("transcript_path")
    if not kayit or not os.path.isfile(kayit):
        return None

    onbellek = Path.home() / ".claude" / "enver" / "jeton-sayaci.json"
    durum = {}
    try:
        durum = json.loads(onbellek.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass

    if durum.get("kayit") != kayit:
        durum = {"kayit": kayit, "konum": 0, "toplam": 0, "baglam": 0}

    try:
        boyut = os.path.getsize(kayit)
        # Dosya küçüldüyse (yeni oturum, aynı ad) baştan say
        if boyut < durum.get("konum", 0):
            durum = {"kayit": kayit, "konum": 0, "toplam": 0, "baglam": 0}

        with open(kayit, encoding="utf-8", errors="ignore") as dosya:
            dosya.seek(durum["konum"])
            for satir in dosya:
                try:
                    kutuk = json.loads(satir)
                except ValueError:
                    continue
                kullanim = (kutuk.get("message") or {}).get("usage")
                if not kullanim:
                    continue
                durum["toplam"] += (kullanim.get("input_tokens", 0)
                                    + kullanim.get("cache_creation_input_tokens", 0)
                                    + kullanim.get("output_tokens", 0))
                durum["baglam"] = (kullanim.get("input_tokens", 0)
                                   + kullanim.get("cache_read_input_tokens", 0)
                                   + kullanim.get("cache_creation_input_tokens", 0))
            durum["konum"] = dosya.tell()
    except OSError:
        return None

    try:
        onbellek.parent.mkdir(parents=True, exist_ok=True)
        onbellek.write_text(json.dumps(durum), encoding="utf-8")
    except OSError:
        pass

    if not durum["toplam"]:
        return None

    metin = f"{_kisalt(durum['toplam'])} jeton"
    if durum["baglam"]:
        metin += f" (bağlam {_kisalt(durum['baglam'])})"
    return metin


def _tam_yetki_acik_mi(kok):
    try:
        import ayarlar
        return bool(ayarlar.oku(kok).get("tam_yetki"))
    except Exception:
        return False


def main():
    bilgi = _oturum_bilgisi()
    kok = _proje_koku(bilgi)

    parcalar = [_proje_adi(kok)]

    makine_adi = _makine_adi(kok)
    if makine_adi:
        parcalar.append(makine_adi)

    faz = _aktif_faz(kok)
    if faz:
        parcalar.append(faz)

    parcalar.append(_kasa_durumu())

    if _tam_yetki_acik_mi(kok):
        parcalar.append("TAM YETKİ")

    jeton = _jeton_sayaci(bilgi)
    if jeton:
        parcalar.append(jeton)

    print(AYIRAC.join(p for p in parcalar if p))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Durum satırı hiçbir koşulda akışı bozmamalı
        print("Enver Framework")
        sys.exit(0)
