#!/usr/bin/env bash
# Faz 5 kapi kontrolu - faz motoru ve tam yetki

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
echo " FAZ 5 KAPI KONTROLU - Faz motoru ve tam yetki"
echo "============================================"
echo ""

echo "--- 1. BETIK VE KANCA DOSYALARI ---"
for b in faz/faz.py faz/mod.py faz/izole.py; do
  [ -f "$P/scripts/$b" ] && kontrol "scripts/$b var" 0 || kontrol "scripts/$b var" 1
  python -c "import ast;ast.parse(open('$P/scripts/$b',encoding='utf-8').read())" 2>/dev/null \
    && kontrol "scripts/$b sozdizimi gecerli" 0 || kontrol "scripts/$b sozdizimi gecerli" 1
done
for k in tam-yetki kalite-kapisi; do
  [ -f "hooks/$k.py" ] && kontrol "hooks/$k.py var" 0 || kontrol "hooks/$k.py var" 1
  python -c "import ast;ast.parse(open('hooks/$k.py',encoding='utf-8').read())" 2>/dev/null \
    && kontrol "hooks/$k.py sozdizimi gecerli" 0 || kontrol "hooks/$k.py sozdizimi gecerli" 1
done

echo ""
echo "--- 2. FAZ MOTORU (T34) ---"
[ -f "hafiza/faz-plani.json" ] && kontrol "Faz plani var" 0 || kontrol "Faz plani var" 1

python - << 'PY' 2>/dev/null && kontrol "Plan gecerli ve tutarli" 0 || kontrol "Plan gecerli ve tutarli" 1
import json
d = json.load(open("hafiza/faz-plani.json", encoding="utf-8"))
fazlar = d["fazlar"]
assert len(fazlar) >= 11, len(fazlar)
numaralar = [f["no"] for f in fazlar]
assert len(numaralar) == len(set(numaralar)), numaralar
assert numaralar == sorted(numaralar), numaralar
for f in fazlar:
    assert "no" in f and "ad" in f and "durum" in f, f
    assert f["durum"] in ("bekliyor", "calisiyor", "kapi-bekliyor", "tamamlandi"), f
    # Numara SAYI olmali; metin olursa siralama alfabetik olur
    # ve 10, 11 numarali fazlar 2'den once gelir
    assert isinstance(f["no"], int), (f["no"], type(f["no"]).__name__)
PY

# Butun fazlar tamamlandiysa aktif faz OLMAZ - bu gecerli bir durumdur.
# Olculecek sey durumun okunabilmesi, aktif faz bulunmasi degil.
python "$P/scripts/faz/faz.py" durum > _calisma/fz.txt 2>&1
grep -qE "Aktif faz|Bütün fazlar tamamlandı" _calisma/fz.txt   && kontrol "Faz durumu okunabiliyor" 0 || kontrol "Faz durumu okunabiliyor" 1
grep -q "İLERLEME" _calisma/fz.txt && kontrol "Ilerleme gosteriliyor" 0 || kontrol "Ilerleme gosteriliyor" 1

python "$P/scripts/faz/faz.py" plan 2>/dev/null | grep -q "FAZ PLANI" \
  && kontrol "Plan listelenebiliyor" 0 || kontrol "Plan listelenebiliyor" 1

python - << 'PY' 2>/dev/null && kontrol "Aktif faz dogru hesaplaniyor" 0 || kontrol "Aktif faz dogru hesaplaniyor" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/faz")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
import faz
biten, toplam = faz.ilerleme()
assert toplam >= 11, toplam
assert biten >= 5, biten
# Aktif faz, tamamlanmamis ILK faz olmali - numarasi sabit degil
plan = faz.plan_oku()["fazlar"]
beklenen = next((f for f in plan if f.get("durum") != "tamamlandi"), None)
aktif = faz.aktif_faz()
assert aktif == beklenen, (aktif, beklenen)
PY

