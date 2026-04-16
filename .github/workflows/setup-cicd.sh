#!/bin/bash
# Script para configurar GitHub Actions CI/CD para renameDriverFolders
# Ejecutar este script UNA SOLA VEZ para setup inicial

set -e

echo "🔧 Configurando GitHub Actions CI/CD..."
echo ""

PROJECT_ID="cloud-functions-474716"
SA_NAME="github-actions-deployer"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
KEY_FILE="gcp-sa-key.json"

# Verificar que gcloud esté autenticado
echo "1️⃣ Verificando autenticación de gcloud..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | grep -q "@"; then
    echo "❌ No estás autenticado con gcloud. Ejecuta: gcloud auth login"
    exit 1
fi
echo "✅ Autenticado como: $(gcloud auth list --filter=status:ACTIVE --format="value(account)")"
echo ""

# Crear Service Account
echo "2️⃣ Creando Service Account..."
if gcloud iam service-accounts describe "$SA_EMAIL" --project="$PROJECT_ID" &>/dev/null; then
    echo "⚠️  Service Account ya existe, saltando creación..."
else
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="GitHub Actions Deployer" \
        --project="$PROJECT_ID"
    echo "✅ Service Account creada: $SA_EMAIL"
fi
echo ""

# Dar permisos
echo "3️⃣ Configurando permisos..."
echo "   - Cloud Run Developer..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/run.developer" \
    --condition=None >/dev/null 2>&1 || echo "   (ya tenía permiso)"

echo "   - Storage Object Admin (para Docker images)..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.objectAdmin" \
    --condition=None >/dev/null 2>&1 || echo "   (ya tenía permiso)"

echo "   - Secret Manager Accessor..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/secretmanager.secretAccessor" \
    --condition=None >/dev/null 2>&1 || echo "   (ya tenía permiso)"

echo "✅ Permisos configurados"
echo ""

# Crear key
echo "4️⃣ Creando key JSON..."
if [ -f "$KEY_FILE" ]; then
    echo "⚠️  El archivo $KEY_FILE ya existe. Borrándolo..."
    rm -f "$KEY_FILE"
fi

gcloud iam service-accounts keys create "$KEY_FILE" \
    --iam-account="$SA_EMAIL" \
    --project="$PROJECT_ID"

echo "✅ Key creada: $KEY_FILE"
echo ""

# Instrucciones para GitHub
echo "5️⃣ Próximos pasos:"
echo ""
echo "   1️⃣ Copiar el contenido del archivo $KEY_FILE"
echo "   2️⃣ Ir a: https://github.com/CENFARG/renameDriverFolders/settings/secrets/actions"
echo "   3️⃣ Crear un nuevo secret:"
echo "      - Name: GCP_SA_KEY"
echo "      - Value: [pegar el contenido de $KEY_FILE]"
echo ""
echo "6️⃣ Comitear los workflows de GitHub Actions:"
echo "   git add .github/"
echo "   git commit -m 'Add GitHub Actions CI/CD workflows'"
echo "   git push origin main"
echo ""
echo "7️⃣ Listo! Los próximos pushes a main harán deploy automático"
echo ""
echo "⚠️  IMPORTANTE: Borrar el archivo $KEY_FILE después de agregarlo a GitHub"
echo ""

# Mostrar el contenido del key (para facilitar copy-paste)
echo "📋 Contenido de $KEY_FILE (para copiar al portapapeles):"
echo "----------------------------------------"
cat "$KEY_FILE"
echo "----------------------------------------"
echo ""
echo "🎯 Setup completo! Seguí los pasos 5️⃣, 6️⃣ y 7️⃣ de arriba"
