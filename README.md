# DeploX Server - Documentación Completa

## 📋 Resumen del Proyecto

**DeploX Server** es una solución cliente-servidor para gestionar la distribución y ejecución de programas en una red local (UNC/SMB). Consta de dos aplicaciones PySide6 con interfaz gráfica:

- **config.exe** (Administrador): Gestiona el catálogo centralizado de programas y grupos
- **download.exe** (Cliente): Interfaz para usuarios finales para ejecutar o descargar programas

---

## 🏗️ Arquitectura General

```
DeploXServer/
├── config.exe              (Administrador compilado)
├── download.exe            (Cliente compilado)
├── config.json             (Catálogo centralizado)
├── icons/                  (Almacenamiento de iconos)
│   ├── chrome.png
│   └── office.png
└── [utils.py]              (Opcional: lógica compartida en fuente)
```

### Flujo de Datos

```
config.exe (R/W) ──────> config.json <────── download.exe (R only)
   Admin                 [Centralizado]         Client
Escribe datos            en Red UNC          Lectura en caliente
```

---

## 📦 Módulos Técnicos

### 1. **utils.py** - Lógica Compartida

Archivo base sin dependencias de UI. Proporciona funciones reutilizables:

#### Configuración
- `load_config()`: Lee config.json con fallback a estructura por defecto
- `save_config(data)`: Guarda JSON con formato UTF-8 e indentación
- `ensure_icons_folder()`: Crea carpeta `icons/` si no existe

#### Gestión de Programas
- `add_program(data, name, exe_path, icon_path)`: Registra programa con detección automática de icono
- `remove_program(data, name)`: Elimina programa de la configuración
- `extract_icon_from_exe(exe_path)`: Busca `icon.png` o `logo.png` en la carpeta del ejecutable
- `copy_icon_to_folder(source_icon, program_name)`: Copia icono a `icons/` con nombre normalizado

#### Ejecución y Descargas
- `run_program(exe_path)`: Ejecuta programa con `subprocess.Popen()`, soporta rutas UNC
- `copy_exe_to_downloads(exe_path, filename)`: Copia ejecutable a `C:\Users\Usuario\Downloads`
- `get_program_icon_path(icon_rel)`: Resuelve ruta absoluta de iconos (relativas o absolutas)

#### Utilidades
- `is_valid_unc_path(path)`: Valida formato `\\servidor\carpeta`
- `normalize_unc_path(path)`: Convierte `/` a `\\`

**Características:**
- ✓ Validación de rutas antes de ejecutar
- ✓ Manejo robusto de errores sin revelar información sensible
- ✓ Soporte nativo de rutas UNC

---

### 2. **config.py** - Administrador (Interfaz)

Aplicación de escritorio para gestionar el catálogo centralizado.

#### Interfaz Principal

**Sección Programas:**
- Botón "Añadir Programa" → Abre `ProgramDialog`
- Lista de programas registrados con:
  - Nombre y ruta del ejecutable
  - Botón ⚙️ (editar): Modifica datos del programa
  - Botón 🗑️ (eliminar): Borra con confirmación

**Sección Grupos:**
- Botón "Añadir Nuevo Grupo" → Abre `GroupDialog`
- Lista de grupos con botones editar/eliminar
- Efecto fade-in al crear nuevo grupo

#### Diálogos Especializados

**ProgramDialog** (Añadir/Editar):
- Campo: Nombre del programa
- Campo: Ruta del ejecutable
- Botón "Explorar": QFileDialog para buscar .exe
- Validaciones: nombre, ruta, existencia del archivo

**GroupDialog** (Crear/Editar grupos):
- Campo: Nombre del grupo
- Lista de programas disponibles con checkboxes
- Barra de búsqueda para filtrar programas
- ComboBox: Filtro por estado (Todos / Añadidos / No añadidos)

#### Lógica de Guardado

```python
add_program() flow:
1. Valida que nombre y ejecutable no estén vacíos
2. Verifica que el archivo existe
3. Si no hay icono manual, busca automáticamente:
   - icon.png en carpeta del .exe
   - logo.png en carpeta del .exe
4. Copia icono a icons/{programa_normalizado}.png
5. Guarda en config.json
6. Sincroniza listas visuales
```

#### Estilos Visuales
- Tema oscuro inspirado en VS Code
- Paleta: #1e1e1e (fondo), #ffffff (texto), #4CAF50 (acciones positivas), #007acc (secundario)
- Botones con efecto hover y animaciones suaves

