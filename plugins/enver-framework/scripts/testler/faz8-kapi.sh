#!/usr/bin/env bash
# Faz 8 kapi kontrolu - is ve musteri katmani

KOK="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && { pwd -W 2>/dev/null || pwd; })}"
P="$KOK/plugins/enver-framework"
I="$P/scripts/is"
cd "$KOK" || exit 1
mkdir -p _calisma

GECEN=0; KALAN=0
kontrol() {
  if [ "$2" -eq 0 ]; then echo "  [GECTI ] $1"; GECEN=$((GECEN+1));
  else echo "  [KALDI ] $1"; KALAN=$((KALAN+1)); fi
}

echo "============================================"
echo " FAZ 8 KAPI KONTROLU - Is ve musteri katmani"
echo "============================================"
echo ""

echo "--- 1. BETIK DOSYALARI ---"
for b in gorev.py takvim.py teslim.py; do
  [ -f "$I/$b" ] && kontrol "is/$b var" 0 || kontrol "is/$b var" 1
  python -c "import ast;ast.parse(open('$I/$b',encoding='utf-8').read())" 2>/dev/null \
    && kontrol "is/$b sozdizimi gecerli" 0 || kontrol "is/$b sozdizimi gecerli" 1
done

echo ""
echo "--- 2. GOREV TAKIBI (T42) ---"
python - << 'PY' 2>/dev/null && kontrol "Gorev eklenip okunabiliyor" 0 || kontrol "Gorev eklenip okunabiliyor" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/is")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
import gorev
g = gorev.ekle("Kapi testi gorevi", proje="kapi-testi", oncelik="normal", kaynak="kendi")
assert g["no"] > 0
bulunan = gorev.gorev_bul(g["no"])
assert bulunan and bulunan["baslik"] == "Kapi testi gorevi"
PY

python - << 'PY' 2>/dev/null && kontrol "Gorevin kaynagi kaydediliyor" 0 || kontrol "Gorevin kaynagi kaydediliyor" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/is")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
import gorev
g = gorev.ekle("Musteri istegi ornegi", proje="kapi-testi", kaynak="musteri")
assert g["kaynak"] == "musteri", g
# Kaynak alanlari tanimli
for k in ("musteri", "kendi", "hata", "bakim"):
    assert k in gorev.KAYNAKLAR
PY

python - << 'PY' 2>/dev/null && kontrol "Oncelik ve durum siralamasi dogru" 0 || kontrol "Oncelik ve durum siralamasi dogru" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/is")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
import gorev
gorev.ekle("Acil ornek", proje="kapi-testi-siralama", oncelik="acil")
gorev.ekle("Dusuk ornek", proje="kapi-testi-siralama", oncelik="dusuk")
liste = gorev.suzgecle(proje="kapi-testi-siralama", acik_olanlar=True)
assert liste[0]["oncelik"] == "acil", [g["oncelik"] for g in liste]
PY

python - << 'PY' 2>/dev/null && kontrol "Gorev bitirilebiliyor" 0 || kontrol "Gorev bitirilebiliyor" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/is")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
import gorev
g = gorev.ekle("Bitirilecek", proje="kapi-testi-bitir")
sonuc = gorev.durum_degistir(g["no"], "bitti")
assert sonuc["durum"] == "bitti" and sonuc["bitis"], sonuc
acik = gorev.suzgecle(proje="kapi-testi-bitir", acik_olanlar=True)
assert not acik, acik
PY

python "$I/gorev.py" ozet 2>/dev/null | grep -q "GÖREV ÖZETİ" \
  && kontrol "Gorev ozeti uretiliyor" 0 || kontrol "Gorev ozeti uretiliyor" 1

echo ""
echo "--- 3. HIZMET TAKVIMI (T74) ---"
python - << 'PY' 2>/dev/null && kontrol "Uyari esikleri dogru hesaplaniyor" 0 || kontrol "Uyari esikleri dogru hesaplaniyor" 1
import sys
from datetime import date, timedelta
sys.path.insert(0, "plugins/enver-framework/scripts/is")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
import takvim

bugun = date.today()
olcumler = [
    (bugun - timedelta(days=5), "kritik"),
    (bugun + timedelta(days=3), "acil"),
    (bugun + timedelta(days=20), "dikkat"),
    (bugun + timedelta(days=45), "yaklasiyor"),
    (bugun + timedelta(days=200), "gecerli"),
]
for tarih, beklenen in olcumler:
    durum, kalan = takvim.durum_hesapla(tarih.isoformat())
    assert durum == beklenen, (tarih, durum, beklenen)
PY

python - << 'PY' 2>/dev/null && kontrol "Bozuk tarih cokme yapmiyor" 0 || kontrol "Bozuk tarih cokme yapmiyor" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/is")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
import takvim
durum, kalan = takvim.durum_hesapla("olmayan-tarih")
assert kalan is None, (durum, kalan)
durum, kalan = takvim.durum_hesapla(None)
assert kalan is None
PY

python - << 'PY' 2>/dev/null && kontrol "Kayitlar aciliyet sirasinda geliyor" 0 || kontrol "Kayitlar aciliyet sirasinda geliyor" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/is")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
import takvim
liste = takvim.kayitlar()
assert liste, "kayit yok"
siralar = [takvim.DURUM_SIRASI[k["durum"]] for k in liste]
assert siralar == sorted(siralar), siralar
PY

