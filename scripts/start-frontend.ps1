# Script PowerShell pour lancer le serveur frontend CV Analyzer
# Usage: .\start-frontend.ps1

Write-Host "🚀 Démarrage du serveur frontend CV Analyzer..." -ForegroundColor Green

# Aller dans le dossier frontend
$frontendPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $frontendPath

# Vérifier si Python est disponible
try {
    $pythonVersion = py --version 2>&1
    Write-Host "✓ Python trouvé: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python n'est pas installé ou n'est pas dans le PATH" -ForegroundColor Red
    Write-Host "Essayez d'utiliser python au lieu de py" -ForegroundColor Yellow
    exit 1
}

# Vérifier que les fichiers existent
if (-not (Test-Path "index.html")) {
    Write-Host "❌ index.html introuvable!" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "app.js")) {
    Write-Host "❌ app.js introuvable!" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "styles.css")) {
    Write-Host "⚠️  styles.css introuvable (optionnel)" -ForegroundColor Yellow
}

# Lancer le serveur
Write-Host "`n🌐 Lancement du serveur sur http://localhost:3000" -ForegroundColor Cyan
Write-Host "Appuyez sur Ctrl+C pour arrêter le serveur`n" -ForegroundColor Yellow
Write-Host "⚠️  Assurez-vous que le backend est lancé sur http://localhost:8000" -ForegroundColor Yellow
Write-Host ""

py -m http.server 3000