---

### 3. **download.py** - Cliente / Launcher (Interfaz)

Aplicación para usuarios finales (lectura única del config.json).

#### Interfaz Principal

**Barra Superior:**
- Campo de búsqueda: Filtra programas en tiempo real
- ComboBox de Grupos: Filtra por categoría (vacío = mostrar todos)
- Botón "Actualizar": Recarga config.json sin reiniciar (efecto spinner)

**Área Central:**
- Lista de programas con componentes `ClientProgramRowWidget`
- Cada fila muestra:
  - Nombre del programa
  - Botón ▶ (ejecutar, visible al pasar el ratón)
  - Botón ⋮ (más opciones)

#### Interacciones

**Doble Click / Click Izquierdo:**
- Ejecuta: `subprocess.Popen(exe_path)` con soporte UNC

**Botón ▶ (Play):**
- Ejecuta el programa (igual que doble click)
- Visible solo al pasar el ratón (efecto hover)

**Botón ⋮ (Menú Contextual):**
- "Descargar": Abre QFileDialog para guardar .exe en carpeta seleccionada (predefecto: Downloads)
- "Mostrar Ruta": Abre ventana `PathDialog` con ruta del ejecutable copiable al portapapeles

**Botón Actualizar:**
- Recarga config.json en caliente
- Efecto visual spinner durante 800ms
- Mantiene filtros activos del usuario

#### Filtrado Dinámico

- **Por texto**: Busca en nombres de programas (case-insensitive)
- **Por grupo**: Muestra solo programas del grupo seleccionado
- Ambos filtros funcionan en conjunto (AND lógico)

#### Estilos Visuales
- Tema oscuro: #1e1e1e (fondo), #121212 (lista)
- Componentes: #252526 (inputs), #2d2d2d (bordes)
- Acentos: #4caf50 (ejecutar), #007acc (información)
- Hover effects suaves con transiciones

---

## 📄 Estructura del config.json

```json
{
    "programs": [
        {
            "name": "Google Chrome",
            "path": "\\\\sena\\programas\\chrome\\chrome.exe",
            "icon": "icons/google_chrome.png"
        },
        {
            "name": "Microsoft Office",
            "path": "\\\\sena\\programas\\office\\office.exe",
            "icon": "icons/microsoft_office.png"
        }
    ],
    "groups": [
        {
            "name": "Diseño",
            "programs": ["Photoshop", "Illustrator"]
        },
        {
            "name": "Desarrollo",
            "programs": ["Visual Studio Code", "Git Bash"]
        }
    ]
}
```

**Notas:**
- Rutas UNC usan `\\\\` (escape JSON)
- Campo `icon` puede ser `null` si no hay icono
- Rutas de iconos relativas a la carpeta raíz
- El campo `server` (si existe) es descartado por `config.py`

---

## 🚀 Instalación y Compilación

### Requisitos Previos

```bash
# Python 3.8 o superior
python --version

# Instalar dependencias
pip install PySide6 pyinstaller
```

### Instalación Manual de Dependencias

```bash
pip install -r requirements.txt
```

**requirements.txt:**
```
PySide6>=6.0.0
pyinstaller>=5.0.0
```

### Compilación

#### Opción 1: Comandos Manuales

```bash
# Desde la carpeta Sin_compilar

# Compilar config.exe
python -m PyInstaller --windowed --name config config.py

# Compilar download.exe
python -m PyInstaller --windowed --name download download.py
```

**Salida:** `dist/config.exe` y `dist/download.exe`

#### Opción 2: Scripts de Compilación (Recomendado)

**En Windows (build.bat):**
```bash
build.bat
```

**En Linux/macOS (build.sh):**
```bash
bash build.sh
```

Se crea automáticamente carpeta `DeploXServer/` con ambos .exe y carpeta `icons/`

### Distribución Final

1. Copiar contenido de `DeploXServer/` a `\\sena\DeploXServer`
2. Estructura en servidor:

```
\\sena\DeploXServer\
├── config.exe
├── download.exe
├── config.json       (se crea al usar config.exe)
└── icons\
    ├── chrome.png
    └── office.png
```

3. Distribuir **download.exe** a usuarios finales:
   - Acceso directo en escritorio
   - Enlace en menú Inicio
   - Instalador MSI (opcional)

---

## 🎮 Guía de Uso

### Para Administradores (config.exe)

#### 1. Añadir un Programa

