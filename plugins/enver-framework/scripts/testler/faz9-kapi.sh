#!/usr/bin/env bash
# Faz 9 kapı kontrolü - sektör ve veri araçları

KOK="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && { pwd -W 2>/dev/null || pwd; })}"
P="$KOK/plugins/enver-framework"
cd "$KOK" || exit 1
mkdir -p _calisma

GECEN=0; KALAN=0
kontrol() {
  if [ "$2" -eq 0 ]; then echo "  [GECTI ] $1"; GECEN=$((GECEN+1));
  else echo "  [KALDI ] $1"; KALAN=$((KALAN+1)); fi
}

YOL_EKLE='import sys
for d in ("saha","veri","plan","ortak","hafiza","sunucu","projeler","is"):
    sys.path.insert(0, f"plugins/enver-framework/scripts/{d}")'

echo "============================================"
echo " FAZ 9 KAPI KONTROLU - Sektor ve veri araclari"
echo "============================================"
echo ""

echo "--- 1. BETIK DOSYALARI ---"
for b in saha/envanter.py veri/toplu.py plan/kesif.py; do
  [ -f "$P/scripts/$b" ] && kontrol "scripts/$b var" 0 || kontrol "scripts/$b var" 1
  python -c "import ast;ast.parse(open('$P/scripts/$b',encoding='utf-8').read())" 2>/dev/null \
    && kontrol "scripts/$b sozdizimi gecerli" 0 || kontrol "scripts/$b sozdizimi gecerli" 1
done

echo ""
echo "--- 2. CIHAZ ENVANTERI (T68) ---"
python - << PY 2>/dev/null && kontrol "Cihaz eklenip okunabiliyor" 0 || kontrol "Cihaz eklenip okunabiliyor" 1
$YOL_EKLE
import envanter
c = envanter.ekle("Kapi testi kamerasi", "kamera", "Kapi Testi Musterisi",
                  konum="Giris", adres="192.168.1.50", model="Ornek")
assert c["no"] > 0 and c["durum"] == "calisiyor", c
PY

python - << PY 2>/dev/null && kontrol "Envantere PAROLA yazilamiyor" 0 || kontrol "Envantere PAROLA yazilamiyor" 1
$YOL_EKLE
import envanter, re
# Yasak alan deseni parola alanlarını yakalamalı
for alan in ("parola", "password", "sifre", "şifre", "secret"):
    assert envanter.YASAK_ALANLAR.match(alan), alan
# Normal alanlar serbest
for alan in ("adres", "model", "konum", "kasa_anahtari"):
    assert not envanter.YASAK_ALANLAR.match(alan), alan
PY

python - << PY 2>/dev/null && kontrol "Sir denetimi calisiyor" 0 || kontrol "Sir denetimi calisiyor" 1
$YOL_EKLE
import envanter
# Not alanına parola görünümlü içerik konursa yakalanmalı
veri = envanter.oku()
veri["cihazlar"].append({"no": 9999, "ad": "Sizinti testi", "tur": "kamera",
                         "musteri": "-", "not": "parola: CokGizli123",
                         "durum": "calisiyor", "kurulum": "2026-01-01"})
envanter.yaz(veri)
try:
    sorunlar = envanter.sir_denetle()
    assert any("9999" in s for s in sorunlar), sorunlar
finally:
    veri = envanter.oku()
    veri["cihazlar"] = [c for c in veri["cihazlar"] if c.get("no") != 9999]
    envanter.yaz(veri)
PY

python - << PY 2>/dev/null && kontrol "Bakim takibi hesaplaniyor" 0 || kontrol "Bakim takibi hesaplaniyor" 1
$YOL_EKLE
import envanter
from datetime import date, timedelta
eski = (date.today() - timedelta(days=400)).isoformat()
c = envanter.ekle("Bakimi gecmis cihaz", "kayit-cihazi", "Kapi Testi Musterisi",
                  kurulum=eski)
gerekenler = envanter.bakim_gerekenler()
assert any(g["no"] == c["no"] and g["gecikme"] > 0 for g in gerekenler), gerekenler
PY

python "$P/scripts/saha/envanter.py" liste --sinir 3 2>/dev/null | grep -q "CİHAZ ENVANTERİ" \
  && kontrol "Envanter listelenebiliyor" 0 || kontrol "Envanter listelenebiliyor" 1

