# Lambda Layers Configuration

Este documento explica la configuración de Lambda Layers para reducir el tamaño del paquete de deployment y evitar el error de límite de 250 MB.

## 📦 Estructura de Layers

El proyecto utiliza **2 Lambda Layers** para separar las dependencias pesadas:

### Layer 1: Data Processing (`fkhub-data-processing`)
**Ubicación**: `backend/layers/data-processing/`
**Tamaño estimado**: ~150-180 MB

**Librerías incluidas**:
- `pandas>=2.0.0` - Procesamiento de datos y Excel
- `PyMuPDF>=1.23.0` - Procesamiento de PDFs
- `openpyxl>=3.0.0` - Lectura/escritura de Excel
- `pdfplumber>=0.10.0` - Extracción de texto de PDFs
- `PyPDF2>=3.0.0` - Manipulación de PDFs
- `sqlalchemy>=2.0.23` - ORM para base de datos
- `alembic>=1.12.1` - Migraciones de DB
- `psycopg2-binary>=2.9.9` - Driver de PostgreSQL

### Layer 2: Google APIs (`fkhub-google-apis`)
**Ubicación**: `backend/layers/google-apis/`
**Tamaño estimado**: ~50-70 MB

**Librerías incluidas**:
- `google-api-python-client>=2.111.0` - Cliente de Google Drive API
- `google-auth>=2.25.2` - Autenticación de Google
- `google-auth-httplib2>=0.2.0` - HTTP adapter
- `google-auth-oauthlib>=1.2.0` - OAuth para Google

### Dependencias Ligeras (en Lambda Function)
**Ubicación**: `backend/requirements.txt`
**Tamaño estimado**: ~30-50 MB

**Librerías incluidas**:
- FastAPI, Uvicorn, Mangum (framework)
- Pydantic (validación)
- Supabase, PyJWT (auth)
- httpx, requests (HTTP clients)
- python-docx, lxml (procesamiento ligero)
- rapidfuzz (fuzzy matching)
- Utilidades: python-dotenv

## 🔧 Build Local

### Opción 1: Usar el script automatizado

```bash
cd backend
./build-layers.sh
```

### Opción 2: Build manual

```bash
cd backend

# Layer 1: Data Processing
cd layers/data-processing
mkdir -p python
pip install -r requirements.txt -t python --platform manylinux2014_x86_64 --only-binary=:all: --upgrade
cd ../..

# Layer 2: Google APIs
cd layers/google-apis
mkdir -p python
pip install -r requirements.txt -t python --platform manylinux2014_x86_64 --only-binary=:all: --upgrade
cd ../..
```

### Probar localmente con SAM

```bash
cd backend/infrastructure
sam build
sam local start-api --port 8000
```

## 🚀 Deployment

### Deployment Automático (GitHub Actions)

El workflow `.github/workflows/deployment.yml` construye y despliega las layers automáticamente:

1. **Detect Changes**: Detecta cambios en `backend/**`
2. **Validate and Build**:
   - Valida template SAM
   - Construye las 2 layers
   - Construye la función Lambda
3. **Deploy**: Despliega todo a AWS usando SAM

**Trigger**: Push a la rama `main` o `workflow_dispatch` manual

### Deployment Manual

```bash
cd backend

# 1. Build layers
./build-layers.sh

# 2. Build y deploy con SAM
cd infrastructure
sam build
sam deploy --guided  # Primera vez
# o
sam deploy  # Deployments subsecuentes
```

## 📊 Reducción de Tamaño

### Antes (Sin Layers)
- **Tamaño total**: ~250-300+ MB descomprimido ❌
- **Resultado**: Error "Unzipped size must be smaller than 262144000 bytes"

### Después (Con Layers)
- **Layer 1 (Data)**: ~150-180 MB ✅
- **Layer 2 (Google)**: ~50-70 MB ✅
- **Función Lambda**: ~30-50 MB ✅
- **Total**: Dentro del límite de AWS Lambda (hasta 5 layers, 250 MB cada uno)

## 🔍 Verificación

### Ver tamaños de las layers localmente

```bash
cd backend

# Tamaño de Data Processing Layer
du -sh layers/data-processing/python

# Tamaño de Google APIs Layer
du -sh layers/google-apis/python
```

### Ver layers en AWS Console

1. AWS Console → Lambda → Layers
2. Buscar: `fkhub-data-processing-prod` y `fkhub-google-apis-prod`
3. Ver versiones y tamaños

### Ver función Lambda

1. AWS Console → Lambda → Functions
2. Buscar: `api-fkhub-prod`
3. Configuration → Layers (debe mostrar 2 layers)

## 🛠️ Troubleshooting

### Error: "pip: No matching distribution found"

**Solución**: Algunas librerías requieren compilación. Usa Docker para build en Linux:

```bash
docker run -v "$PWD":/var/task "public.ecr.aws/sam/build-python3.12" \
  /bin/sh -c "pip install -r layers/data-processing/requirements.txt -t layers/data-processing/python --upgrade"
```

### Error: "Layer size exceeds limit"

**Solución**: Dividir en más layers o optimizar:

```bash
# Remover archivos innecesarios
find layers/*/python -name "*.pyc" -delete
find layers/*/python -name "__pycache__" -type d -exec rm -rf {} +
find layers/*/python -name "tests" -type d -exec rm -rf {} +
```

### Error: "ImportError: No module named 'pandas'"

**Causa**: La layer no está asociada a la función Lambda

**Solución**: Verificar en `template.yaml`:

```yaml
FinkargoFKhubAPI:
  Properties:
    Layers:
      - !Ref DataProcessingLayer
      - !Ref GoogleAPIsLayer
```

## 📚 Referencias

- [AWS Lambda Layers](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html)
- [SAM LayerVersion](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-resource-layerversion.html)
- [Lambda Limits](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)

## 📝 Notas

- Las layers se versionan automáticamente en cada deployment
- `RetentionPolicy: Retain` mantiene versiones anteriores
- Las layers son compartibles entre múltiples funciones Lambda
- Máximo 5 layers por función Lambda
- Tamaño máximo por layer: 250 MB descomprimido
