#!/bin/bash
# ================================================
# Enver Framework - Otomatik Kurulum
# Mac ve Linux için
# ================================================

set -e

CLAUDE_DIR="$HOME/.claude"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo "  ENVER FRAMEWORK v1.0 - KURULUM"
echo "========================================"
echo ""
echo "Kaynak: $REPO_DIR"
echo "Hedef:  $CLAUDE_DIR"
echo ""

# .claude dizini var mı?
if [ ! -d "$CLAUDE_DIR" ]; then
    echo "HATA: $CLAUDE_DIR dizini bulunamadi!"
    echo "Once Claude Code'u kurun ve en az bir kez calistirin."
    exit 1
fi

# Dizinleri oluştur
mkdir -p "$CLAUDE_DIR/vault"
mkdir -p "$CLAUDE_DIR/bilgi"
mkdir -p "$CLAUDE_DIR/sablonlar"
mkdir -p "$CLAUDE_DIR/hooks"
mkdir -p "$CLAUDE_DIR/plugins/enver-framework"
mkdir -p "$CLAUDE_DIR/plugins/.claude-plugin"

# Dosyaları kopyala
echo "[1/6] Global CLAUDE.md kopyalaniyor..."
cp "$REPO_DIR/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md"

echo "[2/6] Vault dosyalari kopyalaniyor..."
cp -r "$REPO_DIR/vault/"* "$CLAUDE_DIR/vault/"

echo "[3/6] Bilgi deposu kopyalaniyor..."
cp -r "$REPO_DIR/bilgi/"* "$CLAUDE_DIR/bilgi/"

echo "[4/6] Sablonlar kopyalaniyor..."
cp -r "$REPO_DIR/sablonlar/"* "$CLAUDE_DIR/sablonlar/"

echo "[5/6] Hook'lar kopyalaniyor..."
cp -r "$REPO_DIR/hooks/"* "$CLAUDE_DIR/hooks/"
chmod +x "$CLAUDE_DIR/hooks/"*.py

echo "[6/6] Plugin kopyalaniyor..."
cp -r "$REPO_DIR/plugins/enver-framework/"* "$CLAUDE_DIR/plugins/enver-framework/"
cp -r "$REPO_DIR/plugins/.claude-plugin/"* "$CLAUDE_DIR/plugins/.claude-plugin/"

# Kancaları KAYDET - sadece kopyalamak yetmez, kayıt olmadan hiçbiri çalışmaz
echo ""
echo "Korumalar devreye aliniyor..."

KAYIT_BETIGI="$CLAUDE_DIR/plugins/enver-framework/scripts/kurulum/kanca-kaydet.py"
if [ -f "$KAYIT_BETIGI" ]; then
    python3 "$KAYIT_BETIGI" "$CLAUDE_DIR/hooks" || \
        echo "UYARI: Korumalar kaydedilemedi. Elle kontrol edin."
else
    echo "UYARI: Kayit betigi bulunamadi: $KAYIT_BETIGI"
fi

# Klon konumunu kaydet: açılışta "uzakta yeni sürüm var mı" kontrolü
# buradan okur. Yol ortam değişkeniyle geçirilir; tırnak sorunu olmaz.
if [ -d "$REPO_DIR/.git" ]; then
    mkdir -p "$CLAUDE_DIR/enver"
    ENVER_KAYNAK="$REPO_DIR" ENVER_HEDEF="$CLAUDE_DIR" python3 - <<'PYKOD' || true
import json, os
from pathlib import Path
p = Path(os.environ["ENVER_HEDEF"]) / "enver" / "kurulum-bilgisi.json"
p.write_text(json.dumps({"kaynak_dizin": os.environ["ENVER_KAYNAK"]},
                        ensure_ascii=False, indent=2), encoding="utf-8")
PYKOD
fi

echo ""
echo "========================================"
echo "  KURULUM TAMAMLANDI!"
echo "========================================"
echo ""
echo "Simdi su komutlari calistir:"
echo ""
echo "  /plugin marketplace add ~/.claude/plugins"
echo "  /plugin install enver-framework@enver-local"
echo "  /reload-plugins"
echo "  /index"
echo ""
echo "========================================"