echo ""
echo "--- 3. TOPLU DOSYA ISLEMI (T80) ---"
rm -rf _calisma/toplu-testi 2>/dev/null
mkdir -p _calisma/toplu-testi
python - << 'PY'
from pathlib import Path
k = Path("_calisma/toplu-testi")
for ad in ["Ürün Görseli 1.JPG", "ÖZEL rapor.PDF", "test  dosya.txt",
           "zaten-uygun.png", "Şirket Logosu.SVG"]:
    (k / ad).write_text("x", encoding="utf-8")
PY

python - << PY 2>/dev/null && kontrol "Sade ad donusumu dogru" 0 || kontrol "Sade ad donusumu dogru" 1
$YOL_EKLE
import toplu
assert toplu.sade_ad("Ürün Görseli 1.JPG") == "urun-gorseli-1.jpg", toplu.sade_ad("Ürün Görseli 1.JPG")
assert toplu.sade_ad("ÖZEL rapor.PDF") == "ozel-rapor.pdf"
assert toplu.sade_ad("zaten-uygun.png") == "zaten-uygun.png"
assert toplu.sade_ad("Şirket Logosu.SVG") == "sirket-logosu.svg"
PY

python - << PY 2>/dev/null && kontrol "Adlandirma plani uretiliyor" 0 || kontrol "Adlandirma plani uretiliyor" 1
$YOL_EKLE
import toplu
plan = toplu.adlandirma_plani("_calisma/toplu-testi")
assert len(plan) == 4, [(a.name, b.name) for a, b in plan]
# Zaten uygun olan plana girmemeli
assert not any(a.name == "zaten-uygun.png" for a, b in plan)
PY

python "$P/scripts/veri/toplu.py" adlandir _calisma/toplu-testi > _calisma/tp.txt 2>&1
grep -q "DENEME" _calisma/tp.txt \
  && kontrol "Onaysiz calistirma DENEME modunda" 0 || kontrol "Onaysiz calistirma DENEME modunda" 1

python - << PY 2>/dev/null && kontrol "Deneme modunda dosya DEGISMIYOR" 0 || kontrol "Deneme modunda dosya DEGISMIYOR" 1
from pathlib import Path
assert (Path("_calisma/toplu-testi") / "Ürün Görseli 1.JPG").exists(), "dosya degismis"
PY

python - << PY 2>/dev/null && kontrol "Ayni ada dusen dosyalar ayristiriliyor" 0 || kontrol "Ayni ada dusen dosyalar ayristiriliyor" 1
$YOL_EKLE
from pathlib import Path
import toplu
k = Path("_calisma/toplu-cakisma")
k.mkdir(parents=True, exist_ok=True)
for ad in ["Rapor.txt", "rapor.txt", "RAPOR.txt"]:
    try:
        (k / ad).write_text("x", encoding="utf-8")
    except OSError:
        pass
plan = toplu.adlandirma_plani(k)
hedefler = [b.name for a, b in plan]
assert len(hedefler) == len(set(hedefler)), hedefler
PY

python "$P/scripts/veri/toplu.py" listele _calisma/toplu-testi 2>/dev/null | grep -q "KLASÖR ÖZETİ" \
  && kontrol "Klasor ozeti uretiliyor" 0 || kontrol "Klasor ozeti uretiliyor" 1

echo ""
echo "--- 4. KESIF - PLANLAMA VE ARASTIRMA (E19) ---"
[ -f "$P/skills/proje-kesif/SKILL.md" ] && kontrol "proje-kesif becerisi var" 0 || kontrol "proje-kesif becerisi var" 1
[ -f "$P/commands/kesif.md" ] && kontrol "kesif komutu var" 0 || kontrol "kesif komutu var" 1

python - << PY 2>/dev/null && kontrol "Dort asama tanimli ve sirali" 0 || kontrol "Dort asama tanimli ve sirali" 1
$YOL_EKLE
import kesif
assert kesif.ASAMALAR == ["istek", "arastirma", "netlestirme", "plan"], kesif.ASAMALAR
for asama in kesif.ASAMALAR:
    assert kesif.SORULAR.get(asama), asama
    assert len(kesif.SORULAR[asama]) >= 5, (asama, len(kesif.SORULAR[asama]))
PY

