import os
from tkinter import messagebox
import re
from datetime import datetime, timedelta
from config import ARCHIVO, FMT, SEP

# ------------------ UTILIDADES ------------------
def parse_fecha(s):
    s = (s or "").strip()
    for f in (FMT, "%Y-%m-%d", "%d/%m/%Y %H:%M", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, f)
        except ValueError:
            pass
    return None

def calcular_siguiente(ultimo_str, frecuencia_str):
    ultimo = parse_fecha(ultimo_str)
    if not ultimo:
        return None
    f = (frecuencia_str or "").lower().strip()
    m = re.search(
        r"(\d+)\s*(minutos?|mins?|min|horas?|hrs?|h|d[ií]as?|d|semanas?|sems?|sem)",
        f,
    )
    if not m:
        return None
    num, unit = int(m.group(1)), m.group(2)
    if unit.startswith("min"):
        delta = timedelta(minutes=num)
    elif unit.startswith("h"):
        delta = timedelta(hours=num)
    elif unit.startswith("d"):
        delta = timedelta(days=num)
    elif unit.startswith("sem"):
        delta = timedelta(weeks=num)
    else:
        return None
    return (ultimo + delta).strftime(FMT)

def estado_registro(sgte_str):
    """
    Devuelve (texto_estado, tag) donde tag ∈ {ok, cercano, atrasado, desconocido}
    """
    dt = parse_fecha(sgte_str)
    if not dt:
        return ("SIN FECHA", "desconocido")

    segs = (dt - datetime.now()).total_seconds()

    if segs < 0:
        # La hora programada ya pasó → NO se consumió a tiempo
        a = abs(segs)
        if a < 3600:
            txt = f"NO CONSUMIDO ({int(a/60)} min)"
        elif a < 86400:
            h = int(a // 3600)
            m = int((a % 3600) // 60)
            txt = f"NO CONSUMIDO ({h}h {m}min)"
        else:
            d = int(a // 86400)
            h = int((a % 86400) // 3600)
            txt = f"NO CONSUMIDO ({d}d {h}h)"
        return (txt, "atrasado")

    # Aún tiene tiempo
    if segs < 3600:
        txt = f"Falta {int(segs/60)} min"
        return (txt, "cercano")
    elif segs < 86400:
        h = int(segs // 3600)
        m = int((segs % 3600) // 60)
        return (f"Falta {h}h {m}min", "ok")
    else:
        d = int(segs // 86400)
        return (f"Falta {d} día(s)", "ok")

def cargar():
    datos = []
    if not os.path.exists(ARCHIVO):
        return datos
    try:
        with open(ARCHIVO, "r", encoding="utf-8") as f:
            for linea in f:
                linea = linea.rstrip("\n")
                if not linea.strip():
                    continue
                p = linea.split(SEP)
                if len(p) == 5:
                    datos.append(p)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo leer {ARCHIVO}:\n{e}")
    return datos

def guardar(datos):
    try:
        with open(ARCHIVO, "w", encoding="utf-8") as f:
            for d in datos:
                f.write(SEP.join(d) + "\n")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar:\n{e}")

def limpiar(s):
    return (s or "").replace(SEP, "/").strip()
