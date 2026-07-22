#!/usr/bin/env bash
# Komple test - bütün kapı testleri, senaryolar ve sağlık kontrolü
#
# Her test BIR KEZ çalışır. Faz testleri normalde kendinden öncekileri de
# çalıştırır; burada ENVER_GERILEME_ATLA ile o tekrar kapatılır.
#
# Kullanım:
#   bash tümünü-çalıştır.sh [proje-kökü]

KOK="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && { pwd -W 2>/dev/null || pwd; })}"
P="$KOK/plugins/enver-framework"
T="$P/scripts/testler"
cd "$KOK" || exit 1
mkdir -p _calisma/komple

export ENVER_GERILEME_ATLA=1

# Kurulmamış kopyada kullanım durumu testleri anlamsızdır.
# Hafıza, arşiv, tasarım kimliği ve ayar dosyası kurulumda ve
# kullanımda oluşur; yokları bozukluk değil, henüz kurulmamışlıktır.
# Bunu 62 "hata" olarak raporlamak yeni kullanıcıyı yanıltır.
YAPISAL_MI=0
if [ ! -f ".claude/settings.json" ]; then
  YAPISAL_MI=1
fi

BASLANGIC=$(date +%s)

TOPLAM_GECEN=0
TOPLAM_KALAN=0
BOLUM_SAYISI=0
BOZUK_BOLUMLER=""

echo "=================================================================="
echo " KOMPLE TEST"
echo "=================================================================="
echo " Proje : $KOK"
echo " Tarih : $(date '+%Y-%m-%d %H:%M')"
echo "=================================================================="
echo ""

# ---------------------------------------------------------------- kapı testleri

echo "FAZ KAPI TESTLERI"
echo "------------------------------------------------------------------"

FAZ_LISTESI="0 1 2 3 4 5 6 7 8 9 10 11"
if [ "$YAPISAL_MI" -eq 1 ]; then
  FAZ_LISTESI="0"
  echo "  Kurulum yapilmamis - sadece yapisal kapi calisiyor."
fi

for f in $FAZ_LISTESI; do
  DOSYA="$T/faz$f-kapi.sh"
  if [ ! -f "$DOSYA" ]; then
    printf "  Faz %-3s %s\n" "$f" "TEST DOSYASI YOK"
    BOZUK_BOLUMLER="$BOZUK_BOLUMLER faz$f"
    continue
  fi

  CIKTI="_calisma/komple/faz$f.txt"
  bash "$DOSYA" "$KOK" > "$CIKTI" 2>&1

  SONUC=$(grep -oE "SONUC: [0-9]+ gecti, [0-9]+ kaldi" "$CIKTI" | tail -1)
  GECEN=$(echo "$SONUC" | grep -oE "[0-9]+ gecti" | grep -oE "[0-9]+")
  KALAN=$(echo "$SONUC" | grep -oE "[0-9]+ kaldi" | grep -oE "[0-9]+")

  GECEN=${GECEN:-0}
  KALAN=${KALAN:-0}

  TOPLAM_GECEN=$((TOPLAM_GECEN + GECEN))
  TOPLAM_KALAN=$((TOPLAM_KALAN + KALAN))
  BOLUM_SAYISI=$((BOLUM_SAYISI + 1))

  BASLIK=$(grep -oE "FAZ $f KAPI KONTROLU - .*" "$CIKTI" | head -1 | sed "s/FAZ $f KAPI KONTROLU - //")

  if [ "$KALAN" -eq 0 ] && [ "$GECEN" -gt 0 ]; then
    printf "  [GECTI ] Faz %-3s %-32s %3s kontrol\n" "$f" "$BASLIK" "$GECEN"
  else
    printf "  [KALDI ] Faz %-3s %-32s %3s gecti, %s KALDI\n" "$f" "$BASLIK" "$GECEN" "$KALAN"
    BOZUK_BOLUMLER="$BOZUK_BOLUMLER faz$f"
  fi
