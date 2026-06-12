# DeploX Server

DeploX Server es una solución cliente-servidor portátil para gestionar la distribución y ejecución de programas dentro de una red local (UNC/SMB). Mediante dos interfaces gráficas intuitivas, permite a los administradores centralizar un catálogo de software en la red y a los usuarios finales ejecutar o descargar las aplicaciones en tiempo real sin configuraciones complejas.

<img width="925" height="331" alt="DeploXServer" src="https://github.com/user-attachments/assets/a425194e-b086-45ef-866a-578483090fba" />


---

## - Tabla de contenidos

- Características
- Estructura del proyecto
- Requisitos
- Instalación
- Compilación a EXE
- Uso del sistema
- Configuración avanzada
- Solución de problemas
- Políticas de seguridad

---

## - Características

- **Administrador centralizado**: Gestiona el catálogo de programas y crea grupos con interfaz visual.
- **Detección automática de iconos**: Busca y extrae automáticamente archivos `icon.png` o `logo.png` de la carpeta del ejecutable.
- **Soporte nativo UNC**: Diseñado específicamente para trabajar con rutas de red local (`\\servidor\carpeta`).
- **Actualización en caliente**: Los clientes recargan el catálogo al instante con un solo botón y un efecto visual de spinner.
- **Filtrado dinámico**: Buscador por texto y filtros por grupos combinables en tiempo real (AND lógico).
- **Seguridad por diseño**: El cliente opera estrictamente en modo de solo lectura (R/only) para proteger el catálogo centralizado.

---

## - Estructura del proyecto

```
DeploXServer/
├── config.py              # Administrador (código fuente)
├── download.py            # Cliente / Launcher (código fuente)
├── utils.py               # Lógica compartida y utilidades base
├── config.json            # Catálogo centralizado (se genera automáticamente)
├── icons/                 # Almacenamiento de iconos normalizados
│   ├── chrome.png
│   └── office.png
└── [archivos de compilación]
    ├── build.bat          # Script de compilación para Windows
    └── build.sh           # Script de compilación para Linux/macOS
```

---

## - Requisitos

### Desarrollo (Python 3.8+)

```bash
pip install PySide6>=6.0.0
```

### Ejecución (EXE compilado)

- Windows 10/11, Linux o macOS (con soporte PySide6)
- No requiere Python instalado
- Permisos de lectura en la ruta de red local (SMB/UNC)

---

## - Instalación

### Opción 1: Ejecutar desde Python

1. Clonar o descargar el proyecto
2. Instalar dependencias

```bash
pip install -r requirements.txt
```

3. Ejecutar en modo desarrollo

```bash
# Administrador
python config.py

# Cliente
python download.py
```

### Opción 2: Usar EXE compilados

Solo necesitas desplegar la carpeta con los archivos .exe generados en el servidor de red.

---

## - Compilación a EXE

### Requisitos previos

```bash
pip install pyinstaller>=5.0.0
```

### Compilar ambas aplicaciones

#### Opción A: Scripts automáticos (Recomendado)

En Windows:

```bash
build.bat
```

En Linux/macOS:

```bash
bash build.sh
```

Este proceso generará automáticamente la carpeta de distribución `DeploXServer/` lista con ambos ejecutables y la estructura interna.

#### Opción B: Comandos manuales

Administrador (config.py):

```bash
python -m PyInstaller --windowed --name config config.py
```

Cliente (download.py):

```bash
python -m PyInstaller --windowed --name download download.py
```

---

## - Uso del sistema

### Flujo de trabajo

```
1. CONFIGURAR (config.exe de Admin escribe R/W)
   ↓
2. ALMACENAR (config.json centralizado en red UNC)
   ↓
3. LANZAR / DESCARGAR (download.exe de Cliente lee R-only)
```

### Paso 1: Administrador (config.exe)

#### Gestionar Programas

1. Haz click en "Añadir Programa" e ingresa el nombre.
2. Introduce o busca la ruta del ejecutable (ej. `\\sena\programas\chrome\chrome.exe`).
3. El sistema buscará un icono automáticamente en la carpeta de origen (`icon.png` o `logo.png`). Si no existe, permite asignarlo manualmente.

#### Gestionar Grupos

