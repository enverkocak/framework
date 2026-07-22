#!/usr/bin/env bash
# Faz 2 kapı kontrolü - koruma kalkanı

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
echo " FAZ 2 KAPI KONTROLU - Koruma kalkani"
echo "============================================"
echo ""

echo "--- 1. KANCA DOSYALARI ---"
for k in sunucu-koruma git-gizlilik-koruma iz-kontrol veri-koruma kasa-koruma yazim-kontrol; do
  [ -f "hooks/$k.py" ] && kontrol "hooks/$k.py var" 0 || kontrol "hooks/$k.py var" 1
  python -c "import ast;ast.parse(open('hooks/$k.py',encoding='utf-8').read())" 2>/dev/null \
    && kontrol "hooks/$k.py sozdizimi gecerli" 0 || kontrol "hooks/$k.py sozdizimi gecerli" 1
done
[ -f "hooks/_ortak_yol.py" ] && kontrol "hooks/_ortak_yol.py (yardimci) var" 0 || kontrol "hooks/_ortak_yol.py (yardimci) var" 1

echo ""
echo "--- 2. KAYIT (settings.json) ---"
python - << 'PY' 2>/dev/null && kontrol "Butun kancalar settings.json'da kayitli" 0 || kontrol "Butun kancalar settings.json'da kayitli" 1
import json
d = json.load(open(".claude/settings.json", encoding="utf-8"))
komutlar = []
for olay in ("PreToolUse", "PostToolUse"):
    for grup in d["hooks"].get(olay, []):
        for k in grup.get("hooks", []):
            komutlar.append(k["command"])
metin = " ".join(komutlar)
for ad in ["sunucu-koruma", "git-gizlilik-koruma", "veri-koruma",
           "kasa-koruma", "iz-kontrol", "yazim-kontrol"]:
    assert ad in metin, ad
PY

python - << 'PY' 2>/dev/null && kontrol "Kurulum betigi butun kancalari taniyor" 0 || kontrol "Kurulum betigi butun kancalari taniyor" 1
import ast, sys
kaynak = open("plugins/enver-framework/scripts/kurulum/kanca-kaydet.py", encoding="utf-8").read()
agac = ast.parse(kaynak)
for dugum in ast.walk(agac):
    if isinstance(dugum, ast.Assign):
        for hedef in dugum.targets:
            if getattr(hedef, "id", "") == "KANCA_TANIMLARI":
                tanimlar = ast.literal_eval(dugum.value)
                dosyalar = {t["dosya"] for t in tanimlar}
                for ad in ["sunucu-koruma.py", "git-gizlilik-koruma.py", "veri-koruma.py",
                           "kasa-koruma.py", "iz-kontrol.py", "yazim-kontrol.py"]:
                    assert ad in dosyalar, ad
                sys.exit(0)
sys.exit(1)
PY

echo ""
echo "--- 3. KASA MOTORU (E1) ---"
K="$P/scripts/kasa/kasa.py"
[ -f "$K" ] && kontrol "Kasa betigi var" 0 || kontrol "Kasa betigi var" 1

rm -rf _calisma/kasa-testi 2>/dev/null
mkdir -p _calisma/kasa-testi
printf 'ornek: deger\n' > _calisma/kasa-testi/a.md

python "$K" kilitle > /dev/null 2>&1
python "$K" kur --kaynak _calisma/kasa-testi --parola "KapiTesti2026!" --uzerine-yaz > /dev/null 2>&1 \
  && kontrol "Kasa kurulabiliyor" 0 || kontrol "Kasa kurulabiliyor" 1

grep -q "ornek: deger" kasa/kasa.kilit 2>/dev/null && S=1 || S=0
kontrol "Sifreli dosyada duz metin YOK" $S

python "$K" oku a.md > /dev/null 2>&1 && S=1 || S=0
kontrol "Kilitliyken okuma REDDEDILIYOR" $S

python "$K" ac --parola "YanlisParola123" > /dev/null 2>&1 && S=1 || S=0
kontrol "Yanlis parola REDDEDILIYOR" $S

python "$K" ac --parola "KapiTesti2026!" --sure 2 > /dev/null 2>&1 \
  && kontrol "Dogru parola kasayi aciyor" 0 || kontrol "Dogru parola kasayi aciyor" 1

python "$K" oku a.md 2>/dev/null | grep -q "ornek: deger" \
  && kontrol "Acikken icerik okunabiliyor" 0 || kontrol "Acikken icerik okunabiliyor" 1

python "$K" kilitle > /dev/null 2>&1
python "$K" oku a.md > /dev/null 2>&1 && S=1 || S=0
kontrol "Kilitlendikten sonra tekrar REDDEDILIYOR" $S

