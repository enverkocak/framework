#!/bin/bash
# ================================================
# Enver Framework - Güncelleme
# Depodan çekip kurulumu yeniler
# Mac ve Linux için
# ================================================

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo "  ENVER FRAMEWORK - GUNCELLEME"
echo "========================================"
echo ""

# --- Depodan çek ---
#
# Dal adı yazılmaz, takip edilen uzak dal ne ise o çekilir. Sabit
# "origin master" yazılıydı: herkese açık depo "main" dalında olduğu
# için güncelleme oradan hiç gelmiyor, komut her seferinde hata veriyordu.
echo "[1/2] Depodan guncelleme aliniyor..."
cd "$REPO_DIR"
if ! git pull --ff-only; then
    echo ""
    echo "UYARI: Guncelleme alinamadi. Sebep genelde biri:"
    echo "  - Ag yok"
    echo "  - Yerel degisiklik var (git durumunu kontrol et)"
    exit 1
fi

# --- Kurulumu tekrar çalıştır ---
#
# Kopyalama listesi tek yerde durur. Eskiden burada kurulum.sh'in bir
# kopyası vardı; ikisi zamanla ayrışınca güncelleme, kurulumun düzelttiği
# hataları geri getiriyordu.
echo ""
echo "[2/2] Dosyalar yenileniyor..."
echo ""
bash "$REPO_DIR/kurulum.sh"

echo ""
echo "Guncelleme bitti. Simdi: /reload-plugins"
echo ""