1. Haz click en "Añadir Nuevo Grupo".
2. Asigna un nombre al grupo (ej. "Diseño") y marca los programas mediante los checkboxes correspondientes.
3. Puedes usar la barra de búsqueda interna o el filtro por estado para organizar mejor tus apps.

#### Editar o Eliminar

Usa los botones de engranaje (⚙️) para modificar o el de basura (🗑️) para borrar programas con confirmación previa. Los cambios se propagan a los grupos de forma automática.

#### Archivo generado: config.json

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
        }
    ]
}
```

### Paso 2: Cliente / Launcher (download.exe)

#### Seleccionar aplicaciones

1. Explora el catálogo visual en su interfaz oscura.
2. Puedes utilizar el buscador por texto o el menú desplegable de grupos para filtrar las aplicaciones en tiempo real.

#### Iniciar ejecución

1. Haz doble click sobre cualquier fila o pasa el ratón por encima para revelar el botón "Play" (▶) y lanzar el ejecutable directamente desde la red UNC.

#### Opciones adicionales

Haz click en el botón de tres puntos (⋮) para abrir el menú contextual.

- **Descargar**: Copia de forma limpia el ejecutable de red a tu equipo local (por defecto a la carpeta Descargas).
- **Mostrar Ruta**: Abre un diálogo interactivo para ver y copiar la ruta del archivo al portapapeles.

---

## - Configuración avanzada

### Archivo config.json

El archivo de configuración puede ser editado directamente para ajustes finos, cuidando de escapar correctamente las barras inclinadas invertidas en las rutas de red:

```json
{
    "programs": [
        {
            "name": "Nombre de la App",
            "path": "\\\\servidor\\recurso\\programa.exe",
            "icon": "icons/nombre_normalizado.png"
        }
    ],
    "groups": [
        {
            "name": "Categoría",
            "programs": ["Nombre de la App"]
        }
    ]
}
```

### Comportamiento del almacenamiento

| Elemento | Tipo de Acceso | Impacto en el Sistema |
|----------|----------------|----------------------|
| config.exe | Lectura y Escritura (R/W) | Modifica el catálogo maestro en la red local. |
| download.exe | Solo Lectura (R only) | Carga los datos en caliente sin riesgo de corrupción. |
| icons/ | Almacenamiento Local | Almacena imágenes PNG/JPG relativas a la carpeta raíz. |

---

## - Solución de problemas

### "JSON corrupto o vacío"

- **Causa**: Interrupción en la escritura o borrado incorrecto.
- **Solución**: Elimina el `config.json` defectuoso, abre `config.exe` y añade una aplicación para regenerar la estructura por defecto automáticamente.

### "Archivo no encontrado al ejecutar"

- **Causa**: La ruta UNC no es accesible o faltan permisos de red SMB.
- **Solución**: Verifica tu conexión con la ruta mediante el comando `net use \\servidor` en Windows y comprueba los permisos NTFS.

### "Los iconos no aparecen en la interfaz"

- **Causa**: Formato de imagen no soportado o falta de permisos de escritura en la carpeta `icons/`.
- **Solución**: Asegúrate de que las imágenes sean PNG o JPG válidas y verifica que el directorio local tenga permisos de escritura correctos.

### "El programa se cierra inmediatamente tras abrirse"

- **Causa**: El ejecutable remoto depende de archivos o librerías DLL que no están presentes localmente.
- **Solución**: Utiliza la opción "Descargar" (dentro del botón ⋮) para traer el programa a tu máquina y diagnosticar fallas de dependencia locales.

---

## - Políticas de seguridad

- **Control de acceso**: El archivo `config.exe` está restringido para administradores de IT, mientras que los terminales de usuario final solo ejecutan `download.exe` en modo lectura.
- **Privacidad de datos**: Toda la información se mantiene localmente dentro de tu red corporativa (autenticación SMB nativa del sistema operativo) sin llamadas externas a internet.
- **Aislamiento de errores**: Las excepciones críticas y rutas de entorno sensibles son capturadas internamente para evitar fugas de información a través de stack traces visibles al usuario.

---

## - Licencia

Proyecto de uso interno corporativo. Redistribución permitida siempre que se mantenga esta documentación y se respeten las políticas de acceso de red.

**Versión**: 1.0  
**Última actualización**: Junio 2026

- Alberto Fernández Bellido -
