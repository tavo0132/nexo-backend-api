# Nexo Backend - Scripts de Guardado Automático

## 📝 Descripción
Scripts para automatizar el proceso de guardado de todos los cambios del proyecto, incluyendo:
- Verificación del estado del repositorio
- Agregar archivos al staging de Git
- Crear commit con mensaje personalizado
- Push al repositorio remoto (GitHub)
- Manejo de errores y validaciones

## 🚀 Uso Rápido

### Windows (PowerShell)
```powershell
# Guardado básico con mensaje automático
.\save_project.ps1

# Guardado con mensaje personalizado
.\save_project.ps1 -CommitMessage "feat: Add new friendship feature"

# Solo commit local (sin push)
.\save_project.ps1 -SkipPush

# Modo verbose (más información)
.\save_project.ps1 -Verbose
```

### Linux/Mac (Bash)
```bash
# Dar permisos de ejecución (solo la primera vez)
chmod +x save_project.sh

# Guardado básico con mensaje automático
./save_project.sh

# Guardado con mensaje personalizado
./save_project.sh "feat: Add new friendship feature"

# Solo commit local (sin push)
./save_project.sh --skip-push

# Modo verbose (más información)
./save_project.sh --verbose
```

## 📋 Características

### ✅ Funcionalidades
- **Detección automática** de cambios en el proyecto
- **Validación** del directorio del proyecto
- **Staging automático** de todos los archivos modificados
- **Commit** con mensaje personalizable o automático con timestamp
- **Push automático** al repositorio remoto (opcional)
- **Manejo de errores** con mensajes informativos
- **Modo verbose** para debugging
- **Colores** en la consola para mejor legibilidad

### 🔒 Validaciones
- Verifica que estás en el directorio correcto del proyecto
- Confirma la existencia del repositorio Git
- Valida que hay cambios antes de proceder
- Maneja errores de conectividad para push

### 🎨 Output
- **Iconos** y **colores** para identificar rápidamente el estado
- **Resumen final** con información del commit
- **Mensajes de error** claros con sugerencias de solución

## 🔧 Parámetros

### PowerShell (`save_project.ps1`)
| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `-CommitMessage` | String | Mensaje personalizado para el commit | `-CommitMessage "fix: Resolve authentication bug"` |
| `-SkipPush` | Switch | Omite el push al repositorio remoto | `-SkipPush` |
| `-Verbose` | Switch | Muestra información detallada del proceso | `-Verbose` |

### Bash (`save_project.sh`)
| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `mensaje` | String | Mensaje personalizado para el commit | `"fix: Resolve authentication bug"` |
| `--skip-push` | Flag | Omite el push al repositorio remoto | `--skip-push` |
| `--verbose` | Flag | Muestra información detallada del proceso | `--verbose` |

## 📊 Ejemplos de Uso

### Escenarios Comunes

#### 1. Guardado rápido al final del día
```powershell
.\save_project.ps1 -CommitMessage "EOD: Save all progress"
```

#### 2. Commit intermedio sin subir a GitHub
```powershell
.\save_project.ps1 -CommitMessage "WIP: Working on friendship system" -SkipPush
```

#### 3. Debugging del proceso
```powershell
.\save_project.ps1 -Verbose
```

#### 4. Guardado de feature completa
```bash
./save_project.sh "feat: Complete friendship system implementation"
```

## ⚡ Atajos Recomendados

### Alias en PowerShell
Agrega a tu perfil de PowerShell (`$PROFILE`):
```powershell
function Save-Project { .\save_project.ps1 @args }
Set-Alias sp Save-Project
```

Uso: `sp "mensaje del commit"`

### Alias en Bash
Agrega a tu `.bashrc` o `.zshrc`:
```bash
alias sp='./save_project.sh'
```

Uso: `sp "mensaje del commit"`

## 🚨 Troubleshooting

### Problemas Comunes
1. **"No se encontró el repositorio Git"**
   - Asegúrate de estar en el directorio raíz del proyecto
   - Verifica que existe la carpeta `.git`

2. **"Error al hacer push"**
   - Verifica tu conexión a internet
   - Confirma tus credenciales de GitHub
   - El commit local se guardó correctamente

3. **"Permission denied" en Linux/Mac**
   - Ejecuta: `chmod +x save_project.sh`

### Logs de Error
Los scripts muestran mensajes detallados de error y sugerencias de solución automáticamente.

## 📦 Instalación

1. Los scripts ya están creados en tu directorio del proyecto
2. Para Windows: usar directamente `.\save_project.ps1`
3. Para Linux/Mac: dar permisos con `chmod +x save_project.sh`

¡Listo para usar! 🎉