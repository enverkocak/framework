#!/usr/bin/env bash
# Faz 3 kapı kontrolü - hafıza ve süreklilik

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
echo " FAZ 3 KAPI KONTROLU - Hafiza ve sureklilik"
echo "============================================"
echo ""

echo "--- 1. BETIK DOSYALARI ---"
for b in hafiza/hafiza.py hafiza/oturum.py hafiza/defter.py \
         senkron/makine.py senkron/senkron.py \
         index/proje-index.py statusline.py; do
  [ -f "$P/scripts/$b" ] && kontrol "scripts/$b var" 0 || kontrol "scripts/$b var" 1
  python -c "import ast;ast.parse(open('$P/scripts/$b',encoding='utf-8').read())" 2>/dev/null \
    && kontrol "scripts/$b sozdizimi gecerli" 0 || kontrol "scripts/$b sozdizimi gecerli" 1
done

for k in oturum-kayit oturum-acilis; do
  [ -f "hooks/$k.py" ] && kontrol "hooks/$k.py var" 0 || kontrol "hooks/$k.py var" 1
done

echo ""
echo "--- 2. ALAN AYRIMI (hafiza senkron olur, gunluk olmaz) ---"
git check-ignore -q hafiza/durum.md && S=1 || S=0
kontrol "hafiza/ depoya GIRER (senkron olur)" $S

git check-ignore -q gunluk/komutlar.jsonl && S=0 || S=1
kontrol "gunluk/ depoya GIRMEZ (makineye ozel)" $S

git check-ignore -q kasa/kasa.kilit && S=0 || S=1
kontrol "kasa/ depoya GIRMEZ" $S

echo ""
echo "--- 3. MAKINE KIMLIGI (E13) ---"
python "$P/scripts/senkron/makine.py" durum > _calisma/mk.txt 2>&1
grep -q "TANINIYOR" _calisma/mk.txt && kontrol "Bu makine taniniyor" 0 || kontrol "Bu makine taniniyor" 1
[ -f "hafiza/makineler.json" ] && kontrol "Makine kaydi dosyasi var" 0 || kontrol "Makine kaydi dosyasi var" 1
python -c "import json;d=json.load(open('hafiza/makineler.json',encoding='utf-8'));assert d['makineler']" 2>/dev/null \
  && kontrol "Makine kaydi gecerli" 0 || kontrol "Makine kaydi gecerli" 1

python - << 'PY' 2>/dev/null && kontrol "Makine kaydinda sabit disk yolu sorunu yok" 0 || kontrol "Makine kaydinda sabit disk yolu sorunu yok" 1
import json, sys
sys.path.insert(0, "plugins/enver-framework/scripts/senkron")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
import makine
# Her makine kendi yolunu taşır; yol makineye göre çözülür, koda gömülmez
d = json.load(open("hafiza/makineler.json", encoding="utf-8"))
for kayit in d["makineler"].values():
    assert kayit.get("proje_yolu"), kayit
assert makine.kimlik() in d["makineler"]
PY

echo ""
echo "--- 4. OTURUM KAYDI VE OZETI (T16-T18, E5) ---"
python "$P/scripts/hafiza/oturum.py" kaydet not "Kapi testi olayi" > /dev/null 2>&1 \
  && kontrol "Ham gunluge kayit yazilabiliyor" 0 || kontrol "Ham gunluge kayit yazilabiliyor" 1

[ -f "gunluk/komutlar.jsonl" ] && kontrol "Ham gunluk dosyasi olustu" 0 || kontrol "Ham gunluk dosyasi olustu" 1

python "$P/scripts/hafiza/oturum.py" kaydet komut "mysql -u root --password=GizliParola123 db" > _calisma/gz.txt 2>&1
grep -q "GizliParola123" _calisma/gz.txt && S=1 || S=0
kontrol "Parola kayda gecerken GIZLENIYOR" $S
grep -q "GizliParola123" gunluk/komutlar.jsonl && S=1 || S=0
kontrol "Parola ham gunlukte de GIZLI" $S

