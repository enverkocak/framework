#!/bin/bash
# ================================================
# Enver Framework - Otomatik Kurulum
# Mac ve Linux için
# ================================================

set -e

CLAUDE_DIR="$HOME/.claude"
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "========================================"
echo "  ENVER FRAMEWORK - KURULUM"
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
mkdir -p "$CLAUDE_DIR/plugins/enver-framework"
mkdir -p "$CLAUDE_DIR/plugins/.claude-plugin"

# Kaynakta olmayan klasör kurulumu DURDURMAZ, atlanır.
#
# Eskiden kasa ve bilgi deposu koşulsuz kopyalanıyordu. Herkese açık
# sürümde bu iki klasör YOKTUR (kişisel veri paylaşılmaz), yani kopyalama
# hata veriyor ve "set -e" kurulumu oracıkta kesiyordu: eklenti hiç
# kopyalanmadan çıkılıyordu. Windows tarafı zaten atlayıp geçiyordu;
# iki taraf artık aynı davranıyor.
kopyala() {
    local ad="$1" kaynak="$2" hedef="$3" sira="$4"

    echo "[$sira] $ad"

    if [ ! -d "$kaynak" ]; then
        echo "      atlandi (kaynak yok)"
        return 0
    fi

    # "dizin/." biçimi gizli dosyaları da alır ve boşluklu yolu bozmaz.
    cp -r "$kaynak/." "$hedef/"
}

# Kurulu kurallar dosyasının üzerine yazmadan önce yedeğini al.
#
# Kullanıcı kendi kimliğini ve kurallarını bu dosyaya işlemiş olabilir.
# Güncelleme onu sessizce silerse kayıp geri getirilemez; yedek yalnız
# içerik gerçekten farklıysa alınır, aynı dosya için çöp üretilmez.
yedekle_kurallar() {
    local hedef="$CLAUDE_DIR/CLAUDE.md"
    local kaynak="$REPO_DIR/CLAUDE.md"

    [ -f "$hedef" ] || return 0
    cmp -s "$hedef" "$kaynak" 2>/dev/null && return 0

    local yedek_dizin="$CLAUDE_DIR/enver/yedek"
    local damga
    damga="$(date +%Y%m%d-%H%M%S)"

    mkdir -p "$yedek_dizin"
    cp "$hedef" "$yedek_dizin/CLAUDE.$damga.md"
    echo "      onceki dosya yedeklendi: enver/yedek/CLAUDE.$damga.md"
}

# Dosyaları kopyala
echo "[1/5] Global CLAUDE.md kopyalaniyor..."
yedekle_kurallar
cp "$REPO_DIR/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md"

kopyala "Kasa dosyalari kopyalaniyor..."   "$REPO_DIR/vault"     "$CLAUDE_DIR/vault"     "2/5"
kopyala "Bilgi deposu kopyalaniyor..."     "$REPO_DIR/bilgi"     "$CLAUDE_DIR/bilgi"     "3/5"
kopyala "Sablonlar kopyalaniyor..."        "$REPO_DIR/sablonlar" "$CLAUDE_DIR/sablonlar" "4/5"

echo "[5/5] Plugin kopyalaniyor (korumalar plugin ile gelir)..."
cp -r "$REPO_DIR/plugins/enver-framework/." "$CLAUDE_DIR/plugins/enver-framework/"
cp -r "$REPO_DIR/plugins/.claude-plugin/." "$CLAUDE_DIR/plugins/.claude-plugin/"

# Korumalar (kancalar) artik plugin'in hooks.json'u ile gelir. Kurulum
# ayri kanca kaydi YAPMAZ - "/plugin install" calistirilinca devreye girer.
# Boylece tek teslim vardir; cift kayit (cift calisma) olmaz.

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
