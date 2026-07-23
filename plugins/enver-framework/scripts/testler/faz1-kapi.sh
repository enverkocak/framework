#!/usr/bin/env bash
# Faz 1 kapı kontrolü - çekirdek iskelet

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
echo " FAZ 1 KAPI KONTROLU - Cekirdek iskelet"
echo "============================================"
echo ""

echo "--- 1. DIZIN YAPISI (T1/T3/T4) ---"
for d in skills scripts scripts/ortak scripts/kurulum references diller commands agents; do
  [ -d "$P/$d" ] && kontrol "$d/ dizini var" 0 || kontrol "$d/ dizini var" 1
done

echo ""
echo "--- 2. DIL KATMANI (E18) ---"
for f in tr en; do
  python -c "import json;json.load(open('$P/diller/$f.json',encoding='utf-8'))" 2>/dev/null \
    && kontrol "diller/$f.json gecerli JSON" 0 || kontrol "diller/$f.json gecerli JSON" 1
done

python -c "
import json
tr=json.load(open('$P/diller/tr.json',encoding='utf-8'))
en=json.load(open('$P/diller/en.json',encoding='utf-8'))
def anahtarlar(d,on=''):
    s=set()
    for k,v in d.items():
        y=f'{on}.{k}' if on else k
        s.add(y)
        if isinstance(v,dict): s|=anahtarlar(v,y)
    return s
assert anahtarlar(tr)==anahtarlar(en), anahtarlar(tr)^anahtarlar(en)
" 2>/dev/null && kontrol "tr ve en ayni anahtarlara sahip" 0 || kontrol "tr ve en ayni anahtarlara sahip" 1

cd "$P/scripts/ortak" || exit 1
python -c "
import sys,io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
import metin
assert metin.al('korumalar.engellendi')=='ENGELLENDİ'
" 2>/dev/null && kontrol "Turkce metin dogru okunuyor" 0 || kontrol "Turkce metin dogru okunuyor" 1

python -c "
import ayarlar,metin,json,os
from pathlib import Path
h=Path.home()/'.claude'/'enver'/'ayarlar.json'
eski=h.read_text(encoding='utf-8') if h.is_file() else None
ayarlar.yaz({'dil':'en'})
import importlib; importlib.reload(metin)
metin._onbellek.clear()
assert metin.al('korumalar.engellendi')=='BLOCKED', metin.al('korumalar.engellendi')
ayarlar.yaz({'dil':'tr'})
metin._onbellek.clear()
assert metin.al('korumalar.engellendi')=='ENGELLENDİ'
if eski is not None: h.write_text(eski,encoding='utf-8')
" 2>/dev/null && kontrol "Dil degistirilebiliyor (tr <-> en)" 0 || kontrol "Dil degistirilebiliyor (tr <-> en)" 1

python -c "
import metin
assert metin.al('boyle.bir.anahtar.yok')=='boyle.bir.anahtar.yok'
" 2>/dev/null && kontrol "Eksik anahtar cokmuyor" 0 || kontrol "Eksik anahtar cokmuyor" 1

echo ""
echo "--- 3. BETIK KATMANI (T3) ---"
cd "$KOK" || exit 1
for f in ortak/ayarlar.py ortak/metin.py ortak/yollar.py ortak/arsiv.py index-uret.py kurulum/kanca-kaydet.py; do
  python -c "import ast;ast.parse(open('$P/scripts/$f',encoding='utf-8').read())" 2>/dev/null \
    && kontrol "scripts/$f sozdizimi gecerli" 0 || kontrol "scripts/$f sozdizimi gecerli" 1
done

cd "$P/scripts/ortak" || exit 1
python -c "
import yollar
from pathlib import Path
k=yollar.proje_kok('$KOK')
assert Path(k).resolve()==Path('$KOK').resolve(), k
assert yollar.gecici_mi('test-deneme.tmp')
assert not yollar.gecici_mi('index.php')
assert yollar.ana_dizinde_mi('$KOK/README.md',k)
assert not yollar.ana_dizinde_mi('$KOK/plugins/enver-framework/hooks/iz-kontrol.py',k)
" 2>/dev/null && kontrol "Yol cozumleme dogru calisiyor" 0 || kontrol "Yol cozumleme dogru calisiyor" 1

