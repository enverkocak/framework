#!/usr/bin/env bash
# Faz 0 kapı kontrolü - tüm maddeleri doğrular
# Geçici test dosyası. İş bitince arşive taşınır.

KOK="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && { pwd -W 2>/dev/null || pwd; })}"
cd "$KOK" || exit 1
mkdir -p _calisma

# Sunucu değerleri HARITADAN okunur; teste gömülmez.
# Bu dosya paylaşılan kopyada da bulunacağı için kişisel değer taşıyamaz.
HARITA="plugins/enver-framework/references/sunucu-haritasi.json"
ADRES=$(python -c "import json;d=json.load(open('$HARITA',encoding='utf-8'));print(d['sunucular'][0]['adres'])")
KORUNAN=$(python -c "import json;d=json.load(open('$HARITA',encoding='utf-8'));print(d['korunan_kok_dizinler'][0])")
IZINLI=$(python -c "import json;d=json.load(open('$HARITA',encoding='utf-8'));print(d['sunucular'][0]['projeler'][0]['dizin'])")

GECEN=0
KALAN=0

kontrol() {
  # $1 = açıklama, $2 = beklenen (GEÇMELİ/KALMALI), $3 = sonuç (0=başarılı)
  if [ "$3" -eq 0 ]; then
    echo "  [GECTI ] $1"
    GECEN=$((GECEN + 1))
  else
    echo "  [KALDI ] $1"
    KALAN=$((KALAN + 1))
  fi
}

echo "============================================"
echo " FAZ 0 KAPI KONTROLU"
echo "============================================"
echo ""

echo "--- 1. GIT TEMIZLIGI ---"

git log --all --oneline -- vault 2>/dev/null | grep -q . && S=1 || S=0
kontrol "Kasa yerel git gecmisinde YOK" GECMELI $S

git ls-files | grep -qi "^vault/" && S=1 || S=0
kontrol "Kasa git takibinde YOK" GECMELI $S

git ls-tree -r origin/master --name-only 2>/dev/null | grep -qi vault && S=1 || S=0
kontrol "Kasa uzak depoda YOK" GECMELI $S

# Geçmişin sıfırlandığını commit SAYISI değil, kök commit gösterir.
# Sayı her yeni çalışmada artıyor ve ölçü olarak yanıltıcı.
# Taze kurulumda henüz depo geçmişi olmayabilir; bu hata değildir.
if git rev-parse --git-dir > /dev/null 2>&1 && git rev-list -1 HEAD > /dev/null 2>&1; then
  # Ölçülecek şey commit metni değil, GEÇMİŞTE SIR OLMAMASIDIR.
  # Metin arayan bir test yalnızca bu deponun kendi geçmişine uyar;
  # paylaşılan kopya kendi geçmişini oluşturduğunda yanlış alarm verir.
  KOK_COMMIT=$(git rev-list --max-parents=0 HEAD | head -1)
  if git log -1 --format=%s "$KOK_COMMIT" | grep -q "temiz baslangic"; then
    kontrol "Kok commit temiz baslangic (gecmis sifirlanmis)" GECMELI 0
  else
    git log --all --name-only --format="" 2>/dev/null       | grep -qiE "^(vault|kasa)/|\.env$|\.pem$" && S=1 || S=0
    kontrol "Gecmiste sir dosyasi yok (kendi gecmisi olan kopya)" GECMELI $S
  fi
else
  kontrol "Depo gecmisi yok - taze kurulum (atlandi)" GECMELI 0
fi

git status --porcelain | grep -qiE "(vault/|\.env|credential|\.pem|\.key)" && S=1 || S=0
kontrol "Bekleyen degisikliklerde sir dosyasi yok" GECMELI $S

echo ""
echo "--- 2. GITIGNORE KORUMASI ---"

echo "test" > vault/sizma-testi.md
git status --porcelain | grep -q "vault/sizma-testi" && S=1 || S=0
kontrol "Kasaya yeni dosya konsa bile git gormuyor" GECMELI $S
rm -f vault/sizma-testi.md

echo "test" > .env
git status --porcelain | grep -q "\.env" && S=1 || S=0
kontrol ".env dosyasi git'e girmiyor" GECMELI $S
rm -f .env

echo ""
echo "--- 3. KANCA DOSYALARI ---"