1. Ejecuta `config.exe`
2. Click "Añadir Programa"
3. Ingresa:
   - Nombre: "Google Chrome"
   - Ejecutable: Busca o ingresa `\\sena\programas\chrome\chrome.exe`
4. Click "Añadir Programa"
   - Sistema detecta automáticamente icono (icon.png o logo.png)
   - Copia icono a `icons/google_chrome.png`
   - Guarda en config.json

#### 2. Crear un Grupo

1. Click "Añadir Nuevo Grupo"
2. Nombre del grupo: "Diseño"
3. Selecciona programas (checkboxes): Photoshop, Illustrator
4. Click "Guardar Grupo"
   - Los usuarios ven filtro en download.exe

#### 3. Editar Programa

1. Hover sobre programa existente
2. Click ⚙️ (editar)
3. Modifica datos y click "Guardar Cambios"
   - Si cambias nombre, se actualiza automáticamente en grupos

#### 4. Eliminar Programa

1. Hover sobre programa
2. Click 🗑️
3. Confirmar eliminación
   - Se elimina automáticamente de todos los grupos

### Para Usuarios Finales (download.exe)

#### 1. Ejecutar un Programa

1. Abre `download.exe`
2. Doble click sobre programa O click botón ▶
3. Se lanza automáticamente desde red

#### 2. Descargar Ejecutable

1. Click botón ⋮ (menú) en programa
2. "Descargar"
3. Selecciona carpeta destino (predefecto: Downloads)
4. Confirma

#### 3. Ver Ruta del Programa

1. Click botón ⋮ (menú)
2. "Mostrar Ruta"
3. Click "📋 Copiar Ruta" para copiar al portapapeles

#### 4. Filtrar Programas

- **Por búsqueda**: Digita en campo "Buscar programa por nombre..."
- **Por grupo**: Selecciona grupo en ComboBox (si existen)
- Ambos filtros funcionan en conjunto

#### 5. Recargar Catálogo

- Click "Actualizar"
- Espera efecto spinner (800ms)
- Mantiene búsqueda y grupo activos

---

## 🔧 Características Técnicas

### ✓ Soporte Completo UNC (Red SMB)

Todas las operaciones funcionan con rutas `\\servidor\carpeta\archivo`:
- Lectura de ejecutables desde red
- Copia de archivos desde/hacia red
- Ejecución directa de programas remotos
- Validación de rutas antes de usar

### ✓ Detección Automática de Iconos

```python
Al seleccionar ejecutable en config.py:
1. Busca icon.png en la carpeta del .exe
2. Si no existe, busca logo.png
3. Si encuentra, lo copia a icons/ automáticamente
4. Si no encuentra, permite selección manual
```

### ✓ Filtrado en Tiempo Real

- Búsqueda por nombre (case-insensitive)
- Filtro por grupo (categorización)
- Ambos activos simultáneamente (AND lógico)
- Sin reinicio necesario

### ✓ Actualización en Caliente

- Botón "Actualizar" recarga config.json sin cerrar app
- Efecto visual spinner durante carga
- Mantiene preferencias del usuario (búsqueda, grupo)

### ✓ Manejo Robusto de Errores

| Escenario | Respuesta |
|-----------|-----------|
| JSON corrupto | Estructura por defecto |
| Archivo no encontrado | Validación previa + mensaje de error |
| Ruta UNC inaccesible | Fallo controlado sin crash |
| Icono inválido | Descarta y permite selección manual |
| Permisos insuficientes | Captura excepción + feedback usuario |

### ✓ Seguridad por Diseño

| Componente | Permisos | Descripción |
|-----------|----------|-------------|
| config.exe | R/W | Crea y modifica config.json |
| download.exe | R only | Solo lectura (no puede modificar) |
| Rutas UNC | R | Ejecuta desde red con permisos de lectura |
| Validación | Pre-execution | Verifica rutas antes de cualquier operación |

---

## 🛠️ Desarrollo y Testing

### Ejecutar en Modo Desarrollo (sin compilar)

```bash
# Administrador (live debugging)
python config.py

# Cliente (live debugging)
python download.py
```

### Verificar Integridad de Código

```bash
# Comprobar sintaxis Python
python -m py_compile utils.py config.py download.py

# Si existe test_integrity.py
python test_integrity.py
```

### Generar Documentación de Cambios

Cada compilación genera carpeta `dist/` con los ejecutables y carpeta `build/` con intermedios.

---

## 🐛 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'PySide6'"

```bash
pip install PySide6
```