done

# ---------------------------------------------------------------- senaryolar

echo ""
echo "SENARYO TESTLERI"
echo "------------------------------------------------------------------"

senaryo() {
  ADI="$1"
  BETIK="$2"
  CIKTI="_calisma/komple/$3.txt"

  if [ ! -f "$BETIK" ]; then
    printf "  [ ?    ] %-40s dosya yok\n" "$ADI"
    return
  fi

  python "$BETIK" "$KOK" > "$CIKTI" 2>&1
  SONUC=$(grep -oE "[0-9]+ geçti, [0-9]+ kaldı" "$CIKTI" | tail -1)
  GECEN=$(echo "$SONUC" | grep -oE "^[0-9]+")
  KALAN=$(echo "$SONUC" | grep -oE "[0-9]+ kaldı" | grep -oE "[0-9]+")

  GECEN=${GECEN:-0}
  KALAN=${KALAN:-0}

  TOPLAM_GECEN=$((TOPLAM_GECEN + GECEN))
  TOPLAM_KALAN=$((TOPLAM_KALAN + KALAN))
  BOLUM_SAYISI=$((BOLUM_SAYISI + 1))

  if [ "$KALAN" -eq 0 ] && [ "$GECEN" -gt 0 ]; then
    printf "  [GECTI ] %-40s %3s senaryo\n" "$ADI" "$GECEN"
  else
    printf "  [KALDI ] %-40s %3s gecti, %s KALDI\n" "$ADI" "$GECEN" "$KALAN"
    BOZUK_BOLUMLER="$BOZUK_BOLUMLER $3"
  fi
}

senaryo "Korumalar" "$T/koruma-testleri.py" "koruma"
senaryo "Turkce yazim" "$T/yazim-testleri.py" "yazim"
senaryo "Tam yetki guvenligi" "$T/tam-yetki-testleri.py" "tam-yetki"

# ------------------------------------------------------------ belge yolları

# Yol denetimi kurulum durumundan bağımsızdır: belgelerin doğruluğu
# kurulmuş olmayı gerektirmez. Taze kopyada da çalışır.
echo ""
echo "BELGE YOLLARI"
echo "------------------------------------------------------------------"
python "$T/yol-denetim.py" "$KOK" > _calisma/komple/yol.txt 2>&1
if [ $? -eq 0 ]; then
  printf "  [GECTI ] Belgelerdeki yollar dogru
"
  TOPLAM_GECEN=$((TOPLAM_GECEN + 1))
else
  printf "  [KALDI ] Belgelerde hatali yol var
"
  grep -A 2 "satır" _calisma/komple/yol.txt | head -12
  TOPLAM_KALAN=$((TOPLAM_KALAN + 1))
  BOZUK_BOLUMLER="$BOZUK_BOLUMLER yol"
fi

# ---------------------------------------------------------------- sağlık

echo ""
echo "SAGLIK KONTROLU"
echo "------------------------------------------------------------------"

if [ "$YAPISAL_MI" -eq 1 ]; then
  echo "  Kurulum yapilmamis - saglik kontrolu atlandi."
  SAGLIK_KODU=0
  SAGLIK_OZET="atlandi"
else
python "$P/scripts/saglik/saglik.py" bak > _calisma/komple/saglik.txt 2>&1
SAGLIK_KODU=$?
SAGLIK_OZET=$(grep -oE "[0-9]+ iyi · [0-9]+ uyarı · [0-9]+ bozuk" _calisma/komple/saglik.txt | tail -1)

if [ "$SAGLIK_KODU" -eq 0 ]; then
  printf "  [GECTI ] %s\n" "$SAGLIK_OZET"
else
  printf "  [KALDI ] %s\n" "$SAGLIK_OZET"
  grep "BOZUK" _calisma/komple/saglik.txt | head -5
  BOZUK_BOLUMLER="$BOZUK_BOLUMLER saglik"
