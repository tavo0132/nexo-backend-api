# Script PowerShell Simple para guardar cambios del proyecto
# Uso: .\save_simple.ps1 [mensaje_del_commit]

param(
    [string]$CommitMessage = "Auto-save: Update project files"
)

Write-Host "NEXO BACKEND - GUARDADO AUTOMATICO" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Gray

try {
    # Verificar directorio del proyecto
    if (!(Test-Path ".git")) {
        Write-Host "ERROR: No se encontro el repositorio Git" -ForegroundColor Red
        exit 1
    }
    
    # Verificar cambios
    Write-Host "Verificando cambios..." -ForegroundColor Green
    $gitStatus = git status --porcelain
    
    if (!$gitStatus) {
        Write-Host "No hay cambios pendientes" -ForegroundColor Green
        Write-Host "Proyecto ya esta actualizado" -ForegroundColor Cyan
        exit 0
    }
    
    # Mostrar archivos modificados
    Write-Host "Cambios detectados:" -ForegroundColor Yellow
    git status --short
    
    # Agregar archivos
    Write-Host "Agregando archivos..." -ForegroundColor Green
    git add .
    
    # Crear commit
    if ($CommitMessage -eq "Auto-save: Update project files") {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $CommitMessage = "Auto-save: Update project files - $timestamp"
    }
    
    Write-Host "Creando commit con mensaje: $CommitMessage" -ForegroundColor Green
    git commit -m $CommitMessage
    
    # Push
    Write-Host "Enviando cambios a GitHub..." -ForegroundColor Green
    git push origin main
    
    # Resumen final
    Write-Host ""
    Write-Host "GUARDADO COMPLETADO EXITOSAMENTE" -ForegroundColor Green
    Write-Host "=================================" -ForegroundColor Gray
    
    $commitHash = git rev-parse --short HEAD
    Write-Host "Commit ID: $commitHash" -ForegroundColor Cyan
    Write-Host "Branch: main" -ForegroundColor Cyan
    Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
    
} catch {
    Write-Host ""
    Write-Host "ERROR EN EL PROCESO" -ForegroundColor Red
    Write-Host "Mensaje: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}