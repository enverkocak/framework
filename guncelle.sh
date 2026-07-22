#!/bin/bash
# ================================================
# Enver Framework - Güncelleme
# GitHub'dan çekip dosyaları günceller
# Mac ve Linux için
# ================================================

set -e

CLAUDE_DIR="$HOME/.claude"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo "  ENVER FRAMEWORK - GUNCELLEME"
echo "========================================"

# Git pull
echo "[1/3] GitHub'dan cekiliyor..."
cd "$REPO_DIR"
git pull origin master

# Dosyaları kopyala
echo "[2/3] Dosyalar guncelleniyor..."
cp "$REPO_DIR/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md"
cp -r "$REPO_DIR/vault/"* "$CLAUDE_DIR/vault/"
cp -r "$REPO_DIR/bilgi/"* "$CLAUDE_DIR/bilgi/"
cp -r "$REPO_DIR/sablonlar/"* "$CLAUDE_DIR/sablonlar/"
cp -r "$REPO_DIR/hooks/"* "$CLAUDE_DIR/hooks/"
cp -r "$REPO_DIR/plugins/enver-framework/"* "$CLAUDE_DIR/plugins/enver-framework/"
cp -r "$REPO_DIR/plugins/.claude-plugin/"* "$CLAUDE_DIR/plugins/.claude-plugin/"

echo "[3/3] Tamamlandi!"
echo ""
echo "Claude Code'da /reload-plugins calistir."
echo "========================================"