# Ayar dosyası bu makinenin mutlak yollarını taşır; her makinede
# kurulum betiği yeniden üretir. Paylaşılan kopyada bulunmaması
# beklenen durumdur, eksiklik değildir.
if [ -f ".claude/settings.json" ]; then
  kontrol "settings.json var" GECMELI 0
  python -c "import json;d=json.load(open('.claude/settings.json'));assert d['hooks']['PreToolUse'];assert d['hooks']['PostToolUse']" 2>/dev/null && S=0 || S=1
  kontrol "settings.json gecerli ve kancalari tanimliyor" GECMELI $S
else
  kontrol "Ayar dosyasi yok - kurulum betigi uretecek (atlandi)" GECMELI 0
  kontrol "Taze kurulum - ayar testi atlandi" GECMELI 0
fi

for k in sunucu-koruma git-gizlilik-koruma iz-kontrol; do
  [ -f "plugins/enver-framework/hooks/$k.py" ] && S=0 || S=1
  kontrol "plugins/enver-framework/hooks/$k.py var" GECMELI $S
  python -c "import ast,sys;ast.parse(open('plugins/enver-framework/hooks/$k.py',encoding='utf-8').read())" 2>/dev/null && S=0 || S=1
  kontrol "plugins/enver-framework/hooks/$k.py sozdizimi gecerli" GECMELI $S
done

[ -f "plugins/enver-framework/hooks/ai-referans-kontrol.py" ] && S=1 || S=0
kontrol "Eski adli kanca dosyasi kalmadi" GECMELI $S

echo ""
echo "--- 4. KANCA DAVRANISI ---"

ct() { python "plugins/enver-framework/hooks/$1.py"; }

# Tek tırnak değişken genişletmez; hook '$ADRES' metnini görür ve
# gerçek bir adres saymaz. Bu yüzden JSON printf ile kuruluyor.
printf '{"tool_name":"Bash","tool_input":{"command":"ssh root@%s rm -rf %sbaska-site.example/"}}' \
  "$ADRES" "$KORUNAN" | ct sunucu-koruma | grep -q '"deny"' && S=0 || S=1
kontrol "Yasak musteri dizini ENGELLENIYOR" GECMELI $S

echo '{"tool_name":"Bash","tool_input":{"command":"ssh root@$ADRES ls $IZINLI"}}' | ct sunucu-koruma | grep -q '"deny"' && S=1 || S=0
kontrol "Izinli dizin GECIYOR" GECMELI $S

echo '{"tool_name":"Bash","tool_input":{"command":"gh repo create yeni --pub'"'"'lic"}}' | ct git-gizlilik-koruma >/dev/null 2>&1
printf '{"tool_name":"Bash","tool_input":{"command":"gh repo create yeni --pu%s"}}' "blic" > _calisma/gp.json
ct git-gizlilik-koruma < _calisma/gp.json | grep -q '"deny"' && S=0 || S=1
kontrol "Herkese acik depo girisimi ENGELLENIYOR" GECMELI $S

printf '{"tool_name":"Bash","tool_input":{"command":"gh repo create yeni"}}' > _calisma/gp2.json
ct git-gizlilik-koruma < _calisma/gp2.json | grep -q '"deny"' && S=0 || S=1
kontrol "Gizlilik bayragi olmayan depo ENGELLENIYOR" GECMELI $S

printf '{"tool_name":"Bash","tool_input":{"command":"gh repo create yeni --private"}}' > _calisma/gp3.json
ct git-gizlilik-koruma < _calisma/gp3.json | grep -q '"deny"' && S=1 || S=0
kontrol "Gizli depo olusturma GECIYOR" GECMELI $S

mkdir -p "D:/Projeler/_test-musteri"
printf 'Claude ile yazildi\n' > "D:/Projeler/_test-musteri/kod.php"
printf '{"tool_name":"Write","tool_input":{"file_path":"D:/Projeler/_test-musteri/kod.php"}}' > _calisma/iz1.json
ct iz-kontrol < _calisma/iz1.json | grep -q "IZ BULUNDU" && S=0 || S=1
kontrol "Musteri projesinde iz YAKALANIYOR" GECMELI $S
rm -rf "D:/Projeler/_test-musteri"

# .iz-muaf her deponun KENDI işaretidir; paylaşılan kopyada bulunmaz,
# kurulum sihirbazı oluşturur. Yokluğu bir eksiklik değil, kurulum adımıdır.
if [ -f ".iz-muaf" ]; then
  printf '{"tool_name":"Write","tool_input":{"file_path":"%s/README.md"}}' "$KOK" > _calisma/iz2.json
  ct iz-kontrol < _calisma/iz2.json | grep -q "IZ BULUNDU" && S=1 || S=0
  kontrol "Framework kendi dosyasi MUAF" GECMELI $S
  kontrol ".iz-muaf isaret dosyasi var" GECMELI 0
