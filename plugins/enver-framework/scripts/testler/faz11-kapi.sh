#!/usr/bin/env bash
# Faz 11 kapı kontrolü - cihaza göre tasarım (E20)

KOK="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && { pwd -W 2>/dev/null || pwd; })}"
P="$KOK/plugins/enver-framework"
T="$P/scripts/tasarim"
cd "$KOK" || exit 1
mkdir -p _calisma

GECEN=0; KALAN=0
kontrol() {
  if [ "$2" -eq 0 ]; then echo "  [GECTI ] $1"; GECEN=$((GECEN+1));
  else echo "  [KALDI ] $1"; KALAN=$((KALAN+1)); fi
}

YOL_EKLE='import sys
for d in ("tasarim","ortak","hafiza"):
    sys.path.insert(0, f"plugins/enver-framework/scripts/{d}")'

echo "============================================"
echo " FAZ 11 KAPI KONTROLU - Cihaza gore tasarim"
echo "============================================"
echo ""

echo "--- 1. BETIK ---"
[ -f "$T/cihaz.py" ] && kontrol "tasarim/cihaz.py var" 0 || kontrol "tasarim/cihaz.py var" 1
python -c "import ast;ast.parse(open('$T/cihaz.py',encoding='utf-8').read())" 2>/dev/null \
  && kontrol "tasarim/cihaz.py sozdizimi gecerli" 0 || kontrol "tasarim/cihaz.py sozdizimi gecerli" 1

echo ""
echo "--- 2. CIHAZ SINIFLARI (E20) ---"
python - << PY 2>/dev/null && kontrol "Bes cihaz sinifi tanimli" 0 || kontrol "Bes cihaz sinifi tanimli" 1
$YOL_EKLE
import cihaz
adlar = [a for a, _, _, _, _ in cihaz.CIHAZ_SINIFLARI]
assert adlar == ["mobil", "buyuk-mobil", "tablet", "web", "masaustu"], adlar
PY

python - << PY 2>/dev/null && kontrol "Sinif araliklari bosluksuz ve ortusmesiz" 0 || kontrol "Sinif araliklari bosluksuz ve ortusmesiz" 1
$YOL_EKLE
import cihaz
sinirlar = [(alt, ust) for _, _, alt, ust, _ in cihaz.CIHAZ_SINIFLARI]
assert sinirlar[0][0] == 0, sinirlar
for sira in range(len(sinirlar) - 1):
    ust = sinirlar[sira][1]
    sonraki_alt = sinirlar[sira + 1][0]
    assert ust is not None and sonraki_alt == ust + 1, (sira, ust, sonraki_alt)
assert sinirlar[-1][1] is None, sinirlar
PY

python - << PY 2>/dev/null && kontrol "Genislikten sinif dogru bulunuyor" 0 || kontrol "Genislikten sinif dogru bulunuyor" 1
$YOL_EKLE
import cihaz
olcumler = [(320, "mobil"), (479, "mobil"), (480, "buyuk-mobil"),
            (768, "tablet"), (1023, "tablet"), (1024, "web"),
            (1439, "web"), (1440, "masaustu"), (2560, "masaustu")]
for genislik, beklenen in olcumler:
    anahtar, _ = cihaz.sinif_bul(genislik)
    assert anahtar == beklenen, (genislik, anahtar, beklenen)
PY

echo ""
echo "--- 3. CIHAZ KATMANI CSS ---"
python "$T/cihaz.py" css > _calisma/cihaz.css 2>/dev/null \
  && kontrol "CSS uretilebiliyor" 0 || kontrol "CSS uretilebiliyor" 1

for parca in "min-width: 480px" "min-width: 768px" "min-width: 1024px" "min-width: 1440px"; do
  grep -q "$parca" _calisma/cihaz.css \
    && kontrol "Kesme noktasi var: $parca" 0 || kontrol "Kesme noktasi var: $parca" 1
done

python - << 'PY' 2>/dev/null && kontrol "Cihazin kendisi de taniniyor" 0 || kontrol "Cihazin kendisi de taniniyor" 1
icerik = open("_calisma/cihaz.css", encoding="utf-8").read()
# Ekran genişliği tek ölçüt değil
for ozellik in ["hover: none", "pointer: coarse", "hover: hover", "pointer: fine",
                "orientation: landscape", "prefers-reduced-motion",
                "min-resolution"]:
    assert ozellik in icerik, ozellik
PY

python - << 'PY' 2>/dev/null && kontrol "Yatay kayma engelleniyor" 0 || kontrol "Yatay kayma engelleniyor" 1
icerik = open("_calisma/cihaz.css", encoding="utf-8").read()
assert "overflow-x: hidden" in icerik
assert "max-width: 100%" in icerik
PY

python - << 'PY' 2>/dev/null && kontrol "Dokunma hedefi ve okuma genisligi tanimli" 0 || kontrol "Dokunma hedefi ve okuma genisligi tanimli" 1
icerik = open("_calisma/cihaz.css", encoding="utf-8").read()
assert "--dokunma-hedefi: 44px" in icerik, "dokunma hedefi yok"
assert "--okuma-genisligi" in icerik
# Dokunmatikte hedef büyümeli
assert "--dokunma-hedefi: 48px" in icerik, "dokunmatikte hedef buyumuyor"
PY

python - << 'PY' 2>/dev/null && kontrol "Yazdirma katmani var" 0 || kontrol "Yazdirma katmani var" 1
icerik = open("_calisma/cihaz.css", encoding="utf-8").read()
assert "@media print" in icerik
PY

