# Guía de Configuración ADW en Windows

Esta guía documenta la configuración completa para ejecutar ADWs (AI Developer Workflows) en Windows, basada en problemas encontrados y sus soluciones.

---

## Opción Recomendada: WSL (Windows Subsystem for Linux)

### 1. Instalar WSL con Debian

```powershell
# En PowerShell como Administrador
wsl --install -d Debian
```

Reinicia si es necesario. Después crea usuario y contraseña cuando se abra Debian.

**Nota:** Se recomienda Debian sobre Ubuntu si tienes problemas de permisos con Ubuntu.

---

### 2. Configurar Debian

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar herramientas necesarias
sudo apt install python3 python3-pip python3-venv python3-full git nodejs npm gh -y

# Instalar Claude Code
sudo npm install -g @anthropic-ai/claude-code
```

---

### 3. Autenticaciones

**GitHub CLI:**
```bash
gh auth login
# Seleccionar: GitHub.com → HTTPS → Yes → Login with browser
# Copiar URL al navegador, autorizar, pegar código en terminal
```

**Claude Code:**
```bash
claude
# Copiar URL al navegador, autorizar, pegar código en terminal
# Aceptar términos si aparecen
# Escribir 'exit' para salir
```

---

### 4. Configurar Proyecto

```bash
# Navegar al proyecto (archivos Windows están en /mnt/c/)
cd /mnt/c/Users/TU_USUARIO/ruta/al/proyecto

# Agregar directorio como seguro para git
git config --global --add safe.directory /mnt/c/Users/TU_USUARIO/ruta/al/proyecto

# Crear entorno virtual de Python
python3 -m venv ~/adw-env

# Activar entorno virtual
source ~/adw-env/bin/activate

# Instalar dependencias del ADW
cd adws
pip install python-dotenv requests pydantic
```

---

### 5. Configurar .env del Proyecto

```env
# GitHub Configuration
GITHUB_REPO_URL=https://github.com/usuario/repositorio

# Claude Code Path (usar 'claude' para WSL, no el path de Windows)
CLAUDE_CODE_PATH=claude

# Opcional: Si tienes API key de Anthropic
# ANTHROPIC_API_KEY=sk-ant-...
```

**IMPORTANTE:** No usar paths de Windows (`C:\...`) en WSL, usar `claude` directamente.

---

### 6. Ejecutar ADW

```bash
# Asegurarse de estar en el entorno virtual
source ~/adw-env/bin/activate

# Ir al directorio adws
cd /mnt/c/Users/TU_USUARIO/ruta/al/proyecto/adws

# Ejecutar ADW para planificar un issue
python adw_plan.py <NUMERO_ISSUE>

# O con un ADW ID existente
python adw_plan.py <NUMERO_ISSUE> <ADW_ID>
```

---

## Opción Alternativa: Git Bash (Sin WSL)

Si no puedes usar WSL, configura Git Bash con estas variables:

### Variables de Entorno Permanentes

Agregar a `~/.bashrc`:

```bash
echo 'export APPDATA="C:/Users/TU_USUARIO/AppData/Roaming"' >> ~/.bashrc
echo 'export LOCALAPPDATA="C:/Users/TU_USUARIO/AppData/Local"' >> ~/.bashrc
echo 'export USERPROFILE="C:/Users/TU_USUARIO"' >> ~/.bashrc
echo 'export PYTHONIOENCODING=utf-8' >> ~/.bashrc
echo 'export PYTHONUTF8=1' >> ~/.bashrc
echo 'export PATH="/c/Program Files/GitHub CLI:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### .env para Git Bash

```env
GITHUB_REPO_URL=https://github.com/usuario/repositorio
CLAUDE_CODE_PATH=C:\Users\TU_USUARIO\AppData\Roaming\npm\claude.cmd
PATH=/c/Program Files/GitHub CLI:$PATH
PYTHONIOENCODING=utf-8
PYTHONUTF8=1
```

### Requisitos Previos para Git Bash

1. **Python 3.11+** instalado en Windows
2. **Node.js** instalado en Windows
3. **GitHub CLI** instalado: `winget install --id GitHub.cli`
4. **Claude Code** instalado: `npm install -g @anthropic-ai/claude-code`
5. Autenticarse en ambos: `gh auth login` y `claude`

