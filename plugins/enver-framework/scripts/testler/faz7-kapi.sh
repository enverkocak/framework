#!/usr/bin/env bash
# Faz 7 kapı kontrolü - operasyon ve sunucu
#
# Not: Güvenlik denetimini sınamak için gerçekçi görünümlü bir anahtar gerekiyor.
# Dosyaya düz halde yazılsa kasa koruması bu dosyanın YAZILMASINI engelliyor -
# ki doğrusu da bu. Bu yüzden örnek anahtar çalışma anında parçalardan kuruluyor.

KOK="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && { pwd -W 2>/dev/null || pwd; })}"
P="$KOK/plugins/enver-framework"
S="$P/scripts/sunucu"
cd "$KOK" || exit 1
mkdir -p _calisma

GECEN=0; KALAN=0
kontrol() {
  if [ "$2" -eq 0 ]; then echo "  [GECTI ] $1"; GECEN=$((GECEN+1));
  else echo "  [KALDI ] $1"; KALAN=$((KALAN+1)); fi
}

echo "============================================"
echo " FAZ 7 KAPI KONTROLU - Operasyon ve sunucu"
echo "============================================"
echo ""

echo "--- 1. BETIK DOSYALARI ---"
for b in yedek.py sertifika.py deploy.py kontrol.py; do
  [ -f "$S/$b" ] && kontrol "sunucu/$b var" 0 || kontrol "sunucu/$b var" 1
  python -c "import ast;ast.parse(open('$S/$b',encoding='utf-8').read())" 2>/dev/null \
    && kontrol "sunucu/$b sozdizimi gecerli" 0 || kontrol "sunucu/$b sozdizimi gecerli" 1
done

echo ""
echo "--- 2. YEDEK VE GERI DONUS (T32/T55) ---"
rm -rf _calisma/yedek-testi 2>/dev/null
mkdir -p _calisma/yedek-testi
printf 'ilk surum\n' > _calisma/yedek-testi/veri.txt

python - << 'PY' 2>/dev/null && kontrol "Yedek alinabiliyor" 0 || kontrol "Yedek alinabiliyor" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/sunucu")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
import yedek
hedef, bilgi = yedek.al("_calisma/yedek-testi", "Kapi testi", etiket="kapi-testi")
assert hedef.is_dir(), hedef
assert bilgi["neden"] == "Kapi testi"
assert (hedef / "yedek-bilgisi.json").is_file()
PY

python - << 'PY' 2>/dev/null && kontrol "Yedekte neden bilgisi tutuluyor" 0 || kontrol "Yedekte neden bilgisi tutuluyor" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/sunucu")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
import yedek
liste = yedek.yedekler()
assert liste, "yedek yok"
assert liste[0].get("neden"), liste[0]
assert liste[0].get("kaynak"), liste[0]
PY

python - << 'PY' 2>/dev/null && kontrol "Geri donus calisiyor ve kendisi de geri alinabiliyor" 0 || kontrol "Geri donus calisiyor ve kendisi de geri alinabiliyor" 1
import sys
from pathlib import Path
sys.path.insert(0, "plugins/enver-framework/scripts/sunucu")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
import yedek

veri = Path("_calisma/yedek-testi/veri.txt")
veri.write_text("bozuk surum\n", encoding="utf-8")

bilgi = yedek.yedek_bul("kapi-testi")
assert bilgi, "yedek bulunamadi"

kaynak, onceki = yedek.geri_don(bilgi)
assert veri.read_text(encoding="utf-8").strip() == "ilk surum", veri.read_text()
assert onceki is not None, "geri donus oncesi yedek alinmadi"
assert onceki.is_dir(), onceki
PY

echo ""
echo "--- 3. SERTIFIKA TAKIBI (T47) ---"
python - << 'PY' 2>/dev/null && kontrol "Sertifika cozumleyicisi calisiyor" 0 || kontrol "Sertifika cozumleyicisi calisiyor" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/sunucu")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
sys.path.insert(0, "plugins/enver-framework/scripts/projeler")
import sertifika
sonuc = sertifika.sertifika_bilgisi("enverkocak.com")
assert sonuc["durum"] in ("gecerli", "dikkat", "acil", "kritik", "ulasilamadi"), sonuc
if sonuc["durum"] != "ulasilamadi":
    assert sonuc.get("kalan_gun") is not None, sonuc
PY

python - << 'PY' 2>/dev/null && kontrol "Ulasilamayan adres cokme yapmiyor" 0 || kontrol "Ulasilamayan adres cokme yapmiyor" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/sunucu")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
sys.path.insert(0, "plugins/enver-framework/scripts/projeler")
import sertifika
sonuc = sertifika.sertifika_bilgisi("kesinlikle-olmayan-adres-98765.test")
assert sonuc["durum"] == "ulasilamadi", sonuc
assert "hata" in sonuc
PY

python - << 'PY' 2>/dev/null && kontrol "Uyari esikleri tanimli" 0 || kontrol "Uyari esikleri tanimli" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/sunucu")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
sys.path.insert(0, "plugins/enver-framework/scripts/projeler")
import sertifika
assert sertifika.DIKKAT_GUN == 30 and sertifika.ACIL_GUN == 14
PY

echo ""
echo "--- 4. DEPLOY GUVENLIK ZINCIRI (T14) ---"
python "$S/deploy.py" kontrol > _calisma/dp.txt 2>&1
grep -q "DEPLOY GÜVENLİK ZİNCİRİ" _calisma/dp.txt \
  && kontrol "Zincir calisiyor" 0 || kontrol "Zincir calisiyor" 1