python - << 'PY' 2>/dev/null && kontrol "Her fazin kapi komutu tanimli" 0 || kontrol "Her fazin kapi komutu tanimli" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/faz")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
import faz
aktif = faz.aktif_faz()
if aktif is None:
    # Butun fazlar bitti - o zaman TAMAMLANAN fazlarin kapisi olmali
    fazlar = faz.plan_oku()["fazlar"]
    kapisiz = [f["no"] for f in fazlar if not f.get("kapi_komutu")]
    assert not kapisiz, f"kapi komutu olmayan fazlar: {kapisiz}"
else:
    assert aktif.get("kapi_komutu"), f"faz {aktif['no']} kapi komutu yok"
PY

echo ""
echo "--- 3. CALISMA MODLARI (T59) ---"
python "$P/scripts/faz/mod.py" > _calisma/md.txt 2>&1
grep -q "Çalışma modu" _calisma/md.txt && kontrol "Mod durumu okunabiliyor" 0 || kontrol "Mod durumu okunabiliyor" 1
grep -q "tam-yetki" _calisma/md.txt && kontrol "Butun modlar listeleniyor" 0 || kontrol "Butun modlar listeleniyor" 1

python - << 'PY' 2>/dev/null && kontrol "Mod degistirilebiliyor ve geri alinabiliyor" 0 || kontrol "Mod degistirilebiliyor ve geri alinabiliyor" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/faz")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
import ayarlar, mod
onceki = ayarlar.oku().get("calisma_modu", "dikkatli")
mod.mod_ayarla("tam-yetki")
assert ayarlar.oku().get("tam_yetki") is True
mod.mod_ayarla("dikkatli")
assert ayarlar.oku().get("tam_yetki") is False
mod.mod_ayarla(onceki)
PY

echo ""
echo "--- 4. TAM YETKI GUVENLIGI (E12) ---"
python "$P/scripts/testler/tam-yetki-testleri.py" "$KOK" > _calisma/ty.txt 2>&1
HATA=$(grep -c "HATA" _calisma/ty.txt)
TOPLAM=$(grep -c "^  \[" _calisma/ty.txt)
[ "$HATA" -eq 0 ] && kontrol "Tam yetki senaryolari ($TOPLAM senaryo, $HATA hata)" 0 \
                  || { kontrol "Tam yetki senaryolari ($HATA hata)" 1; grep "HATA" _calisma/ty.txt; }

python - << 'PY' 2>/dev/null && kontrol "Istisna listesi eksiksiz" 0 || kontrol "Istisna listesi eksiksiz" 1
import re
kaynak = open("hooks/tam-yetki.py", encoding="utf-8").read()
for konu in ["kasa", "silme", "uzak sunucu", "canlıya çıkış", "depo ayarı",
             "geri alınamaz", "ödeme"]:
    assert konu in kaynak, konu
PY

python - << 'PY' 2>/dev/null && kontrol "Kanca cokerse tam yetki kapali kalir" 0 || kontrol "Kanca cokerse tam yetki kapali kalir" 1
import json, subprocess, sys
# Bozuk girdi verildiginde kanca izin VERMEMELI
p = subprocess.run([sys.executable, "hooks/tam-yetki.py"], input="bozuk-json",
                   capture_output=True, text=True, encoding="utf-8")
cikti = json.loads(p.stdout or "{}")
assert cikti.get("hookSpecificOutput", {}).get("permissionDecision") != "allow", cikti
PY

echo ""
echo "--- 5. KALITE KAPISI (T5) ---"
python - << 'PY' 2>/dev/null && kontrol "Tam yetki kapaliyken kalite kapisi sessiz" 0 || kontrol "Tam yetki kapaliyken kalite kapisi sessiz" 1
import json, subprocess, sys
sys.path.insert(0, "plugins/enver-framework/scripts/faz")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
import ayarlar, mod
onceki = ayarlar.oku().get("calisma_modu", "dikkatli")
mod.mod_ayarla("dikkatli")
p = subprocess.run([sys.executable, "hooks/kalite-kapisi.py"],
                   input=json.dumps({"stop_hook_active": False}),
                   capture_output=True, text=True, encoding="utf-8")
cikti = json.loads(p.stdout or "{}")
assert cikti.get("decision") != "block", cikti
mod.mod_ayarla(onceki)
PY

