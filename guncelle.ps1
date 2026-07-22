# ================================================
#  Enver Framework - Guncelleme (Windows)
#  Gelistirici: Enver KOCAK | enverkocak.com
# ================================================

$ErrorActionPreference = "Stop"

$KaynakDizin = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host ""
Write-Host "========================================"
Write-Host "  ENVER FRAMEWORK - GUNCELLEME"
Write-Host "========================================"
Write-Host ""

# --- Depodan cek ---

Push-Location $KaynakDizin
try {
    Write-Host "[1/2] Depodan guncelleme aliniyor..."
    git pull --ff-only
    if ($LASTEXITCODE -ne 0) {
        Write-Host "UYARI: Guncelleme alinamadi. Yerel degisiklikler olabilir." -ForegroundColor Yellow
    }
}
finally {
    Pop-Location
}

# --- Kurulumu tekrar calistir ---

Write-Host ""
Write-Host "[2/2] Dosyalar yenileniyor..."
Write-Host ""

& (Join-Path $KaynakDizin "kurulum.ps1")

Write-Host ""
Write-Host "Guncelleme bitti. Simdi: /reload-plugins"
Write-Host ""