fi
fi

# ---------------------------------------------------------------- işlevsel

echo ""
echo "ISLEVSEL DENETIMLER"
echo "------------------------------------------------------------------"

# Bazı komutlar çıkış kodunu HATA değil SINYAL olarak kullanır:
# takvim.py acil kayıt varsa 1 döner, kontrol.py bulgu varsa 1 döner.
# Bu komutlar için ölçülecek şey ÇALIŞIP çalışmadığı, ne döndüğü değil.
islevsel_sinyal() {
  ADI="$1"
  shift
  CIKTI=$("$@" 2>&1)
  if [ -n "$CIKTI" ]; then
    printf "  [GECTI ] %s
" "$ADI"
    TOPLAM_GECEN=$((TOPLAM_GECEN + 1))
  else
    printf "  [KALDI ] %s (cikti uretmedi)
" "$ADI"
    TOPLAM_KALAN=$((TOPLAM_KALAN + 1))
    BOZUK_BOLUMLER="$BOZUK_BOLUMLER islevsel"
  fi
}

islevsel() {
  ADI="$1"
  shift
  if "$@" > /dev/null 2>&1; then
    printf "  [GECTI ] %s\n" "$ADI"
    TOPLAM_GECEN=$((TOPLAM_GECEN + 1))
  else
    printf "  [KALDI ] %s\n" "$ADI"
    TOPLAM_KALAN=$((TOPLAM_KALAN + 1))
    BOZUK_BOLUMLER="$BOZUK_BOLUMLER islevsel"
  fi
}

if [ "$YAPISAL_MI" -eq 1 ]; then
  echo "  Kurulum yapilmamis - islevsel denetimler atlandi."
  echo "  Bu denetimler proje kaydi, faz plani ve tasarim kimligi ister;"
  echo "  bunlar kurulum ve ilk kullanimda olusur."
else
islevsel "Komut rehberi uretiliyor" python "$P/scripts/index-uret.py"
islevsel "Proje panosu calisiyor" python "$P/scripts/projeler/kayit.py" liste
islevsel "Sistem semasi uretiliyor" python "$P/scripts/projeler/sema.py" uret --hedef _calisma/komple/sema.html
islevsel "Faz durumu okunuyor" python "$P/scripts/faz/faz.py" durum
islevsel "Tasarim kimligi gecerli" python "$P/scripts/tasarim/kimlik.py" denetle
islevsel "Imza on planda degil" python "$P/scripts/tasarim/imza.py" denetle
islevsel "Cihaz katmani uretiliyor" python "$P/scripts/tasarim/cihaz.py" css
islevsel "Arama calisiyor" python "$P/scripts/ara.py" kasa
islevsel "Gorev ozeti uretiliyor" python "$P/scripts/is/gorev.py" ozet
islevsel_sinyal "Hizmet takvimi okunuyor" python "$P/scripts/is/takvim.py" liste --sinir 3
islevsel "Envanter listeleniyor" python "$P/scripts/saha/envanter.py" liste --sinir 3
islevsel "Yedek listesi okunuyor" python "$P/scripts/sunucu/yedek.py" liste --sinir 3
islevsel "Kurulum ortami hazir" python "$P/scripts/kurulum/sihirbaz.py" kontrol
islevsel "Senkron durumu okunuyor" python "$P/scripts/senkron/senkron.py" durum
islevsel "Makine taniniyor" python "$P/scripts/senkron/makine.py" durum
fi

# ---------------------------------------------------------------- güvenlik

echo ""
echo "GUVENLIK DOGRULAMALARI"
echo "------------------------------------------------------------------"