---

## Problemas Comunes y Soluciones

| Problema | Causa | Solución |
|----------|-------|----------|
| `UnicodeEncodeError: 'charmap' codec` | Windows usa cp1252, no UTF-8 | Usar WSL o exportar `PYTHONIOENCODING=utf-8` |
| `Claude Code error: terms` | Términos no aceptados | Ejecutar `claude` interactivamente y aceptar |
| `GitHub CLI not installed` | gh no está en PATH | Agregar GitHub CLI al PATH |
| `error connecting to api.github.com` | GITHUB_PAT mal configurado | Comentar GITHUB_PAT y usar `gh auth login` |
| `dubious ownership in repository` | Permisos WSL/Windows | `git config --global --add safe.directory <path>` |
| `externally-managed-environment` | Debian no permite pip global | Usar `python3 -m venv` |
| `Claude Code path not found` | Path de Windows en WSL | Cambiar a `CLAUDE_CODE_PATH=claude` |
| `No module named 'dotenv'` | Dependencias no instaladas | `pip install python-dotenv requests pydantic` |

---

## Flujo de Trabajo ADW

```
1. Crear issue en GitHub
          ↓
2. python adw_plan.py <ISSUE_NUMBER>
          ↓
3. ADW clasifica (bug/feature/chore)
          ↓
4. ADW genera plan en specs/
          ↓
5. ADW publica plan en GitHub issue
          ↓
6. Usuario revisa y aprueba plan
          ↓
7. python adw_implement.py <ISSUE_NUMBER> <ADW_ID>
          ↓
8. ADW crea branch, implementa, abre PR
```

---

## Checklist de Configuración Rápida (WSL)

- [ ] WSL Debian instalado (`wsl --install -d Debian`)
- [ ] Python 3, pip, venv instalados (`sudo apt install python3 python3-pip python3-venv python3-full`)
- [ ] Git instalado (`sudo apt install git`)
- [ ] Node.js y npm instalados (`sudo apt install nodejs npm`)
- [ ] GitHub CLI instalado y autenticado (`sudo apt install gh && gh auth login`)
- [ ] Claude Code instalado y autenticado (`sudo npm install -g @anthropic-ai/claude-code && claude`)
- [ ] Git configurado con safe.directory
- [ ] Entorno virtual creado y activado (`python3 -m venv ~/adw-env && source ~/adw-env/bin/activate`)
- [ ] Dependencias instaladas (`pip install python-dotenv requests pydantic`)
- [ ] .env configurado con `CLAUDE_CODE_PATH=claude`

---

## Comandos de Referencia Diaria

```bash
# Abrir WSL Debian
wsl -d Debian

# Activar entorno virtual
source ~/adw-env/bin/activate

# Ir al proyecto
cd /mnt/c/Users/TU_USUARIO/ruta/al/proyecto/adws

# Ejecutar ADW - Planificación
python adw_plan.py <ISSUE_NUMBER>

# Ejecutar ADW - Implementación (después de aprobar plan)
python adw_implement.py <ISSUE_NUMBER> <ADW_ID>
```

---

## Estructura de Archivos ADW

```
proyecto/
├── .env                    # Configuración (CLAUDE_CODE_PATH, GITHUB_REPO_URL)
├── adws/                   # Scripts del ADW
│   ├── adw_plan.py        # Fase de planificación
│   ├── adw_implement.py   # Fase de implementación
│   └── adw_modules/       # Módulos compartidos
├── agents/                 # Datos de ejecución por ADW ID
│   └── <adw_id>/
│       ├── adw_state.json # Estado del ADW
│       └── ...            # Logs y outputs
├── specs/                  # Planes generados
│   └── issue-<N>-adw-<id>-*.md
└── .claude/
    └── commands/          # Comandos disponibles (/feature, /bug, etc.)
```

---

## Referencias

- **Claude Code Docs:** https://docs.anthropic.com/claude-code
- **GitHub CLI Docs:** https://cli.github.com/manual/
- **WSL Docs:** https://learn.microsoft.com/en-us/windows/wsl/

---

*Guía creada: 2026-01-07*
*Basada en sesión de configuración para proyecto Finkargo Automation Hub*
