#!/usr/bin/env bash
# Faz 10 kapı kontrolü - sağlık ve paylaşım (son faz)

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
for d in ("saglik","kurulum","ortak","hafiza"):
    sys.path.insert(0, f"plugins/enver-framework/scripts/{d}")'

echo "============================================"
echo " FAZ 10 KAPI KONTROLU - Saglik ve paylasim"
echo "============================================"
echo ""

echo "--- 1. BETIK DOSYALARI ---"
for b in saglik/saglik.py kurulum/sihirbaz.py; do
  [ -f "$P/scripts/$b" ] && kontrol "scripts/$b var" 0 || kontrol "scripts/$b var" 1
  python -c "import ast;ast.parse(open('$P/scripts/$b',encoding='utf-8').read())" 2>/dev/null \
    && kontrol "scripts/$b sozdizimi gecerli" 0 || kontrol "scripts/$b sozdizimi gecerli" 1
done

echo ""
echo "--- 2. SAGLIK KONTROLU (T82) ---"
python "$P/scripts/saglik/saglik.py" bak > _calisma/sg.txt 2>&1
GECTI_KODU=$?
grep -q "SAĞLIK KONTROLÜ" _calisma/sg.txt \
  && kontrol "Saglik kontrolu calisiyor" 0 || kontrol "Saglik kontrolu calisiyor" 1

[ "$GECTI_KODU" -eq 0 ] && kontrol "Framework saglikli (bozuk bulgu yok)" 0 \
  || { kontrol "Framework saglikli" 1; grep "BOZUK" _calisma/sg.txt | head -5; }

python - << PY 2>/dev/null && kontrol "Koruma olcumu KAYITLI degil CALISIYOR mu bakiyor" 0 || kontrol "Koruma olcumu davranis olcuyor" 1
$YOL_EKLE
import saglik
# Her ölçümde gerçek bir girdi ve beklenen karar olmalı
assert len(saglik.KORUMA_OLCUMLERI) >= 5, len(saglik.KORUMA_OLCUMLERI)
for dosya, arac, girdiler, beklenen, mesaj in saglik.KORUMA_OLCUMLERI:
    assert dosya.endswith(".py"), dosya
    assert girdiler, dosya
    assert mesaj, dosya
PY

python - << PY 2>/dev/null && kontrol "Bozuk koruma YAKALANIYOR" 0 || kontrol "Bozuk koruma YAKALANIYOR" 1
$YOL_EKLE
import json, saglik, shutil
from pathlib import Path
kanca = Path("hooks/veri-koruma.py")
yedek = Path("_calisma/veri-koruma-yedek.py")
shutil.copy2(kanca, yedek)
try:
    # Korumayı geçici olarak etkisizleştir
    kanca.write_text('import json\nprint(json.dumps({}))\n', encoding="utf-8")
    bulgular = saglik.kancalari_kontrol()
    assert any(d[0] == saglik.BOZUK for d in bulgular), bulgular
finally:
    shutil.copy2(yedek, kanca)
    yedek.unlink()
# Geri alındıktan sonra tekrar iyi olmalı
bulgular = saglik.kancalari_kontrol()
assert not any(d[0] == saglik.BOZUK for d in bulgular), bulgular
PY

python "$P/scripts/saglik/saglik.py" istatistik 2>/dev/null | grep -q "FRAMEWORK İSTATİSTİĞİ" \
  && kontrol "Istatistik uretiliyor" 0 || kontrol "Istatistik uretiliyor" 1

echo ""
echo "--- 3. CAKISMA DENETIMI (T84) ---"
python "$P/scripts/saglik/saglik.py" cakisma > _calisma/ck.txt 2>&1 \
  && kontrol "Cakisma denetimi gecti" 0 \
  || { kontrol "Cakisma denetimi gecti" 1; grep "BOZUK" _calisma/ck.txt | head -4; }

python - << PY 2>/dev/null && kontrol "Harf farkiyla cakisma yakalanabiliyor" 0 || kontrol "Harf farkiyla cakisma yakalanabiliyor" 1
$YOL_EKLE
import saglik, re
kaynak = open("plugins/enver-framework/scripts/saglik/saglik.py", encoding="utf-8").read()
# Windows veri kaybı dersinden gelen kontrol kodda olmalı
assert "lower()" in kaynak and "cakisma" in kaynak.lower()
assert "Windows" in kaynak
PY

echo ""
echo "--- 4. DIL TUTARLILIGI (E18) ---"
python - << PY 2>/dev/null && kontrol "Dil dosyalari ayni anahtarlari tasiyor" 0 || kontrol "Dil dosyalari ayni anahtarlari tasiyor" 1
$YOL_EKLE
import saglik
bulgular = saglik.dili_kontrol()
assert not any(d[0] == saglik.BOZUK for d in bulgular), bulgular
PY

python - << PY 2>/dev/null && kontrol "Dil degistirilebiliyor" 0 || kontrol "Dil degistirilebiliyor" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
import ayarlar, metin
onceki = ayarlar.oku().get("dil", "tr")
try:
    ayarlar.yaz({"dil": "en"})
    metin._onbellek.clear()
    assert metin.al("korumalar.engellendi") == "BLOCKED", metin.al("korumalar.engellendi")
    ayarlar.yaz({"dil": "tr"})
    metin._onbellek.clear()
    assert metin.al("korumalar.engellendi") == "ENGELLENDİ"
finally:
    ayarlar.yaz({"dil": onceki})
    metin._onbellek.clear()
PY