echo ""
echo "--- 4. SAYFA ISKELETI ---"
rm -rf _calisma/cihaz-iskelet 2>/dev/null
mkdir -p _calisma/cihaz-iskelet
python "$T/cihaz.py" iskelet --hedef _calisma/cihaz-iskelet/index.html > /dev/null 2>&1 \
  && kontrol "Iskelet uretilebiliyor" 0 || kontrol "Iskelet uretilebiliyor" 1
python "$T/cihaz.py" css --hedef _calisma/cihaz-iskelet/cihaz.css > /dev/null 2>&1

python - << 'PY' 2>/dev/null && kontrol "Iskelette goruntu alani etiketi var" 0 || kontrol "Iskelette goruntu alani etiketi var" 1
from pathlib import Path
icerik = Path("_calisma/cihaz-iskelet/index.html").read_text(encoding="utf-8")
assert 'name="viewport"' in icerik
assert "width=device-width" in icerik
assert 'lang="tr"' in icerik
PY

python "$T/cihaz.py" denetle _calisma/cihaz-iskelet 2>/dev/null | grep -q "sorunu bulunamadı" \
  && kontrol "Uretilen iskelet kendi denetiminden geciyor" 0 \
  || kontrol "Uretilen iskelet kendi denetiminden geciyor" 1

echo ""
echo "--- 5. CIHAZ UYUMU DENETIMI ---"
rm -rf _calisma/cihaz-kotu 2>/dev/null
mkdir -p _calisma/cihaz-kotu
python - << 'PY'
from pathlib import Path
k = Path("_calisma/cihaz-kotu")
(k / "k.html").write_text(
    '<!doctype html><html><head><title>X</title></head>'
    '<body><div>Icerik</div></body></html>', encoding="utf-8")
(k / "k.css").write_text(
    '.k { width: 1200px; height: 28px; font-size: 14px; }\n'
    '.m:hover { display: block; }\n'
    '.a { transition: all .3s; }\n', encoding="utf-8")
PY

python "$T/cihaz.py" denetle _calisma/cihaz-kotu > _calisma/cd.txt 2>&1
YUKSEK=$(grep -c "\[YÜKSEK\]" _calisma/cd.txt)
[ "$YUKSEK" -ge 3 ] && kontrol "Uyumsuz sayfada $YUKSEK yuksek bulgu" 0 \
                    || kontrol "Uyumsuz sayfada yeterli bulgu yok ($YUKSEK)" 1

for konu in "Görüntü alanı" "kesme noktası" "Sabit piksel"; do
  grep -qi "$konu" _calisma/cd.txt && kontrol "Yakalandi: $konu" 0 || kontrol "Yakalanmadi: $konu" 1
done

python - << PY 2>/dev/null && kontrol "Kesme noktasi sabit genislik sanilmiyor" 0 || kontrol "Kesme noktasi sabit genislik sanilmiyor" 1
$YOL_EKLE
import cihaz, re
desen = [d[3] for d in cihaz.DENETIMLER if d[0] == "sabit-genislik"][0]
# min-width ve max-width kesme noktasıdır, sabit genişlik değil
assert not desen.search("@media (min-width: 768px) {")
assert not desen.search(".k { max-width: 1320px; }")
# Ama sabit width yakalanmalı
assert desen.search(".k { width: 1200px; }")
PY

python - << PY 2>/dev/null && kontrol "Olcek kilidi yakalaniyor" 0 || kontrol "Olcek kilidi yakalaniyor" 1
$YOL_EKLE
import cihaz
desen = [d[3] for d in cihaz.DENETIMLER if d[0] == "olcek-kilitli"][0]
assert desen.search('<meta name="viewport" content="width=device-width, user-scalable=no">')
PY

python - << PY 2>/dev/null && kontrol "Bos klasorde 'uyumlu' denmiyor" 0 || kontrol "Bos klasorde 'uyumlu' denmiyor" 1
import subprocess, sys
from pathlib import Path
Path("_calisma/cihaz-bos").mkdir(parents=True, exist_ok=True)
p = subprocess.run([sys.executable, "plugins/enver-framework/scripts/tasarim/cihaz.py",
                    "denetle", "_calisma/cihaz-bos"],
                   capture_output=True, text=True, encoding="utf-8")
assert "bakılamadı" in p.stdout, p.stdout
PY

echo ""
echo "--- 6. BELGELEME ---"
grep -q "Cihaza göre tasarım" "$P/skills/ozgun-tasarim/SKILL.md" \
  && kontrol "Beceri cihaz katmanini anlatiyor" 0 || kontrol "Beceri cihaz katmanini anlatiyor" 1
grep -q "cihaz.py" "$P/commands/tasarim.md" \
  && kontrol "Komut cihaz betigini gosteriyor" 0 || kontrol "Komut cihaz betigini gosteriyor" 1
grep -q "küçültüp büyütmek yeterli değil" "$P/skills/ozgun-tasarim/SKILL.md" \
  && kontrol "Tek duzen yeterli degil kurali yazili" 0 || kontrol "Tek duzen yeterli degil kurali yazili" 1

echo ""
echo "--- 7. GERILEME TESTLERI ---"
if [ -n "$ENVER_GERILEME_ATLA" ]; then
  echo "  (gerileme testleri atlandi - ust testten cagrildi)"
else
export ENVER_GERILEME_ATLA=1
for f in 0 1 2 3 4 5 6 7 8 9 10; do
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
[ "$KALAN" -eq 0 ] && echo " FAZ 11 KAPISI ACIK" || echo " FAZ 11 KAPISI KAPALI"