### Error: "Archivo no encontrado" al ejecutar

**Causas:**
- Ruta UNC no accesible desde la red
- Permisos insuficientes en `\\sena\`

**Solución:**
1. Verifica acceso de red: `net use \\sena`
2. Confirma permisos NTFS en servidor
3. Si es ruta local, verifica que existe el archivo

### Config.json vacío o corrupto

**Síntomas:**
- download.exe muestra "No hay programas registrados"
- config.exe no carga datos

**Solución:**
1. Elimina config.json corrupto
2. Abre config.exe
3. Crea al menos un programa
4. Click "Añadir Programa" para regenerar JSON

### Los iconos no aparecen

**Causas posibles:**
- Formato de imagen inválido (debe ser PNG o JPG)
- Carpeta `icons/` sin permisos de escritura
- Ruta de icono relativa incorrecta

**Solución:**
1. Verifica formato: `file icons/programa.png` debe ser imagen válida
2. Permisos: `chmod 755 icons/` (Linux/Mac)
3. Selecciona icono manualmente desde config.exe

### Programa se abre pero luego cierra

**Causa:** Programa remoto requiere dependencias locales no disponibles

**Solución:**
1. Descargar .exe a máquina local (opción "Descargar" en download.exe)
2. Ejecutar desde disco local para diagnóstico
3. Verificar que todas las DLL dependientes están en carpeta de programa

### El filtro de grupos no funciona

**Causa:** No existen grupos definidos en config.json

**Solución:**
1. Abre config.exe
2. Click "Añadir Nuevo Grupo"
3. Selecciona al menos un programa
4. Recarga download.exe

---

## 📋 Estructura de Archivos en Desarrollo

```
Sin_compilar/                 (Código fuente)
├── utils.py                  (Funciones compartidas)
├── config.py                 (Admin - código fuente)
├── download.py               (Cliente - código fuente)
├── requirements.txt          (Dependencias pip)
├── README.md                 (Esta documentación)
├── build.bat                 (Compilación Windows)
├── build.sh                  (Compilación Linux/Mac)
└── [test_integrity.py]       (Tests opcionales)

dist/                         (Después de compilar)
├── config.exe
├── download.exe
├── _internal/                (Dependencias empaquetadas)
└── ...

DeploXServer/                 (Carpeta de distribución)
├── config.exe
├── download.exe
├── config.json
└── icons/
```

---

## 📚 Referencias Técnicas

### Importaciones Principales

**PySide6:**
```python
from PySide6.QtWidgets import QApplication, QMainWindow, QDialog, QListWidget
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QClipboard
```

**Estándar Library:**
```python
import json, os, shutil, subprocess
from pathlib import Path
from typing import Dict, List, Optional
```

### Configuración PyInstaller

```bash
# Generar spec file
pyi-makespec --windowed --name config config.py

# Compilación avanzada (con icono)
pyinstaller --windowed --icon=app.ico --name config config.py
```

---

## 🔐 Políticas de Seguridad

### Control de Acceso
- **config.exe**: Acceso administrativo (crear/modificar catálogo)
- **download.exe**: Acceso usuario (solo lectura, ejecutar, descargar)
- Validación de rutas antes de cualquier operación del sistema

### Datos en Tránsito
- No se envían datos a servidores externos
- Todo se almacena localmente en config.json
- Comunicación a través de red UNC existente (autenticación SMB del SO)

### Gestión de Errores
- Excepciones capturadas sin revelar rutas sensibles
- Mensajes de error claros para usuario sin stack traces
- Logs de errores solo en salida estándar (desarrollo)

---

## 📞 Soporte y Contribuciones

### Reportar Issues

Documentar:
1. Versión de Python y SO
2. Error exacto con timestamp
3. Pasos para reproducir
4. Rutas afectadas (con privacidad)

### Mejoras Futuras

- [ ] Interfaz web alternativa
- [ ] Base de datos centralizada (en lugar de JSON)
- [ ] Autenticación LDAP para control de acceso
- [ ] Logs de auditoría
- [ ] Sincronización automática de catálogos entre servidores

---

## 📊 Historial de Cambios

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-06-12 | Versión inicial con PySide6, soporte completo UNC, grupos, filtros |
| - | - | - |

---

**Documentación Actualizada:** 2026-06-12  
**Plataformas Soportadas:** Windows 10/11, Linux (con PySide6), macOS (con PySide6)  
**Python Mínimo:** 3.8+  
**Licencia:** [Especificar]
