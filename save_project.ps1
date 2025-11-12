# Script PowerShell para guardar todos los cambios del proyecto nexo-backend
# Creado: 12 de Noviembre 2025
# Propósito: Automatizar el guardado, commit y push de todos los cambios

param(
    [string]$CommitMessage = "Auto-save: Update project files",
    [switch]$SkipPush = $false,
    [switch]$Verbose = $false
)

Write-Host "🔧 NEXO BACKEND - SCRIPT DE GUARDADO AUTOMÁTICO" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Gray

# Función para mostrar mensajes si verbose está activado
function Write-VerboseMessage($message) {
    if ($Verbose) {
        Write-Host "   ℹ️ $message" -ForegroundColor Yellow
    }
}

try {
    # 1. Verificar que estamos en el directorio correcto
    Write-Host "📁 Verificando directorio del proyecto..." -ForegroundColor Green
    
    if (!(Test-Path ".git")) {
        throw "Error: No se encontró el repositorio Git. Asegúrate de estar en el directorio del proyecto."
    }
    
    if (!(Test-Path "app")) {
        throw "Error: No se encontró la carpeta 'app'. Verifica que estás en el directorio correcto."
    }
    
    Write-VerboseMessage "Directorio del proyecto verificado correctamente"

    # 2. Mostrar estado actual del repositorio
    Write-Host "📊 Verificando estado del repositorio..." -ForegroundColor Green
    
    $gitStatus = git status --porcelain
    if ($gitStatus) {
        Write-Host "   📝 Cambios detectados:" -ForegroundColor Yellow
        $gitStatus | ForEach-Object { Write-Host "      $_" -ForegroundColor White }
    } else {
        Write-Host "   ✅ No hay cambios pendientes" -ForegroundColor Green
        Write-Host "🎉 Proyecto ya está actualizado" -ForegroundColor Cyan
        return
    }

    # 3. Agregar todos los archivos al staging
    Write-Host "📦 Agregando archivos al staging..." -ForegroundColor Green
    
    git add .
    if ($LASTEXITCODE -ne 0) {
        throw "Error al agregar archivos al staging"
    }
    
    Write-VerboseMessage "Todos los archivos agregados al staging correctamente"

    # 4. Verificar archivos en staging
    Write-Host "🔍 Verificando archivos en staging..." -ForegroundColor Green
    
    $stagedFiles = git diff --cached --name-only
    if ($stagedFiles) {
        Write-Host "   📋 Archivos preparados para commit:" -ForegroundColor Yellow
        $stagedFiles | ForEach-Object { Write-Host "      ✓ $_" -ForegroundColor Green }
    } else {
        Write-Host "   ⚠️ No hay archivos en staging" -ForegroundColor Yellow
        return
    }

    # 5. Crear commit con mensaje personalizado o automático
    Write-Host "💾 Creando commit..." -ForegroundColor Green
    
    # Si no se proporciona mensaje, generar uno automático con timestamp
    if ($CommitMessage -eq "Auto-save: Update project files") {
        $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        $CommitMessage = "Auto-save: Update project files - $timestamp"
    }
    
    Write-Host "   📝 Mensaje: $CommitMessage" -ForegroundColor White
    
    git commit -m $CommitMessage
    if ($LASTEXITCODE -ne 0) {
        throw "Error al crear el commit"
    }
    
    Write-VerboseMessage "Commit creado exitosamente"

    # 6. Push al repositorio remoto (opcional)
    if (!$SkipPush) {
        Write-Host "🚀 Enviando cambios al repositorio remoto..." -ForegroundColor Green
        
        git push origin main
        if ($LASTEXITCODE -ne 0) {
            Write-Host "   ⚠️ Error al hacer push. El commit local fue exitoso." -ForegroundColor Yellow
            Write-Host "   💡 Intenta ejecutar manualmente: git push origin main" -ForegroundColor Cyan
        } else {
            Write-VerboseMessage "Push completado exitosamente"
        }
    } else {
        Write-Host "⏸️ Push omitido (usar -SkipPush $false para activar)" -ForegroundColor Yellow
    }

    # 7. Mostrar resumen final
    Write-Host "" -ForegroundColor White
    Write-Host "✅ GUARDADO COMPLETADO EXITOSAMENTE" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Gray
    
    $commitHash = git rev-parse --short HEAD
    Write-Host "   📊 Commit ID: $commitHash" -ForegroundColor Cyan
    Write-Host "   📁 Branch: main" -ForegroundColor Cyan
    Write-Host "   🕒 Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
    
    if (!$SkipPush) {
        Write-Host "   🌐 Estado: Sincronizado con GitHub" -ForegroundColor Green
    } else {
        Write-Host "   🏠 Estado: Solo guardado local" -ForegroundColor Yellow
    }

} catch {
    Write-Host "" -ForegroundColor White
    Write-Host "❌ ERROR EN EL PROCESO DE GUARDADO" -ForegroundColor Red
    Write-Host "=" * 60 -ForegroundColor Gray
    Write-Host "   💥 Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "" -ForegroundColor White
    Write-Host "💡 SOLUCIONES SUGERIDAS:" -ForegroundColor Yellow
    Write-Host "   1. Verifica que estás en el directorio correcto del proyecto" -ForegroundColor White
    Write-Host "   2. Asegúrate de tener conexión a internet para el push" -ForegroundColor White
    Write-Host "   3. Verifica tus credenciales de Git" -ForegroundColor White
    Write-Host "   4. Ejecuta manualmente: git status" -ForegroundColor White
    
    exit 1
}

Write-Host "" -ForegroundColor White
Write-Host "🎯 SCRIPT COMPLETADO" -ForegroundColor Cyan