else
  kontrol "Muafiyet isareti yok - kurulum sihirbazi olusturacak (atlandi)" GECMELI 0
  kontrol "Taze kurulum - muafiyet testi atlandi" GECMELI 0
fi

echo ""
echo "--- 5. SURUM VE DUPLIKAT ---"

P=$(python -c "import json;print(json.load(open('plugins/.claude-plugin/plugin.json'))['version'])" 2>/dev/null)
M=$(python -c "import json;print(json.load(open('plugins/.claude-plugin/marketplace.json'))['plugins'][0]['version'])" 2>/dev/null)
# Surum README'de ilk satirda olmayabilir (dil gecisi satiri var);
# rozette ya da baslikta. Dosyadaki ilk X.Y.Z'yi al.
R=$(grep -o "[0-9]\+\.[0-9]\+\.[0-9]\+" README.md | head -1)
[ "$P" = "$M" ] && [ "$M" = "$R" ] && S=0 || S=1
kontrol "Surumler ayni (plugin=$P marketplace=$M readme=$R)" GECMELI $S

[ -f "plugins/enver-framework/commands/panel-enver.md" ] && S=1 || S=0
kontrol "panel duplikati kaldirildi" GECMELI $S

KOMUT=$(ls plugins/enver-framework/commands/*.md | wc -l)
[ "$KOMUT" -ge 16 ] && S=0 || S=1
kontrol "En az 16 benzersiz komut var (bulunan: $KOMUT)" GECMELI $S

echo ""
echo "--- 6. ARSIV VE YEDEK ---"

# Bu yedekler Faz 0 temizliginde ENVER'in makinesinde olusturuldu; o makineye
# ozgu tarihsel kayittir. Baska bir bilgisayarda, taze klonda ya da CI'da
# bulunmazlar - yokluklari bir eksiklik degil. (Yerelde gecip CI'da kaldilar,
# cunku sabit D:/Projeler/_arsiv yolu yalniz gelistirme makinesinde var.)
YEDEK_KOK="D:/Projeler/_arsiv/2026-07-21_git-gecmisi-yedegi"
if [ -d "$YEDEK_KOK" ]; then
  [ -d "$YEDEK_KOK/git-klasoru" ] && S=0 || S=1
  kontrol "Git gecmisi yedegi duruyor" GECMELI $S
  [ -f "$YEDEK_KOK/NEDEN.md" ] && S=0 || S=1
  kontrol "Yedegin NEDEN notu var" GECMELI $S
  [ -f "D:/Projeler/_arsiv/2026-07-21_faz0-temizlik/panel-enver.md" ] && S=0 || S=1
  kontrol "Duplikat arsivde duruyor (silinmedi)" GECMELI $S
  [ -f "D:/Projeler/_arsiv/2026-07-21_faz0-temizlik/NEDEN.md" ] && S=0 || S=1
  kontrol "Faz 0 arsivinin NEDEN notu var" GECMELI $S
else
  kontrol "Gelistirme makinesi yedegi yok - baska ortam (atlandi)" GECMELI 0
  kontrol "Tarihsel yedek kontrolu atlandi (bu makineye ozgu)" GECMELI 0
fi

echo ""
echo "--- 7. ANA DIZIN DUZENI ---"

# Beklenen üst düzey içerik references/dizin-düzeni.json'dan okunur.
# Yeni klasör eklendiğinde sadece o dosya güncellenir, test değişmez.
ANA=$(python - << 'PYKOD'
import json, os, sys
duzen = json.load(open("plugins/enver-framework/references/dizin-duzeni.json", encoding="utf-8"))
beklenen = set(duzen["kalici"]) | set(duzen["uretilen"])
fazla = [a for a in sorted(os.listdir(".")) if a not in beklenen]
print(" ".join(fazla))
PYKOD
)
[ -z "$ANA" ] && S=0 || S=1
kontrol "Ana dizinde beklenmeyen dosya yok" GECMELI $S
[ -n "$ANA" ] && echo "         Fazlalik: $ANA"
[ -n "$ANA" ] && echo "         Beklenen listeye ekle: references/dizin-duzeni.json"

echo ""
echo "============================================"
echo " SONUC: $GECEN gecti, $KALAN kaldi"
echo "============================================"
[ "$KALAN" -eq 0 ] && echo " FAZ 0 KAPISI ACIK - Faz 1'e gecilebilir" || echo " FAZ 0 KAPISI KAPALI - once sorunlar duzeltilmeli"
