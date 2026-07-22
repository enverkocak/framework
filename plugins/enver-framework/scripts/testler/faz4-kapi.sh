#!/usr/bin/env bash
# Faz 4 kapi kontrolu - projeler beyni ve sistem semasi

KOK="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && { pwd -W 2>/dev/null || pwd; })}"
P="$KOK/plugins/enver-framework"
cd "$KOK" || exit 1
mkdir -p _calisma

GECEN=0; KALAN=0
kontrol() {
  if [ "$2" -eq 0 ]; then echo "  [GECTI ] $1"; GECEN=$((GECEN+1));
  else echo "  [KALDI ] $1"; KALAN=$((KALAN+1)); fi
}

echo "============================================"
echo " FAZ 4 KAPI KONTROLU - Projeler beyni"
echo "============================================"
echo ""

echo "--- 1. BETIK DOSYALARI ---"
for b in projeler/proje.py projeler/kayit.py projeler/sema.py projeler/tani.py ara.py; do
  [ -f "$P/scripts/$b" ] && kontrol "scripts/$b var" 0 || kontrol "scripts/$b var" 1
  python -c "import ast;ast.parse(open('$P/scripts/$b',encoding='utf-8').read())" 2>/dev/null \
    && kontrol "scripts/$b sozdizimi gecerli" 0 || kontrol "scripts/$b sozdizimi gecerli" 1
done

echo ""
echo "--- 2. PROJE TANIMI (E11 temeli) ---"
[ -f ".claude/proje.json" ] && kontrol "Bu projenin tanimi var" 0 || kontrol "Bu projenin tanimi var" 1
python "$P/scripts/projeler/proje.py" dogrula > /dev/null 2>&1 \
  && kontrol "Tanim gecerli" 0 || kontrol "Tanim gecerli" 1

python - << 'PY' 2>/dev/null && kontrol "Tanimda gizli bilgi YOK" 0 || kontrol "Tanimda gizli bilgi YOK" 1
import json, re, glob
for yol in [".claude/proje.json"] + glob.glob("hafiza/projeler/*.json"):
    ham = open(yol, encoding="utf-8").read()
    assert not re.search(r'"(parola|password|sifre|secret|token|api_key)"\s*:\s*"[^"]{4,}"',
                         ham, re.I), yol
PY

echo ""
echo "--- 3. MERKEZI KAYIT (E11) ---"
python "$P/scripts/projeler/kayit.py" liste > _calisma/pl.txt 2>&1
grep -q "PROJELER" _calisma/pl.txt && kontrol "Proje listesi uretiliyor" 0 || kontrol "Proje listesi uretiliyor" 1

# Tanimli olma bilgisi kayittan degil, o anki durumdan okunmali
grep -c "tanım dosyası yok" _calisma/pl.txt > _calisma/tanimsiz.txt 2>/dev/null || echo 0 > _calisma/tanimsiz.txt
TANIMSIZ=$(cat _calisma/tanimsiz.txt)
[ "$TANIMSIZ" -eq 0 ] && kontrol "Tanimli durumu guncel okunuyor" 0 || kontrol "Tanimli durumu guncel okunuyor ($TANIMSIZ tanimsiz gorunuyor)" 1
# Cikti Turkce karakterli; ASCII aramak yaniltiyordu.
grep -q "buradas" _calisma/pl.txt && kontrol "Mevcut proje isaretleniyor" 0 || kontrol "Mevcut proje isaretleniyor" 1

python - << 'PY' 2>/dev/null && kontrol "Tarama koku D:/Projeler ile sinirli" 0 || kontrol "Tarama koku D:/Projeler ile sinirli" 1
import json, sys
from pathlib import Path
yol = Path.home() / ".claude" / "enver" / "projeler.json"
veri = json.loads(yol.read_text(encoding="utf-8"))
kokler = veri.get("kokler", [])
assert kokler, "kok tanimli degil"
for kok in kokler:
    assert Path(kok).resolve() == Path("D:/Projeler").resolve(), kok
PY

python - << 'PY' 2>/dev/null && kontrol "Butun projeler kok altinda" 0 || kontrol "Butun projeler kok altinda" 1
import json, sys
from pathlib import Path
yol = Path.home() / ".claude" / "enver" / "projeler.json"
veri = json.loads(yol.read_text(encoding="utf-8"))
kok = Path("D:/Projeler").resolve()
for ad, kayit in veri.get("projeler", {}).items():
    p = Path(kayit["yol"]).resolve()
    assert kok in p.parents or p == kok, f"{ad}: {p}"