python - << 'PY' 2>/dev/null && kontrol "Sonsuz dongu korumasi var" 0 || kontrol "Sonsuz dongu korumasi var" 1
import json, subprocess, sys
p = subprocess.run([sys.executable, "hooks/kalite-kapisi.py"],
                   input=json.dumps({"stop_hook_active": True}),
                   capture_output=True, text=True, encoding="utf-8")
cikti = json.loads(p.stdout or "{}")
assert cikti == {}, cikti
PY

grep -q "stop_hook_active" hooks/kalite-kapisi.py \
  && kontrol "Dongu korumasi kodda tanimli" 0 || kontrol "Dongu korumasi kodda tanimli" 1

echo ""
echo "--- 6. IZOLE DENEME ALANI (T51) ---"
python - << 'PY' 2>/dev/null && kontrol "Deneme alani proje DISINDA aciliyor" 0 || kontrol "Deneme alani proje DISINDA aciliyor" 1
import sys
from pathlib import Path
sys.path.insert(0, "plugins/enver-framework/scripts/faz")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
import izole, yollar
kok = Path(yollar.proje_kok()).resolve()
hedef = izole.deneme_koku(kok).resolve()
assert kok not in hedef.parents and hedef != kok, (kok, hedef)
PY

grep -q "arsiv.arsivle" "$P/scripts/faz/izole.py" \
  && kontrol "Kapatirken arsivleniyor (silinmiyor)" 0 || kontrol "Kapatirken arsivleniyor" 1

echo ""
echo "--- 7. KANCA KAYDI ---"
python - << 'PY' 2>/dev/null && kontrol "Yeni kancalar settings.json'da" 0 || kontrol "Yeni kancalar settings.json'da" 1
import json
d = json.load(open(".claude/settings.json", encoding="utf-8"))
metin = json.dumps(d)
assert "tam-yetki" in metin
assert "kalite-kapisi" in metin
assert "Stop" in d["hooks"]
PY

python - << 'PY' 2>/dev/null && kontrol "Kurulum betigi yeni kancalari taniyor" 0 || kontrol "Kurulum betigi yeni kancalari taniyor" 1
import ast, sys
kaynak = open("plugins/enver-framework/scripts/kurulum/kanca-kaydet.py", encoding="utf-8").read()
for dugum in ast.walk(ast.parse(kaynak)):
    if isinstance(dugum, ast.Assign):
        for hedef in dugum.targets:
            if getattr(hedef, "id", "") == "KANCA_TANIMLARI":
                dosyalar = {t["dosya"] for t in ast.literal_eval(dugum.value)}
                for ad in ["tam-yetki.py", "kalite-kapisi.py"]:
                    assert ad in dosyalar, ad
                sys.exit(0)
sys.exit(1)
PY

echo ""
echo "--- 8. KOMUT ---"
[ -f "$P/commands/faz.md" ] && kontrol "faz komutu var" 0 || kontrol "faz komutu var" 1
grep -q "kontrolsüzlük değil" "$P/commands/faz.md" \
  && kontrol "Tam yetkinin sinirlari belgelenmis" 0 || kontrol "Tam yetkinin sinirlari belgelenmis" 1

echo ""
echo "--- 9. YAZIM DENETIMI ---"
python "$P/scripts/testler/yazim-testleri.py" "$KOK" > _calisma/yz.txt 2>&1
HATA=$(grep -c "HATA" _calisma/yz.txt)
[ "$HATA" -eq 0 ] && kontrol "Yazim senaryolari (0 hata)" 0 \
                  || { kontrol "Yazim senaryolari ($HATA hata)" 1; grep "HATA" _calisma/yz.txt; }

echo ""
echo "--- 10. GERILEME TESTLERI ---"
if [ -n "$ENVER_GERILEME_ATLA" ]; then
  echo "  (gerileme testleri atlandi - ust testten cagrildi)"
else
export ENVER_GERILEME_ATLA=1
for f in 0 1 2 3 4; do
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
[ "$KALAN" -eq 0 ] && echo " FAZ 5 KAPISI ACIK" || echo " FAZ 5 KAPISI KAPALI"
