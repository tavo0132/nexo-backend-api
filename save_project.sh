#!/bin/bash
# Script Bash para guardar todos los cambios del proyecto nexo-backend
# Creado: 12 de Noviembre 2025
# Propósito: Automatizar el guardado, commit y push de todos los cambios
# Uso: ./save_project.sh [mensaje_del_commit] [--skip-push] [--verbose]

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;37m'
NC='\033[0m' # No Color

# Parámetros por defecto
COMMIT_MESSAGE="Auto-save: Update project files"
SKIP_PUSH=false
VERBOSE=false

# Procesar argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-push)
            SKIP_PUSH=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        -*)
            echo -e "${RED}Opción desconocida: $1${NC}"
            exit 1
            ;;
        *)
            COMMIT_MESSAGE="$1"
            shift
            ;;
    esac
done

# Función para mostrar mensajes verbose
verbose_message() {
    if [ "$VERBOSE" = true ]; then
        echo -e "   ℹ️ ${YELLOW}$1${NC}"
    fi
}

# Función para manejo de errores
error_exit() {
    echo -e "\n${RED}❌ ERROR EN EL PROCESO DE GUARDADO${NC}"
    echo -e "${GRAY}=$(printf '%.0s=' {1..60})${NC}"
    echo -e "   ${RED}💥 Error: $1${NC}"
    echo -e "\n${YELLOW}💡 SOLUCIONES SUGERIDAS:${NC}"
    echo -e "   ${WHITE}1. Verifica que estás en el directorio correcto del proyecto${NC}"
    echo -e "   ${WHITE}2. Asegúrate de tener conexión a internet para el push${NC}"
    echo -e "   ${WHITE}3. Verifica tus credenciales de Git${NC}"
    echo -e "   ${WHITE}4. Ejecuta manualmente: git status${NC}"
    exit 1
}

echo -e "${CYAN}🔧 NEXO BACKEND - SCRIPT DE GUARDADO AUTOMÁTICO${NC}"
echo -e "${GRAY}$(printf '%.0s=' {1..60})${NC}"

# 1. Verificar que estamos en el directorio correcto
echo -e "${GREEN}📁 Verificando directorio del proyecto...${NC}"

if [ ! -d ".git" ]; then
    error_exit "No se encontró el repositorio Git. Asegúrate de estar en el directorio del proyecto."
fi

if [ ! -d "app" ]; then
    error_exit "No se encontró la carpeta 'app'. Verifica que estás en el directorio correcto."
fi

verbose_message "Directorio del proyecto verificado correctamente"

# 2. Mostrar estado actual del repositorio
echo -e "${GREEN}📊 Verificando estado del repositorio...${NC}"

GIT_STATUS=$(git status --porcelain)
if [ -n "$GIT_STATUS" ]; then
    echo -e "   ${YELLOW}📝 Cambios detectados:${NC}"
    echo "$GIT_STATUS" | while IFS= read -r line; do
        echo -e "      ${WHITE}$line${NC}"
    done
else
    echo -e "   ${GREEN}✅ No hay cambios pendientes${NC}"
    echo -e "${CYAN}🎉 Proyecto ya está actualizado${NC}"
    exit 0
fi

# 3. Agregar todos los archivos al staging
echo -e "${GREEN}📦 Agregando archivos al staging...${NC}"

if ! git add .; then
    error_exit "Error al agregar archivos al staging"
fi

verbose_message "Todos los archivos agregados al staging correctamente"

# 4. Verificar archivos en staging
echo -e "${GREEN}🔍 Verificando archivos en staging...${NC}"

STAGED_FILES=$(git diff --cached --name-only)
if [ -n "$STAGED_FILES" ]; then
    echo -e "   ${YELLOW}📋 Archivos preparados para commit:${NC}"
    echo "$STAGED_FILES" | while IFS= read -r file; do
        echo -e "      ${GREEN}✓ $file${NC}"
    done
else
    echo -e "   ${YELLOW}⚠️ No hay archivos en staging${NC}"
    exit 0
fi

# 5. Crear commit con mensaje personalizado o automático
echo -e "${GREEN}💾 Creando commit...${NC}"

# Si es el mensaje por defecto, agregar timestamp
if [ "$COMMIT_MESSAGE" = "Auto-save: Update project files" ]; then
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    COMMIT_MESSAGE="Auto-save: Update project files - $TIMESTAMP"
fi

echo -e "   ${WHITE}📝 Mensaje: $COMMIT_MESSAGE${NC}"

if ! git commit -m "$COMMIT_MESSAGE"; then
    error_exit "Error al crear el commit"
fi

verbose_message "Commit creado exitosamente"

# 6. Push al repositorio remoto (opcional)
if [ "$SKIP_PUSH" = false ]; then
    echo -e "${GREEN}🚀 Enviando cambios al repositorio remoto...${NC}"
    
    if ! git push origin main; then
        echo -e "   ${YELLOW}⚠️ Error al hacer push. El commit local fue exitoso.${NC}"
        echo -e "   ${CYAN}💡 Intenta ejecutar manualmente: git push origin main${NC}"
    else
        verbose_message "Push completado exitosamente"
    fi
else
    echo -e "${YELLOW}⏸️ Push omitido (usar sin --skip-push para activar)${NC}"
fi

# 7. Mostrar resumen final
echo -e "\n${GREEN}✅ GUARDADO COMPLETADO EXITOSAMENTE${NC}"
echo -e "${GRAY}$(printf '%.0s=' {1..60})${NC}"

COMMIT_HASH=$(git rev-parse --short HEAD)
CURRENT_TIME=$(date '+%Y-%m-%d %H:%M:%S')

echo -e "   ${CYAN}📊 Commit ID: $COMMIT_HASH${NC}"
echo -e "   ${CYAN}📁 Branch: main${NC}"
echo -e "   ${CYAN}🕒 Timestamp: $CURRENT_TIME${NC}"

if [ "$SKIP_PUSH" = false ]; then
    echo -e "   ${GREEN}🌐 Estado: Sincronizado con GitHub${NC}"
else
    echo -e "   ${YELLOW}🏠 Estado: Solo guardado local${NC}"
fi

echo -e "\n${CYAN}🎯 SCRIPT COMPLETADO${NC}"