PY

echo ""
echo "--- 4. CIFT KAYIT (proje + merkezi yansima) ---"
[ -d "hafiza/projeler" ] && kontrol "Merkezi yansima dizini var" 0 || kontrol "Merkezi yansima dizini var" 1
SAYI=$(ls hafiza/projeler/*.json 2>/dev/null | wc -l)
[ "$SAYI" -ge 20 ] && kontrol "Merkezi yansimada $SAYI tanim var" 0 || kontrol "Merkezi yansimada yeterli tanim ($SAYI)" 1

python - << 'PY' 2>/dev/null && kontrol "Asil kayit merkezi yansimadan ustun" 0 || kontrol "Asil kayit merkezi yansimadan ustun" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/projeler")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
import kayit
from pathlib import Path
# Denek olarak bulundugumuz depo kullanilir. Ad ve yol sabit
# yazilmaz; depo baska bir ada klonlansa da test gecerli kalir.
kok = Path.cwd()
k = {"ad": kok.name, "yol": str(kok)}
t = kayit.tanim_getir(k)
assert t and t.get("ad") == kok.name, t
# Yol bozuksa merkezi yansimaya dusmeli
k2 = {"ad": kok.name, "yol": "D:/olmayan-yol-12345"}
t2 = kayit.tanim_getir(k2)
assert t2 is not None, "merkezi yansimaya dusulmedi"
PY

echo ""
echo "--- 5. PROJEYE GECMEDEN SORGU (E10) ---"
# Sorgulanacak proje HARITADAN alinir; teste gomulmez
ILK_PROJE=$(python -c "
import json, sys
from pathlib import Path
yol = Path.home() / '.claude' / 'enver' / 'projeler.json'
try:
    d = json.loads(yol.read_text(encoding='utf-8'))
    adlar = sorted(d.get('projeler', {}))
    print(adlar[0] if adlar else '')
except Exception:
    print('')
")
python "$P/scripts/projeler/kayit.py" sor "$ILK_PROJE" "teknoloji" > _calisma/sr.txt 2>&1
grep -qi "teknolojiler" _calisma/sr.txt && kontrol "Gecmeden bilgi alinabiliyor" 0 || kontrol "Gecmeden bilgi alinabiliyor" 1

python "$P/scripts/projeler/kayit.py" goster "olmayan-proje-12345" > /dev/null 2>&1 && S=1 || S=0
kontrol "Olmayan proje dogru sekilde reddediliyor" $S

echo ""
echo "--- 6. GORSEL SEMA (E4) ---"
python "$P/scripts/projeler/sema.py" uret --hedef _calisma/test-sema.html > _calisma/sm.txt 2>&1 \
  && kontrol "Sema uretilebiliyor" 0 || kontrol "Sema uretilebiliyor" 1

python - << 'PY' 2>/dev/null && kontrol "Sema tek dosya, dis kaynak yok" 0 || kontrol "Sema tek dosya, dis kaynak yok" 1
import re
h = open("_calisma/test-sema.html", encoding="utf-8").read()
assert not re.search(r'(src|href)=["\']https?://', h), "dis kaynak var"
PY

python - << 'PY' 2>/dev/null && kontrol "Sema butun projeleri ciziyor" 0 || kontrol "Sema butun projeleri ciziyor" 1
import re, json
from pathlib import Path
h = open("_calisma/test-sema.html", encoding="utf-8").read()
kutu = len(re.findall(r'class="dugum"', h))
veri = json.loads((Path.home() / ".claude" / "enver" / "projeler.json").read_text(encoding="utf-8"))
assert kutu == len(veri["projeler"]), f"{kutu} kutu, {len(veri['projeler'])} proje"
PY

python - << 'PY' 2>/dev/null && kontrol "Sema tiklanabilir ve ayrinti paneli var" 0 || kontrol "Sema tiklanabilir ve ayrinti paneli var" 1
h = open("_calisma/test-sema.html", encoding="utf-8").read()
for parca in ['class="dugum"', 'id="panel"', "addEventListener", "function kacir"]:
    assert parca in h, parca
PY

python - << 'PY' 2>/dev/null && kontrol "Sema karanlik tema ve mobil uyumlu" 0 || kontrol "Sema karanlik tema ve mobil uyumlu" 1
h = open("_calisma/test-sema.html", encoding="utf-8").read()
assert "prefers-color-scheme: dark" in h
assert "@media (max-width: 900px)" in h
PY

python - << 'PY' 2>/dev/null && kontrol "Semada gizli bilgi YOK" 0 || kontrol "Semada gizli bilgi YOK" 1
import re
h = open("_calisma/test-sema.html", encoding="utf-8").read()
assert not re.search(r'"(parola|password|sifre|secret|token|api_key)"\s*:\s*"[^"]{4,}"', h, re.I)
PY

python "$P/scripts/projeler/sema.py" ozet 2>/dev/null | grep -q "SİSTEM ŞEMASI" \
  && kontrol "Sema metin ozeti calisiyor" 0 || kontrol "Sema metin ozeti calisiyor" 1

echo ""
echo "--- 7. OTOMATIK TANIMA ---"
python "$P/scripts/projeler/tani.py" bu --deneme > /dev/null 2>&1 \
  && kontrol "Tanima deneme modu calisiyor" 0 || kontrol "Tanima deneme modu calisiyor" 1

python - << 'PY' 2>/dev/null && kontrol "Tanima elle yazilani ezmiyor" 0 || kontrol "Tanima elle yazilani ezmiyor" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/projeler")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
import tani
mevcut = {"ad": "elle-yazilmis", "gorev": "ELLE YAZILDI", "durum": "canlida"}
tahmin = {"ad": "otomatik", "gorev": "TAHMIN", "durum": "yarim", "teknolojiler": ["Python"]}
yeni, doldurulan = tani.birlestir(mevcut, tahmin)
assert yeni["gorev"] == "ELLE YAZILDI", yeni["gorev"]
assert yeni["durum"] == "canlida", yeni["durum"]
assert yeni["teknolojiler"] == ["Python"]
assert "teknolojiler" in doldurulan and "gorev" not in doldurulan
PY

python - << 'PY' 2>/dev/null && kontrol "Tahmin edilen alanlar isaretleniyor" 0 || kontrol "Tahmin edilen alanlar isaretleniyor" 1
import json, glob
bulundu = False
for yol in glob.glob("hafiza/projeler/*.json"):
    veri = json.load(open(yol, encoding="utf-8"))
    if veri.get("_tahmin_edilen_alanlar"):
        bulundu = True
        break
assert bulundu, "hicbir tanimda tahmin isareti yok"
PY

echo ""
echo "--- 8. TEK ARAMA (T88) ---"
python "$P/scripts/ara.py" "kasa" > _calisma/ar.txt 2>&1
grep -q "eşleşme" _calisma/ar.txt && kontrol "Arama sonuc uretiyor" 0 || kontrol "Arama sonuc uretiyor" 1

python "$P/scripts/ara.py" "sifre" 2>/dev/null | grep -q "Kasa aranmaz\|kasada" \
  && kontrol "Gizli konuda kasaya yonlendiriyor" 0 || kontrol "Gizli konuda kasaya yonlendiriyor" 1

python - << 'PY' 2>/dev/null && kontrol "Turkce karakter farki aramayi bozmuyor" 0 || kontrol "Turkce karakter farki aramayi bozmuyor" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
import ara
a = ara.ara("sifre")
b = ara.ara("şifre")
assert a and b, (len(a), len(b))
assert len(a) == len(b), (len(a), len(b))
PY

python "$P/scripts/ara.py" "qxzv-hicbir-kayitta-bulunmayan-ifade-7788" > /dev/null 2>&1 && S=1 || S=0
kontrol "Bulunamayan aramada dogru sonuc" $S

echo ""
echo "--- 9. KOMUTLAR ---"
for k in projeler sema ara; do
  [ -f "$P/commands/$k.md" ] && kontrol "$k komutu var" 0 || kontrol "$k komutu var" 1
  grep -q "^description:" "$P/commands/$k.md" \
    && kontrol "$k komutunun aciklamasi var" 0 || kontrol "$k komutunun aciklamasi var" 1
done

echo ""
echo "--- 10. GERILEME TESTLERI ---"
if [ -n "$ENVER_GERILEME_ATLA" ]; then
  echo "  (gerileme testleri atlandi - ust testten cagrildi)"
else
export ENVER_GERILEME_ATLA=1
for f in 0 1 2 3; do
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
[ "$KALAN" -eq 0 ] && echo " FAZ 4 KAPISI ACIK" || echo " FAZ 4 KAPISI KAPALI"