python "$I/takvim.py" liste --sinir 5 > _calisma/tk.txt 2>&1
grep -q "HİZMET TAKVİMİ" _calisma/tk.txt \
  && kontrol "Takvim listelenebiliyor" 0 || kontrol "Takvim listelenebiliyor" 1

python - << 'PY' 2>/dev/null && kontrol "Sertifika taramasi takvime beslenebiliyor" 0 || kontrol "Sertifika taramasi takvime beslenebiliyor" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/is")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
import takvim
# Ikinci cagri ayni kayitlari TEKRAR eklememeli
once = len(takvim.oku()["kayitlar"])
takvim.sertifikadan_al()
sonra = len(takvim.oku()["kayitlar"])
takvim.sertifikadan_al()
son = len(takvim.oku()["kayitlar"])
assert son == sonra, (once, sonra, son)
PY

echo ""
echo "--- 4. TESLIM PAKETI (T43/T73/T72) ---"
rm -rf _calisma/teslim-kapi 2>/dev/null
python "$I/teslim.py" hazirla --hedef _calisma/teslim-kapi > _calisma/ts.txt 2>&1 \
  && kontrol "Teslim paketi uretiliyor" 0 || kontrol "Teslim paketi uretiliyor" 1

for d in kullanim-kilavuzu teknik-belge erisim-bilgileri teslim-tutanagi kisisel-veri-kontrol-listesi; do
  [ -f "_calisma/teslim-kapi/$d.md" ] && kontrol "$d.md uretildi" 0 || kontrol "$d.md uretildi" 1
done

python - << 'PY' 2>/dev/null && kontrol "Erisim belgesinde PAROLA YOK" 0 || kontrol "Erisim belgesinde PAROLA YOK" 1
import re
from pathlib import Path
icerik = Path("_calisma/teslim-kapi/erisim-bilgileri.md").read_text(encoding="utf-8")
# Parola gorunumlu deger olmamali
assert not re.search(r"(?i)(parola|password|sifre)\s*[:=]\s*\S{6,}", icerik), icerik[:300]
# Ama parolanin NEREDE oldugunu soylemeli
assert "kasa" in icerik.lower(), icerik[:300]
PY

python - << 'PY' 2>/dev/null && kontrol "Teknik belge parola icermedigini soyluyor" 0 || kontrol "Teknik belge parola icermedigini soyluyor" 1
from pathlib import Path
icerik = Path("_calisma/teslim-kapi/teknik-belge.md").read_text(encoding="utf-8")
assert "parola bulunmaz" in icerik.lower(), icerik[-400:]
PY

python - << 'PY' 2>/dev/null && kontrol "Tutanakta kapsam disi bolumu var" 0 || kontrol "Tutanakta kapsam disi bolumu var" 1
from pathlib import Path
icerik = Path("_calisma/teslim-kapi/teslim-tutanagi.md").read_text(encoding="utf-8")
assert "Kapsam dışı" in icerik
assert "İmza" in icerik
PY

python - << 'PY' 2>/dev/null && kontrol "Kisisel veri listesinde en az 8 madde var" 0 || kontrol "Kisisel veri listesinde en az 8 madde var" 1
import sys
sys.path.insert(0, "plugins/enver-framework/scripts/is")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
sys.path.insert(0, "plugins/enver-framework/scripts/projeler")
import teslim
assert len(teslim.KVKK_MADDELERI) >= 8, len(teslim.KVKK_MADDELERI)
from pathlib import Path
icerik = Path("_calisma/teslim-kapi/kisisel-veri-kontrol-listesi.md").read_text(encoding="utf-8")
assert "hukuki görüş değildir" in icerik
PY

python "$I/teslim.py" kontrol > _calisma/tk2.txt 2>&1
grep -q "TESLİME HAZIR MI" _calisma/tk2.txt \
  && kontrol "Teslim hazirlik kontrolu calisiyor" 0 || kontrol "Teslim hazirlik kontrolu calisiyor" 1

python - << 'PY' 2>/dev/null && kontrol "Acil gorev varsa teslim kontrolu DURUYOR" 0 || kontrol "Acil gorev varsa teslim kontrolu DURUYOR" 1
import subprocess, sys
sys.path.insert(0, "plugins/enver-framework/scripts/is")
sys.path.insert(0, "plugins/enver-framework/scripts/ortak")
sys.path.insert(0, "plugins/enver-framework/scripts/hafiza")
import gorev, yollar
proje = yollar.proje_adi()
g = gorev.ekle("Gecici acil kapi testi", proje=proje, oncelik="acil")
try:
    p = subprocess.run([sys.executable, "plugins/enver-framework/scripts/is/teslim.py",
                        "kontrol"], capture_output=True, text=True, encoding="utf-8")
    assert "Açık acil görev" in p.stdout and "KALDI" in p.stdout, p.stdout
finally:
    gorev.durum_degistir(g["no"], "iptal")
PY

echo ""
echo "--- 5. GERILEME TESTLERI ---"
if [ -n "$ENVER_GERILEME_ATLA" ]; then
  echo "  (gerileme testleri atlandi - ust testten cagrildi)"
else
export ENVER_GERILEME_ATLA=1
for f in 0 1 2 3 4 5 6 7; do
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
[ "$KALAN" -eq 0 ] && echo " FAZ 8 KAPISI ACIK" || echo " FAZ 8 KAPISI KAPALI"