echo ""
echo "--- 4. KORUMA DAVRANISI ---"
python "$P/scripts/testler/koruma-testleri.py" > _calisma/koruma-sonuc.txt 2>&1
HATA=$(grep -c "HATA" _calisma/koruma-sonuc.txt)
TOPLAM=$(grep -c "^  \[" _calisma/koruma-sonuc.txt)
[ "$HATA" -eq 0 ] && kontrol "Koruma senaryolari ($TOPLAM senaryo, $HATA hata)" 0 \
                  || { kontrol "Koruma senaryolari ($TOPLAM senaryo, $HATA hata)" 1; grep "HATA" _calisma/koruma-sonuc.txt; }

echo ""
echo "--- 5. SUNUCU HARITASI (T31/E3) ---"
[ -f "$P/references/sunucu-haritasi.json" ] && kontrol "Sunucu haritasi dosyasi var" 0 || kontrol "Sunucu haritasi dosyasi var" 1
python -c "import json;json.load(open('$P/references/sunucu-haritasi.json',encoding='utf-8'))" 2>/dev/null \
  && kontrol "Sunucu haritasi gecerli JSON" 0 || kontrol "Sunucu haritasi gecerli JSON" 1

python - << 'PY' 2>/dev/null && kontrol "Haritada parola/anahtar YOK" 0 || kontrol "Haritada parola/anahtar YOK" 1
import json, re
ham = open("plugins/enver-framework/references/sunucu-haritasi.json", encoding="utf-8").read()
yasak = re.compile(r'"(parola|password|sifre|secret|token|api_key)"\s*:\s*"[^"]{6,}"', re.I)
assert not yasak.search(ham)
PY

grep -q "IZINLI_DIZINLER" hooks/sunucu-koruma.py && S=1 || S=0
kontrol "Sunucu korumasinda sabit kodlu dizin YOK" $S

echo ""
echo "--- 6. SANAL DENEME (T61) ---"
[ -f "$P/scripts/kuru-deneme.py" ] && kontrol "Sanal deneme betigi var" 0 || kontrol "Sanal deneme betigi var" 1
python "$P/scripts/kuru-deneme.py" "git reset --hard" 2>/dev/null | grep -q "ONAY İSTER" \
  && kontrol "Sanal deneme yikici komutu bildiriyor" 0 || kontrol "Sanal deneme yikici komutu bildiriyor" 1
python "$P/scripts/kuru-deneme.py" "ls -la" 2>/dev/null | grep -q "engel görmez" \
  && kontrol "Sanal deneme zararsiz komutu geciriyor" 0 || kontrol "Sanal deneme zararsiz komutu geciriyor" 1

echo ""
echo "--- 7. TURKCE GEREKCE (E15/E16) ---"
python - << 'PY' 2>/dev/null && kontrol "Gerekceler Turkce ve dort parcali" 0 || kontrol "Gerekceler Turkce ve dort parcali" 1
import json, subprocess, sys
veri = json.dumps({"tool_name": "Bash", "tool_input": {"command": "rm -rf x"}})
p = subprocess.run([sys.executable, "hooks/veri-koruma.py"], input=veri,
                   capture_output=True, text=True, encoding="utf-8")
sebep = json.loads(p.stdout)["hookSpecificOutput"]["permissionDecisionReason"]
for parca in ["ENGELLENDİ", "Ne yapılacak", "Neden", "Nasıl düzeltilir"]:
    assert parca in sebep, parca
PY

echo ""
echo "--- 8. GERILEME TESTLERI ---"
bash "$P/scripts/testler/faz0-kapi.sh" "$KOK" > _calisma/faz0.txt 2>&1
grep -q " 0 kaldi" _calisma/faz0.txt && kontrol "Faz 0 hala gecerli" 0 \
  || { kontrol "Faz 0 hala gecerli" 1; grep "KALDI" _calisma/faz0.txt; }

bash "$P/scripts/testler/faz1-kapi.sh" "$KOK" > _calisma/faz1.txt 2>&1
grep -q " 0 kaldi" _calisma/faz1.txt && kontrol "Faz 1 hala gecerli" 0 \
  || { kontrol "Faz 1 hala gecerli" 1; grep "KALDI" _calisma/faz1.txt; }

echo ""
echo "============================================"
echo " SONUC: $GECEN gecti, $KALAN kaldi"
echo "============================================"
[ "$KALAN" -eq 0 ] && echo " FAZ 2 KAPISI ACIK" || echo " FAZ 2 KAPISI KAPALI"