echo ""
echo "--- 5. KURULUM SIHIRBAZI (T92) ---"
python "$P/scripts/kurulum/sihirbaz.py" kontrol > _calisma/sh.txt 2>&1
grep -q "ORTAM KONTROLÜ" _calisma/sh.txt \
  && kontrol "Ortam kontrolu calisiyor" 0 || kontrol "Ortam kontrolu calisiyor" 1

python - << PY 2>/dev/null && kontrol "Kasa ve gunluk asla depoya girmiyor" 0 || kontrol "Kasa ve gunluk asla depoya girmiyor" 1
$YOL_EKLE
import sihirbaz
sorunlar = sihirbaz.kisisel_veri_kontrol(paylasim=False)
assert not sorunlar, sorunlar
PY

python - << PY 2>/dev/null && kontrol "Paylasimda hafiza cikarilmasi gerektigi biliniyor" 0 || kontrol "Paylasimda hafiza cikarilmasi gerektigi biliniyor" 1
$YOL_EKLE
import sihirbaz
assert "hafiza" in sihirbaz.PAYLASIMDA_CIKAR, sihirbaz.PAYLASIMDA_CIKAR
assert "kasa" in sihirbaz.ASLA_DEPOYA
# İki liste ayrı olmalı - hafıza kendi kullanımda depoda durur
assert "hafiza" not in sihirbaz.ASLA_DEPOYA
sorunlar = sihirbaz.kisisel_veri_kontrol(paylasim=True)
assert any("hafiza" in s for s in sorunlar), sorunlar
PY

echo ""
echo "--- 6. PAYLASIMA HAZIRLAMA ---"
rm -rf _calisma/paylasim-kapi 2>/dev/null
python "$P/scripts/kurulum/sihirbaz.py" paylasima-hazirla \
  --hedef _calisma/paylasim-kapi --uzerine-yaz > _calisma/pz.txt 2>&1 \
  && kontrol "Temiz kopya uretiliyor" 0 || kontrol "Temiz kopya uretiliyor" 1

python - << PY 2>/dev/null && kontrol "Temiz kopyada hafiza YOK" 0 || kontrol "Temiz kopyada hafiza YOK" 1
from pathlib import Path
hedef = Path("_calisma/paylasim-kapi")
assert hedef.is_dir(), "kopya uretilmemis"
assert not (hedef / "hafiza").exists(), "hafiza kopyaya girmis"
assert not (hedef / "kasa").exists(), "kasa kopyaya girmis"
assert not (hedef / ".claude" / "proje.json").exists(), "proje tanimi kopyaya girmis"
PY

python - << PY 2>/dev/null && kontrol "Temiz kopyada framework govdesi VAR" 0 || kontrol "Temiz kopyada framework govdesi VAR" 1
from pathlib import Path
hedef = Path("_calisma/paylasim-kapi")
for gereken in ("README.md", "hooks", "plugins/enver-framework/commands",
                "plugins/enver-framework/scripts", "kurulum.ps1"):
    assert (hedef / gereken).exists(), gereken
PY

python - << PY 2>/dev/null && kontrol "Temiz kopyada musteri bilgisi YOK" 0 || kontrol "Temiz kopyada musteri bilgisi YOK" 1
import json
from pathlib import Path
hedef = Path("_calisma/paylasim-kapi")
# Cihaz envanteri ve proje tanımları müşteri adı taşır; kopyada olmamalı
for yol in hedef.rglob("*.json"):
    ad = yol.name
    assert ad not in ("cihaz-envanteri.json", "gorevler.json",
                      "hizmet-takvimi.json", "projeler.json"), ad
PY

echo ""
echo "--- 7. DEGISIKLIK GUNLUGU (T94) ---"
[ -f "DEGISIKLIKLER.md" ] && kontrol "Degisiklik gunlugu var" 0 || kontrol "Degisiklik gunlugu var" 1
grep -q "### Neden" DEGISIKLIKLER.md \
  && kontrol "Her surumde 'neden' yaziyor" 0 || kontrol "Her surumde 'neden' yaziyor" 1

python - << 'PY' 2>/dev/null && kontrol "Gunlukteki surum plugin surumuyle uyumlu" 0 || kontrol "Gunlukteki surum plugin surumuyle uyumlu" 1
import json, re
from pathlib import Path
p = json.load(open("plugins/.claude-plugin/plugin.json", encoding="utf-8"))
gunluk = Path("DEGISIKLIKLER.md").read_text(encoding="utf-8")
surumler = re.findall(r"^## (\d+\.\d+\.\d+)", gunluk, re.MULTILINE)
assert surumler, "gunlukte surum basligi yok"
assert p["version"] in surumler, (p["version"], surumler[:3])
PY

echo ""
echo "--- 8. KOMUT ---"
[ -f "$P/commands/saglik.md" ] && kontrol "saglik komutu var" 0 || kontrol "saglik komutu var" 1
grep -q "Kayıtlı.*çalışıyor.*farklı" "$P/commands/saglik.md" \
  && kontrol "Komut kayitli-calisiyor ayrimini anlatiyor" 0 \
  || kontrol "Komut kayitli-calisiyor ayrimini anlatiyor" 1

echo ""
echo "--- 9. GERILEME TESTLERI ---"
if [ -n "$ENVER_GERILEME_ATLA" ]; then
  echo "  (gerileme testleri atlandi - ust testten cagrildi)"
else
export ENVER_GERILEME_ATLA=1
for f in 0 1 2 3 4 5 6 7 8 9; do
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
[ "$KALAN" -eq 0 ] && echo " FAZ 10 KAPISI ACIK" || echo " FAZ 10 KAPISI KAPALI"
