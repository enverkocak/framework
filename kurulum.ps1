# ================================================
#  Enver Framework - Kurulum (Windows)
#  Gelistirici: Enver KOCAK | enverkocak.com
# ================================================

$ErrorActionPreference = "Stop"

$KaynakDizin = Split-Path -Parent $MyInvocation.MyCommand.Path
$HedefDizin  = Join-Path $env:USERPROFILE ".claude"

Write-Host ""
Write-Host "========================================"
Write-Host "  ENVER FRAMEWORK - KURULUM"
Write-Host "========================================"
Write-Host ""
Write-Host "  Kaynak : $KaynakDizin"
Write-Host "  Hedef  : $HedefDizin"
Write-Host ""

# --- On kontroller ---

if (-not (Test-Path $HedefDizin)) {
    Write-Host "HATA: $HedefDizin bulunamadi." -ForegroundColor Red
    Write-Host "Once ana uygulamayi kurup en az bir kez calistirin."
    exit 1
}

$Python = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $Python) {
    $Python = (Get-Command py -ErrorAction SilentlyContinue).Source
}
if (-not $Python) {
    Write-Host "HATA: Python bulunamadi. Kancalar Python ile calisiyor." -ForegroundColor Red
    exit 1
}

# --- Dizinler ---

$Dizinler = @(
    "vault", "bilgi", "sablonlar", "hooks",
    "plugins\enver-framework", "plugins\.claude-plugin"
)
foreach ($d in $Dizinler) {
    $tam = Join-Path $HedefDizin $d
    if (-not (Test-Path $tam)) {
        New-Item -ItemType Directory -Path $tam -Force | Out-Null
    }
}

# --- Kopyalama ---

function Kopyala {
    param($Ad, $Kaynak, $Hedef, $Sira)

    Write-Host "[$Sira] $Ad"

    if (-not (Test-Path $Kaynak)) {
        Write-Host "      atlandi (kaynak yok)" -ForegroundColor DarkYellow
        return
    }

    Copy-Item -Path $Kaynak -Destination $Hedef -Recurse -Force
}

Kopyala "Kurallar dosyasi" (Join-Path $KaynakDizin "CLAUDE.md") (Join-Path $HedefDizin "CLAUDE.md") "1/6"
Kopyala "Kasa"             (Join-Path $KaynakDizin "vault\*")     (Join-Path $HedefDizin "vault\") "2/6"
Kopyala "Bilgi deposu"     (Join-Path $KaynakDizin "bilgi\*")     (Join-Path $HedefDizin "bilgi\") "3/6"
Kopyala "Sablonlar"        (Join-Path $KaynakDizin "sablonlar\*") (Join-Path $HedefDizin "sablonlar\") "4/6"
Kopyala "Korumalar"        (Join-Path $KaynakDizin "hooks\*")     (Join-Path $HedefDizin "hooks\") "5/6"

Write-Host "[6/6] Eklenti"
Copy-Item -Path (Join-Path $KaynakDizin "plugins\enver-framework\*") `
          -Destination (Join-Path $HedefDizin "plugins\enver-framework\") -Recurse -Force
Copy-Item -Path (Join-Path $KaynakDizin "plugins\.claude-plugin\*") `
          -Destination (Join-Path $HedefDizin "plugins\.claude-plugin\") -Recurse -Force

# --- Kancalari KAYDET (kopyalamak yetmez) ---

Write-Host ""
Write-Host "Korumalar devreye aliniyor..."

$KayitBetigi = Join-Path $HedefDizin "plugins\enver-framework\scripts\kurulum\kanca-kaydet.py"
$KancaDizini = Join-Path $HedefDizin "hooks"

& $Python $KayitBetigi $KancaDizini
if ($LASTEXITCODE -ne 0) {
    Write-Host "UYARI: Korumalar kaydedilemedi. Elle kontrol edin." -ForegroundColor Yellow
}

# --- Bitis ---

Write-Host ""
Write-Host "========================================"
Write-Host "  KURULUM TAMAMLANDI"
Write-Host "========================================"
Write-Host ""
Write-Host "Simdi su komutlari calistirin:"
Write-Host ""
Write-Host "  /plugin marketplace add ~/.claude/plugins"
Write-Host "  /plugin install enver-framework@enver-local"
Write-Host "  /reload-plugins"
Write-Host "  /index"
Write-Host ""