guvenlik() {
  ADI="$1"
  shift
  if "$@" > /dev/null 2>&1; then
    printf "  [KALDI ] %s\n" "$ADI"
    TOPLAM_KALAN=$((TOPLAM_KALAN + 1))
    BOZUK_BOLUMLER="$BOZUK_BOLUMLER guvenlik"
  else
    printf "  [GECTI ] %s\n" "$ADI"
    TOPLAM_GECEN=$((TOPLAM_GECEN + 1))
  fi
}

# Bu komutlar BAŞARISIZ olmalı
guvenlik "Kasa parolasiz acilmiyor" python "$P/scripts/kasa/kasa.py" liste
guvenlik "Kasa yanlis parolayi reddediyor" python "$P/scripts/kasa/kasa.py" ac --parola "kesinlikle-yanlis-parola-98765"

python - << 'PY' > /dev/null 2>&1
import subprocess, sys
from pathlib import Path
kok = Path(".")
# Kasa ve günlük depoda izlenmemeli
sonuc = subprocess.run(["git", "ls-files"], capture_output=True, text=True, encoding="utf-8")
izlenen = sonuc.stdout.splitlines()
for yol in izlenen:
    assert not yol.startswith(("kasa/", "vault/", "gunluk/", "_arsiv/")), yol
sys.exit(0)
PY
if [ $? -eq 0 ]; then
  printf "  [GECTI ] Kasa ve ham gunluk depoda izlenmiyor\n"
  TOPLAM_GECEN=$((TOPLAM_GECEN + 1))
else
  printf "  [KALDI ] Kasa ve ham gunluk depoda izlenmiyor\n"
  TOPLAM_KALAN=$((TOPLAM_KALAN + 1))
  BOZUK_BOLUMLER="$BOZUK_BOLUMLER guvenlik"
fi

python - << 'PY' > /dev/null 2>&1
import re, subprocess, sys
sonuc = subprocess.run(["git", "ls-files"], capture_output=True, text=True, encoding="utf-8")
desen = re.compile(r'(?i)(parola|password|sifre|secret|api[_-]?key|token)\s*[:=]\s*["\'][^"\']{8,}["\']')
yer_tutucu = re.compile(r"(?i)(degistir|example|ornek|placeholder|xxx|your[_-]|os\.environ|process\.env)")
from pathlib import Path
for yol in sonuc.stdout.splitlines():
    p = Path(yol)
    if not p.is_file() or p.suffix.lower() in (".png", ".jpg", ".ico", ".woff"):
        continue
    if "testler" in yol or "yazim-kontrol" in yol or "kasa-koruma" in yol:
        continue
    icerik = p.read_text(encoding="utf-8", errors="ignore")
    for e in desen.finditer(icerik):
        if not yer_tutucu.search(e.group(0)):
            print(f"{yol}: {e.group(0)[:60]}")
            sys.exit(1)
sys.exit(0)
PY
if [ $? -eq 0 ]; then
  printf "  [GECTI ] Depoda acikta sir yok\n"
  TOPLAM_GECEN=$((TOPLAM_GECEN + 1))
else
  printf "  [KALDI ] Depoda acikta sir VAR\n"
  TOPLAM_KALAN=$((TOPLAM_KALAN + 1))
  BOZUK_BOLUMLER="$BOZUK_BOLUMLER guvenlik"
fi

# ---------------------------------------------------------------- sonuç

BITIS=$(date +%s)
SURE=$((BITIS - BASLANGIC))

unset ENVER_GERILEME_ATLA

echo ""
echo "=================================================================="
echo " SONUC"
echo "=================================================================="
echo "  Gecen  : $TOPLAM_GECEN"
echo "  Kalan  : $TOPLAM_KALAN"
echo "  Sure   : $SURE saniye"
echo "=================================================================="

if [ "$TOPLAM_KALAN" -eq 0 ]; then
  echo " HEPSI GECTI"
  exit 0
fi

echo " KALAN VAR:$BOZUK_BOLUMLER"
echo ""
echo " Ayrintilar: _calisma/komple/ altinda"
exit 1