echo ""
echo "--- 4. ARSIV MOTORU (E2/E7) ---"
cd "$KOK" || exit 1
[ -f "_arsiv/INDEX.md" ] && kontrol "Arsiv INDEX.md uretiliyor" 0 || kontrol "Arsiv INDEX.md uretiliyor" 1
ls _arsiv/*/NEDEN.md >/dev/null 2>&1 && kontrol "Her arsiv kaydinda NEDEN.md var" 0 || kontrol "Her arsiv kaydinda NEDEN.md var" 1
[ -d "_arsiv/2026-07-21_odeme-entegrasyonu-denemesi-2" ] && kontrol "Ayni ada ikinci kayit numaralaniyor" 0 || kontrol "Ayni ada ikinci kayit numaralaniyor" 1

echo ""
echo "--- 5. KOMUT REHBERI (E14) ---"
[ -f "$P/commands/index.md" ] && kontrol "index komutu var" 0 || kontrol "index komutu var" 1
[ -f "$P/skills/index-rehber/SKILL.md" ] && kontrol "index-rehber becerisi var" 0 || kontrol "index-rehber becerisi var" 1

python "$P/scripts/index-uret.py" > _calisma/rehber.txt 2>/dev/null && kontrol "Rehber uretilebiliyor" 0 || kontrol "Rehber uretilebiliyor" 1
grep -q "/index" _calisma/rehber.txt && kontrol "Rehberde index komutu listeleniyor" 0 || kontrol "Rehberde index komutu listeleniyor" 1
grep -q "index-rehber" _calisma/rehber.txt && kontrol "Rehberde beceriler listeleniyor" 0 || kontrol "Rehberde beceriler listeleniyor" 1
grep -q "iz-kontrol.py" _calisma/rehber.txt && kontrol "Rehberde korumalar listeleniyor" 0 || kontrol "Rehberde korumalar listeleniyor" 1
grep -q "Açıklama" _calisma/rehber.txt && kontrol "Rehber Turkce karakterle uretiliyor" 0 || kontrol "Rehber Turkce karakterle uretiliyor" 1

python "$P/scripts/index-uret.py" --json > _calisma/rehber.json 2>/dev/null
python -c "
import json
d=json.load(open('_calisma/rehber.json',encoding='utf-8'))
assert len(d['komutlar'])>=17, len(d['komutlar'])
assert len(d['ajanlar'])>=4
assert len(d['kancalar'])>=3
assert len(d['beceriler'])>=1
" 2>/dev/null && kontrol "JSON ciktisi dogru sayida ogeye sahip" 0 || kontrol "JSON ciktisi dogru sayida ogeye sahip" 1

echo ""
echo "--- 6. WINDOWS KATMANI (T35) ---"
[ -f "kurulum.ps1" ] && kontrol "kurulum.ps1 var" 0 || kontrol "kurulum.ps1 var" 1
[ -f "guncelle.ps1" ] && kontrol "guncelle.ps1 var" 0 || kontrol "guncelle.ps1 var" 1
# Korumalar artik plugin'in hooks.json'u ile gelir (tek teslim), kurulum
# ayri kanca kaydi yapmaz. Olculecek yapisal invariant: plugin hooks.json
# TASIYOR ve butun kancalari tanimliyor - "/plugin install" korumalari da getirir.
HJ="plugins/enver-framework/hooks/hooks.json"
python -c "import json,sys; d=json.load(open('$HJ',encoding='utf-8')); h=d['hooks']; assert h.get('PreToolUse') and h.get('PostToolUse') and h.get('SessionStart') and h.get('Stop'); s=json.dumps(h); assert 'veri-koruma.py' in s and 'kasa-koruma.py' in s and 'CLAUDE_PLUGIN_ROOT' in s" 2>/dev/null \
  && kontrol "Plugin hooks.json korumalari tanimliyor (tek teslim)" 0 || kontrol "Plugin hooks.json korumalari tanimliyor (tek teslim)" 1
grep -q "kanca-kaydet.py" kurulum.sh && kontrol "kurulum.sh kanca KAYDETMIYOR (plugin veriyor)" 1 || kontrol "kurulum.sh kanca KAYDETMIYOR (plugin veriyor)" 0

echo ""
echo "--- 7. PAKETLEME (T2) ---"
python -c "
import json
p=json.load(open('$KOK/plugins/.claude-plugin/plugin.json',encoding='utf-8'))
m=json.load(open('$KOK/plugins/.claude-plugin/marketplace.json',encoding='utf-8'))
# Sürüm sabit değil: uç dosyanın aynı sürümü taşıdığı doğrulanır
readme = open('$KOK/README.md', encoding='utf-8').readline()
import re
r = re.search(r'v(\d+\.\d+\.\d+)', readme).group(1)
assert p['version']==m['plugins'][0]['version']==r, (p['version'], m['plugins'][0]['version'], r)
assert p['author']['name']=='Enver KOCAK'
" 2>/dev/null && kontrol "Surumler uc dosyada tutarli" 0 || kontrol "Surumler uc dosyada tutarli" 1

head -1 README.md | grep -qE "v[0-9]+\.[0-9]+\.[0-9]+" && kontrol "README surum satiri var" 0 || kontrol "README surum satiri var" 1

echo ""
echo "--- 8. FAZ 0 GERILEME TESTI ---"
bash "$P/scripts/testler/faz0-kapi.sh" "$KOK" > _calisma/faz0.txt 2>&1
if grep -q "0 kaldi" _calisma/faz0.txt; then kontrol "Faz 0 korumalari hala calisiyor (32/32)" 0
else kontrol "Faz 0 korumalari hala calisiyor" 1; grep "KALDI" _calisma/faz0.txt; fi

echo ""
echo "============================================"
echo " SONUC: $GECEN gecti, $KALAN kaldi"
echo "============================================"
[ "$KALAN" -eq 0 ] && echo " FAZ 1 KAPISI ACIK" || echo " FAZ 1 KAPISI KAPALI"
