import os
import shutil
import sys


# ---------- Localizar la carpeta "Documentos" real ----------
def _get_documents_dir():
    """
    Devuelve la ruta de la carpeta Documentos del usuario, sin importar
    el idioma del sistema (Documents / Documentos / Dokumente / ...).
    """
    # Windows: preguntar al shell por la carpeta real (CSIDL_PERSONAL = 5)
    if sys.platform.startswith("win"):
        try:
            import ctypes
            from ctypes import wintypes
            CSIDL_PERSONAL = 5
            SHGFP_TYPE_CURRENT = 0
            buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
            res = ctypes.windll.shell32.SHGetFolderPathW(
                None, CSIDL_PERSONAL, None, SHGFP_TYPE_CURRENT, buf
            )
            if res == 0 and buf.value and os.path.isdir(buf.value):
                return buf.value
        except Exception:
            pass

    # Fallback multiplataforma
    home = os.path.expanduser("~")
    for name in ("Documents", "Documentos", "Dokumente", "Documenti", "Documentos"):
        p = os.path.join(home, name)
        if os.path.isdir(p):
            return p
    return home


BASE_DIR = _get_documents_dir()

# Aseguramos que la carpeta exista (por si acaso)
try:
    os.makedirs(BASE_DIR, exist_ok=True)
except OSError:
    pass

# ---------- Configuración ----------
ARCHIVO = os.path.join(BASE_DIR, "GesMed.ini")
SEP = "|"
FMT = "%Y-%m-%d %H:%M"

FRECUENCIAS = [
    "4 horas", "6 horas", "8 horas", "12 horas", "24 horas",
    "1 día", "2 días", "3 días", "1 semana", "15 días",
]


def ruta_recurso(nombre_archivo):
    """
    Devuelve la ruta absoluta a un recurso (ícono, etc.), ya sea que
    estemos ejecutando el .py directamente o el .exe de PyInstaller.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = sys._MEIPASS          # carpeta temporal del .exe
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, nombre_archivo)

ICONO = ruta_recurso("icono.ico")