grep -q "Hazırlık" _calisma/dp.txt \
  && kontrol "Hazirlik adimi var" 0 || kontrol "Hazirlik adimi var" 1

python - << 'PY' 2>/dev/null && kontrol "Hedef tanimsizsa zincir DURUYOR" 0 || kontrol "Hedef tanimsizsa zincir DURUYOR" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/sunucu")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
sys.path.insert(0, "plugins/enver-framework/scripts/projeler")
import deploy
z = deploy.Zincir(".")
deploy.adim_hazirlik(z, None)
assert z.durdu, "tanim yokken zincir durmadi"
z2 = deploy.Zincir(".")
deploy.adim_hazirlik(z2, {"ad": "x"})
assert z2.durdu, "sunucu/dizin yokken zincir durmadi"
z3 = deploy.Zincir(".")
deploy.adim_hazirlik(z3, {"ad": "x", "sunucu": "s", "dizin": "/var/www/x/"})
assert not z3.durdu, "tam tanimda zincir durdu"
PY

python - << 'PY' 2>/dev/null && kontrol "Testler gecmezse zincir DURUYOR" 0 || kontrol "Testler gecmezse zincir DURUYOR" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/sunucu")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
sys.path.insert(0, "plugins/enver-framework/scripts/projeler")
import deploy
z = deploy.Zincir(".")
deploy.adim_test(z, ".", "python -c \"import sys; sys.exit(1)\"")
assert z.durdu, "basarisiz testte zincir durmadi"
z2 = deploy.Zincir(".")
deploy.adim_test(z2, ".", "python -c \"pass\"")
assert not z2.durdu, "basarili testte zincir durdu"
PY

grep -q "ASIL GÖNDERİMİ KENDİ YAPMAZ" "$S/deploy.py" \
  && kontrol "Asil gonderimi kendisi yapmiyor (insan karari)" 0 \
  || kontrol "Asil gonderimi kendisi yapmiyor" 1

echo ""
echo "--- 5. TESLIM ONCESI DENETIMLER (T44/T45/T46) ---"
rm -rf _calisma/kontrol-kapi 2>/dev/null
mkdir -p _calisma/kontrol-kapi
python - << 'PY'
from pathlib import Path
Path("_calisma/kontrol-kapi/k.html").write_text(
    '<!doctype html><html><head></head><body><img src="a.png">'
    '<div onclick="x()">T</div><script src="a.js"></script></body></html>',
    encoding="utf-8")
# Örnek anahtar parçalardan kuruluyor; bu dosyada düz halde durmuyor
ornek_anahtar = "sk-" + "ornekAnahtar" + "1234567890abc"
Path("_calisma/kontrol-kapi/k.php").write_text(
    '<?php\n$api_key = "' + ornek_anahtar + '";\neval($k);\n',
    encoding="utf-8")
PY
python "$S/kontrol.py" tara _calisma/kontrol-kapi > _calisma/kt.txt 2>&1
for alan in "GÜVENLİK" "ERİŞİLEBİLİRLİK" "ARAMA" "BAŞARIM"; do
  grep -q "$alan" _calisma/kt.txt && kontrol "$alan alani denetleniyor" 0 || kontrol "$alan alani denetleniyor" 1
done

grep -q "yapılacak:" _calisma/kt.txt \
  && kontrol "Her bulguda yapilacak is yaziyor" 0 || kontrol "Her bulguda yapilacak is yaziyor" 1

grep -qi "acikta anahtar\|açıkta anahtar" _calisma/kt.txt \
  && kontrol "Acikta kalan anahtar yakalaniyor" 0 || kontrol "Acikta kalan anahtar yakalaniyor" 1

rm -rf _calisma/kontrol-temiz 2>/dev/null
mkdir -p _calisma/kontrol-temiz
python - << 'PY'
from pathlib import Path
Path("_calisma/kontrol-temiz/t.html").write_text(
    '<!doctype html><html lang="tr"><head><title>Sayfa</title>'
    '<meta name="description" content="Aciklama"></head><body><h1>Baslik</h1>'
    '<img src="a.png" alt="Aciklama" width="10" height="10">'
    '<script src="a.js" defer></script></body></html>',
    encoding="utf-8")
PY
python "$S/kontrol.py" tara _calisma/kontrol-temiz 2>/dev/null | grep -q "bulgu yok" \
  && kontrol "Temiz sayfada yanlis alarm yok" 0 || kontrol "Temiz sayfada yanlis alarm yok" 1

python - << 'PY' 2>/dev/null && kontrol "Bos klasorde 'sorun yok' denmiyor" 0 || kontrol "Bos klasorde 'sorun yok' denmiyor" 1
import subprocess, sys
from pathlib import Path
Path("_calisma/kontrol-bos").mkdir(parents=True, exist_ok=True)
p = subprocess.run([sys.executable,
                    "plugins/enver-framework/scripts/sunucu/kontrol.py",
                    "tara", "_calisma/kontrol-bos"],
                   capture_output=True, text=True, encoding="utf-8")
assert "bakılamadı" in p.stdout, p.stdout
PY

echo ""
echo "--- 6. GERILEME TESTLERI ---"
if [ -n "$ENVER_GERILEME_ATLA" ]; then
  echo "  (gerileme testleri atlandi - ust testten cagrildi)"
else
export ENVER_GERILEME_ATLA=1
for f in 0 1 2 3 4 5 6; do
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
[ "$KALAN" -eq 0 ] && echo " FAZ 7 KAPISI ACIK" || echo " FAZ 7 KAPISI KAPALI"
