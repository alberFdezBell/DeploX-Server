import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


CONFIG_FILE = "config.json"
ICONS_FOLDER = "icons"
DEFAULT_SERVER_PATH = r"\\sena\DeploXServer"


def ensure_icons_folder():
    """Crea la carpeta de iconos si no existe."""
    os.makedirs(ICONS_FOLDER, exist_ok=True)


def load_config() -> Dict:
    """Carga config.json de forma segura."""
    if not os.path.exists(CONFIG_FILE):
        return {"server": DEFAULT_SERVER_PATH, "programs": []}

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {"server": DEFAULT_SERVER_PATH, "programs": []}
            return json.loads(content)
    except (json.JSONDecodeError, Exception):
        return {"server": DEFAULT_SERVER_PATH, "programs": []}


def save_config(data: Dict) -> None:
    """Guarda configuración en JSON con formato estricto."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def extract_icon_from_exe(exe_path: str) -> Optional[str]:
    """
    Intenta extraer el icono de un ejecutable.
    Busca primero icon.png o logo.png en la misma carpeta.
    """
    exe_dir = os.path.dirname(exe_path)

    for icon_name in ["icon.png", "logo.png"]:
        icon_path = os.path.join(exe_dir, icon_name)
        if os.path.exists(icon_path):
            return icon_path

    return None


def copy_icon_to_folder(source_icon: str, program_name: str) -> Optional[str]:
    """
    Copia un icono a la carpeta local de iconos.
    Retorna la ruta relativa del icono guardado.
    """
    ensure_icons_folder()

    if not os.path.exists(source_icon):
        return None

    ext = os.path.splitext(source_icon)[1] or ".png"
    dest_icon = os.path.join(ICONS_FOLDER, f"{program_name.lower().replace(' ', '_')}{ext}")

    try:
        shutil.copy2(source_icon, dest_icon)
        return dest_icon
    except Exception:
        return None


def add_program(data: Dict, name: str, exe_path: str, icon_path: Optional[str] = None) -> Dict:
    """Añade un programa a la configuración."""

    # Detectar icono automáticamente si no se proporciona
    if not icon_path:
        detected_icon = extract_icon_from_exe(exe_path)
        if detected_icon:
            icon_path = copy_icon_to_folder(detected_icon, name)
    else:
        icon_path = copy_icon_to_folder(icon_path, name)

    program = {
        "name": name,
        "path": exe_path,
        "icon": icon_path if icon_path else None
    }

    # Evitar duplicados por nombre
    data["programs"] = [p for p in data["programs"] if p["name"] != name]
    data["programs"].append(program)

    return data


def remove_program(data: Dict, name: str) -> Dict:
    """Elimina un programa de la configuración."""
    data["programs"] = [p for p in data["programs"] if p["name"] != name]
    return data


def get_program_icon_path(icon_rel: Optional[str]) -> Optional[str]:
    """
    Retorna la ruta absoluta del icono, manejando rutas relativas.
    """
    if not icon_rel:
        return None

    if os.path.isabs(icon_rel):
        return icon_rel if os.path.exists(icon_rel) else None

    icon_path = os.path.join(os.getcwd(), icon_rel)
    return icon_path if os.path.exists(icon_path) else None


def run_program(exe_path: str) -> bool:
    """
    Ejecuta un programa desde la ruta especificada.
    Soporta rutas UNC.
    """
    try:
        subprocess.Popen(exe_path)
        return True
    except Exception:
        return False


def copy_exe_to_downloads(exe_path: str, filename: Optional[str] = None) -> Optional[str]:
    """
    Copia un ejecutable a la carpeta de descargas del usuario.
    """
    if not os.path.exists(exe_path):
        return None

    downloads_folder = str(Path.home() / "Downloads")

    if not filename:
        filename = os.path.basename(exe_path)

    dest_path = os.path.join(downloads_folder, filename)

    try:
        shutil.copy2(exe_path, dest_path)
        return dest_path
    except Exception:
        return None


def is_valid_unc_path(path: str) -> bool:
    """Valida si la ruta es un path UNC válido."""
    return path.startswith(r"\\")


def normalize_unc_path(path: str) -> str:
    """Normaliza una ruta UNC (convierte / a \\)."""
    if path.startswith(r"\\"):
        return path.replace("/", "\\")
    return path