[ -f "hafiza/durum.md" ] && kontrol "Durum belgesi var" 0 || kontrol "Durum belgesi var" 1
ls hafiza/oturumlar/*.md >/dev/null 2>&1 && kontrol "Oturum ozeti uretilmis" 0 || kontrol "Oturum ozeti uretilmis" 1

echo ""
echo "--- 5. ACILIS BRIFINGI (E5/T19) ---"
echo '{"session_id":"t","source":"startup"}' | python hooks/oturum-acilis.py > _calisma/br.json 2>&1
python -c "
import json
d=json.load(open('_calisma/br.json',encoding='utf-8'))
m=d['hookSpecificOutput']['additionalContext']
assert 'NEREDE KALDIK' in m, m[:200]
assert 'Makine' in m
" 2>/dev/null && kontrol "Brifing nerede kaldik bilgisini veriyor" 0 || kontrol "Brifing nerede kaldik bilgisini veriyor" 1

echo ""
echo "--- 6. DEFTERLER (T21/T23) ---"
python "$P/scripts/hafiza/defter.py" karar ekle "Kapi testi karari" "Test amacli kayit." > /dev/null 2>&1 \
  && kontrol "Karar eklenebiliyor" 0 || kontrol "Karar eklenebiliyor" 1
[ -f "hafiza/kararlar.md" ] && kontrol "Karar defteri olustu" 0 || kontrol "Karar defteri olustu" 1

python "$P/scripts/hafiza/defter.py" hata ekle "Kapi testi hatasi belirtisi" "Cozum adimi." --nerede "kapi testi" > /dev/null 2>&1 \
  && kontrol "Hata eklenebiliyor" 0 || kontrol "Hata eklenebiliyor" 1

python "$P/scripts/hafiza/defter.py" hata ara "kapi testi" 2>/dev/null | grep -q "belirtisi" \
  && kontrol "Hata aramasi calisiyor" 0 || kontrol "Hata aramasi calisiyor" 1

python "$P/scripts/hafiza/defter.py" hata ara "qxzv-hicbir-kayitta-bulunmayan-ifade-7788" > /dev/null 2>&1 && S=1 || S=0
kontrol "Bulunamayan aramada dogru sonuc" $S

echo ""
echo "--- 7. PROJE INDEX'LERI (E6/T86) ---"
python "$P/scripts/index/proje-index.py" uret > _calisma/ix.txt 2>&1 \
  && kontrol "Index uretilebiliyor" 0 || kontrol "Index uretilebiliyor" 1
[ -f "plugins/enver-framework/scripts/ICINDEKILER.md" ] && kontrol "Icindekiler belgesi uretilmis" 0 || kontrol "Icindekiler belgesi uretilmis" 1

grep -q "INDEX.md" "$P/scripts/index/proje-index.py" && grep -q 'INDEX_ADI = "ICINDEKILER.md"' "$P/scripts/index/proje-index.py" \
  && kontrol "Uretilen ad ICINDEKILER.md (cakisma onlendi)" 0 || kontrol "Uretilen ad ICINDEKILER.md (cakisma onlendi)" 1

# Gerileme koruması: index üreteci daha önce INDEX.md yazıyordu ve Windows
# harf büyüklüğüne bakmadığı için elle yazılmış index.md dosyalarının üzerine
# yazılıyordu. Uç dosya böyle kayboldu, depodan geri alındı.
# Bu kontrol aynı şeyin tekrar olmasını yakalar.
for D in "plugins/enver-framework/commands/index.md" "bilgi/index.md" "sablonlar/index.md"; do
  [ -s "$D" ] && kontrol "$D saglam (uzerine yazilmamis)" 0 || kontrol "$D saglam" 1
done
grep -q "^description:" "plugins/enver-framework/commands/index.md" \
  && kontrol "index.md komut tanimi bozulmamis" 0 || kontrol "index.md komut tanimi bozulmamis" 1
grep -q "cakisma_var_mi" "$P/scripts/index/proje-index.py" \
  && kontrol "Uretecte cakisma kontrolu var" 0 || kontrol "Uretecte cakisma kontrolu var" 1

# Önce üret, sonra kontrol et. Yeni klasör eklendikçe index eskiyor;
# bu bir hata değil. Ölçülecek şey, üretim sonrası güncel olup olmadığı.
python "$P/scripts/index/proje-index.py" uret > /dev/null 2>&1
python "$P/scripts/index/proje-index.py" kontrol > /dev/null 2>&1 \
  && kontrol "Index uretim sonrasi guncel" 0 || kontrol "Index uretim sonrasi guncel" 1

echo ""
echo "--- 8. SENKRON (E13) ---"
python "$P/scripts/senkron/senkron.py" durum > _calisma/sk.txt 2>&1
grep -q "Makine" _calisma/sk.txt && kontrol "Senkron durumu okunabiliyor" 0 || kontrol "Senkron durumu okunabiliyor" 1

python - << 'PY' 2>/dev/null && kontrol "Senkron kapsami sadece hafiza" 0 || kontrol "Senkron kapsami sadece hafiza" 1
import ast
kaynak = open("plugins/enver-framework/scripts/senkron/senkron.py", encoding="utf-8").read()
for dugum in ast.walk(ast.parse(kaynak)):
    if isinstance(dugum, ast.Assign):
        for hedef in dugum.targets:
            if getattr(hedef, "id", "") == "SENKRON_YOLLARI":
                yollar = ast.literal_eval(dugum.value)
                assert yollar == ["hafiza"], yollar
PY

echo ""
echo "--- 9. DURUM SATIRI (T89) ---"
echo '{"workspace":{"project_dir":"'"$KOK"'"},"cost":{"total_cost_usd":1.5}}' \
  | python "$P/scripts/statusline.py" > _calisma/sl.txt 2>&1
grep -q "kasa" _calisma/sl.txt && kontrol "Durum satiri kasa durumunu gosteriyor" 0 || kontrol "Durum satiri kasa durumunu gosteriyor" 1
grep -q "$(basename "$KOK")" _calisma/sl.txt && kontrol "Durum satiri proje adini gosteriyor" 0 || kontrol "Durum satiri proje adini gosteriyor" 1

echo "" | python "$P/scripts/statusline.py" > /dev/null 2>&1 \
  && kontrol "Durum satiri bos girdide cokmuyor" 0 || kontrol "Durum satiri bos girdide cokmuyor" 1

echo ""
echo "--- 10. KANCA KAYDI ---"
python - << 'PY' 2>/dev/null && kontrol "Yeni kancalar settings.json'da" 0 || kontrol "Yeni kancalar settings.json'da" 1
import json
d = json.load(open(".claude/settings.json", encoding="utf-8"))
metin = json.dumps(d)
for ad in ["oturum-kayit", "oturum-acilis", "statusline"]:
    assert ad in metin, ad
assert "SessionStart" in d["hooks"]
assert d.get("statusLine")
PY

python - << 'PY' 2>/dev/null && kontrol "Kurulum betigi yeni kancalari taniyor" 0 || kontrol "Kurulum betigi yeni kancalari taniyor" 1
import ast, sys
kaynak = open("plugins/enver-framework/scripts/kurulum/kanca-kaydet.py", encoding="utf-8").read()
for dugum in ast.walk(ast.parse(kaynak)):
    if isinstance(dugum, ast.Assign):
        for hedef in dugum.targets:
            if getattr(hedef, "id", "") == "KANCA_TANIMLARI":
                dosyalar = {t["dosya"] for t in ast.literal_eval(dugum.value)}
                for ad in ["oturum-kayit.py", "oturum-acilis.py"]:
                    assert ad in dosyalar, ad
                sys.exit(0)
sys.exit(1)
PY

echo ""
echo "--- 11. YAZIM DENETIMI KESKINLIGI ---"
python "$P/scripts/testler/yazim-testleri.py" "$KOK" > _calisma/yz.txt 2>&1
HATA=$(grep -c "HATA" _calisma/yz.txt)
[ "$HATA" -eq 0 ] && kontrol "Yazim senaryolari (0 hata)" 0 \
                  || { kontrol "Yazim senaryolari ($HATA hata)" 1; grep "HATA" _calisma/yz.txt; }

echo ""
echo "--- 12. GERILEME TESTLERI ---"
if [ -n "$ENVER_GERILEME_ATLA" ]; then
  echo "  (gerileme testleri atlandi - ust testten cagrildi)"
else
export ENVER_GERILEME_ATLA=1
for f in 0 1 2; do
  bash "$P/scripts/testler/faz$f-kapi.sh" "$KOK" > "_calisma/faz$f.txt" 2>&1
  grep -q " 0 kaldi" "_calisma/faz$f.txt" && kontrol "Faz $f hala gecerli" 0 \
    || { kontrol "Faz $f hala gecerli" 1; grep "KALDI" "_calisma/faz$f.txt" | head -5; }
done
unset ENVER_GERILEME_ATLA
fi

echo ""
echo "============================================"
echo " SONUC: $GECEN gecti, $KALAN kaldi"
echo "============================================"
[ "$KALAN" -eq 0 ] && echo " FAZ 3 KAPISI ACIK" || echo " FAZ 3 KAPISI KAPALI"