python - << PY 2>/dev/null && kontrol "Bos asama ATLANAMIYOR" 0 || kontrol "Bos asama ATLANAMIYOR" 1
$YOL_EKLE
import kesif
kesif.baslat("kapi-testi-kesif", "Test")
veri, mesaj = kesif.ilerle("kapi-testi-kesif")
assert veri is None, "bos asama atlandi"
assert "atlanamaz" in mesaj.lower(), mesaj
PY

python - << PY 2>/dev/null && kontrol "Bulgu eklenince ilerlenebiliyor" 0 || kontrol "Bulgu eklenince ilerlenebiliyor" 1
$YOL_EKLE
import kesif
kesif.bulgu_ekle("Ornek istek", proje="kapi-testi-kesif")
veri, mesaj = kesif.ilerle("kapi-testi-kesif")
assert veri is not None and veri["asama"] == "arastirma", (veri, mesaj)
PY

python - << PY 2>/dev/null && kontrol "Kesif bitmeden KODLAMAYA GECILMEZ" 0 || kontrol "Kesif bitmeden KODLAMAYA GECILMEZ" 1
$YOL_EKLE
import kesif
hazir, mesaj = kesif.kodlamaya_hazir_mi("kapi-testi-kesif")
assert hazir is False, mesaj
assert "sürüyor" in mesaj.lower() or "suruyor" in mesaj.lower(), mesaj
PY

python - << PY 2>/dev/null && kontrol "Dort asama bitince kodlamaya gecilebiliyor" 0 || kontrol "Dort asama bitince kodlamaya gecilebiliyor" 1
$YOL_EKLE
import kesif
for asama in ("arastirma", "netlestirme", "plan"):
    kesif.bulgu_ekle(f"{asama} bulgusu", proje="kapi-testi-kesif")
    kesif.ilerle("kapi-testi-kesif")
hazir, mesaj = kesif.kodlamaya_hazir_mi("kapi-testi-kesif")
assert hazir is True, mesaj
PY

python - << PY 2>/dev/null && kontrol "Kesiften faz plani uretilebiliyor" 0 || kontrol "Kesiften faz plani uretilebiliyor" 1
import subprocess, sys
from pathlib import Path
p = subprocess.run([sys.executable, "plugins/enver-framework/scripts/plan/kesif.py",
                    "plana-dok", "--proje", "kapi-testi-kesif",
                    "--hedef", "_calisma/kesif-plani.md"],
                   capture_output=True, text=True, encoding="utf-8")
assert p.returncode == 0, p.stdout + p.stderr
icerik = Path("_calisma/kesif-plani.md").read_text(encoding="utf-8")
assert "Faz 1" in icerik and "Keşif özeti" in icerik, icerik[:300]
PY

grep -q "Asla varsayma\|varsayma" "$P/skills/proje-kesif/SKILL.md" \
  && kontrol "Beceri varsaymayi yasakliyor" 0 || kontrol "Beceri varsaymayi yasakliyor" 1

grep -q "KODLAMAYA GEÇİLMEZ" "$P/skills/proje-kesif/SKILL.md" \
  && kontrol "Beceri kodlama sinirini belirtiyor" 0 || kontrol "Beceri kodlama sinirini belirtiyor" 1

echo ""
echo "--- 5. GERILEME TESTLERI ---"
if [ -n "$ENVER_GERILEME_ATLA" ]; then
  echo "  (gerileme testleri atlandi - ust testten cagrildi)"
else
export ENVER_GERILEME_ATLA=1
for f in 0 1 2 3 4 5 6 7 8; do
  bash "$P/scripts/testler/faz$f-kapi.sh" "$KOK" > "_calisma/faz$f.txt" 2>&1
  grep -q " 0 kaldi" "_calisma/faz$f.txt" && kontrol "Faz $f hala gecerli" 0 \
    || { kontrol "Faz $f hala gecerli" 1; grep "KALDI" "_calisma/faz$f.txt" | head -4; }
done
unset ENVER_GERILEME_ATLA
fi

echo ""
echo "============================================"
echo " SONUC: $GECEN gecti, $KALAN kaldi"
echo "============================================"
[ "$KALAN" -eq 0 ] && echo " FAZ 9 KAPISI ACIK" || echo " FAZ 9 KAPISI KAPALI"
