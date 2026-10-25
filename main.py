import tkinter as tk
import os
from tkinter import ttk, messagebox
from datetime import datetime
from utils import cargar, estado_registro, calcular_siguiente, limpiar, parse_fecha, guardar
from config import FMT, FRECUENCIAS, ARCHIVO, ICONO
from tkcalendar import DateEntry
from notifier import Recordador

# ------------------ WIDGET: selector fecha + hora ------------------
class DateTimePicker(ttk.Frame):
    """Selector compuesto: calendario (DateEntry) + hora/minuto (Spinbox)."""

    def __init__(self, master, initial=None, on_change=None, **kw):
        super().__init__(master, **kw)
        self._on_change = on_change
        self.var_date = tk.StringVar()
        self.var_hour = tk.StringVar()
        self.var_min = tk.StringVar()

        self.date_entry = DateEntry(
            self, width=11, date_pattern="yyyy-mm-dd",
            textvariable=self.var_date, state="readonly",
            background="darkblue", foreground="white", borderwidth=2,
        )
        self.date_entry.pack(side="left")

        ttk.Label(self, text="  ").pack(side="left")

        self.sp_h = ttk.Spinbox(self, from_=0, to=23, width=3,
                                 textvariable=self.var_hour, wrap=True,
                                 format="%02.0f")
        self.sp_h.pack(side="left")
        ttk.Label(self, text=":").pack(side="left")
        self.sp_m = ttk.Spinbox(self, from_=0, to=59, width=3,
                                 textvariable=self.var_min, wrap=True,
                                 format="%02.0f")
        self.sp_m.pack(side="left")

        # Inicializa el valor ANTES de enganchar el callback
        self.set_datetime(initial or datetime.now())

        self.var_date.trace_add("write", self._fire)
        self.var_hour.trace_add("write", self._fire)
        self.var_min.trace_add("write", self._fire)

    def _fire(self, *args):
        if self._on_change:
            self._on_change()

    def set_on_change(self, cb):
        self._on_change = cb

    def set_datetime(self, dt):
        if isinstance(dt, str):
            dt = parse_fecha(dt)
        if not dt:
            dt = datetime.now()
        self.var_date.set(dt.strftime("%Y-%m-%d"))
        self.var_hour.set(f"{dt.hour:02d}")
        self.var_min.set(f"{dt.minute:02d}")

    def get_datetime(self):
        try:
            d = datetime.strptime(self.var_date.get().strip(), "%Y-%m-%d")
            return d.replace(hour=int(self.var_hour.get()),
                             minute=int(self.var_min.get()))
        except (ValueError, TypeError):
            return None

    def get_string(self):
        dt = self.get_datetime()
        return dt.strftime(FMT) if dt else ""


# ------------------ DIÁLOGO DE EDICIÓN ------------------
class EditDialog(tk.Toplevel):
    def __init__(self, master, idx, record, on_save):
        super().__init__(master)
        self.title("Editar medicamento")
        self.transient(master)
        self.grab_set()
        self.resizable(False, False)
        self.idx = idx
        self.on_save = on_save

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Paciente:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        self.e_paciente = ttk.Entry(frm, width=30)
        self.e_paciente.insert(0, record[0])
        self.e_paciente.grid(row=0, column=1, padx=6, pady=6)

        ttk.Label(frm, text="Medicamento:").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        self.e_med = ttk.Entry(frm, width=30)
        self.e_med.insert(0, record[1])
        self.e_med.grid(row=1, column=1, padx=6, pady=6)

        ttk.Label(frm, text="Último consumo:").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        self.picker = DateTimePicker(frm, initial=record[2], on_change=self._recalcular)
        self.picker.grid(row=2, column=1, padx=6, pady=6, sticky="w")

        ttk.Label(frm, text="Frecuencia:").grid(row=3, column=0, sticky="e", padx=6, pady=6)
        self.var_frec = tk.StringVar(value=record[4])
        self.var_frec.trace_add("write", lambda *a: self._recalcular())
        ttk.Combobox(frm, values=FRECUENCIAS, width=27,
                    textvariable=self.var_frec,
                    state="readonly"
                    ).grid(
                        row=3,
                        column=1,
                        padx=6,
                        pady=6,
                        sticky="w"
                        )

        ttk.Label(frm, text="Siguiente consumo:").grid(row=4, column=0, sticky="e", padx=6, pady=6)
        self.var_sgte = tk.StringVar()
        ttk.Entry(frm, width=30, textvariable=self.var_sgte,
                  state="readonly").grid(row=4, column=1, padx=6, pady=6)

        btns = ttk.Frame(frm)
        btns.grid(row=5, column=0, columnspan=2, pady=(12, 0))
        ttk.Button(btns, text="Guardar", command=self._save).pack(side="left", padx=4)
        ttk.Button(btns, text="Cancelar", command=self.destroy).pack(side="left", padx=4)

        self._recalcular()
        self._centrar_sobre_padre(master)
        self.bind("<Escape>", lambda e: self.destroy())

    def _recalcular(self):
        ultimo = self.picker.get_string()
        sgte = calcular_siguiente(ultimo, self.var_frec.get().strip())
        self.var_sgte.set(sgte or "")

    def _save(self):
        paciente = limpiar(self.e_paciente.get())
        med = limpiar(self.e_med.get())
        ultimo = self.picker.get_string()
        frec = limpiar(self.var_frec.get())
        sgte = self.var_sgte.get().strip()

        if not paciente or not med:
            messagebox.showwarning("Faltan datos",
                                   "Debe indicar paciente y medicamento.", parent=self)
            return
        if not ultimo:
            messagebox.showerror("Fecha inválida",
                                 "Verifica la fecha del último consumo.", parent=self)
            return

        self.on_save(self.idx, [paciente, med, ultimo, sgte, frec])
        self.destroy()

    def _centrar_sobre_padre(self, parent):
        """Centra el diálogo sobre la ventana padre, sin salirse de la pantalla."""
        self.update_idletasks()
        w = self.winfo_reqwidth()
        h = self.winfo_reqheight()

        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()

        x = px + (pw - w) // 2
        y = py + (ph - h) // 2

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, min(x, sw - w))
        y = max(0, min(y, sh - h))

        self.geometry(f"+{x}+{y}")

# ------------------ APP ------------------
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GesMed - Gestor de Medicamentos")
        self.geometry("1180x720")
        self.minsize(1040, 620)
        self.datos = cargar()
        self.checked = set()

        self._aplicar_icono()

        self._build_ui()
        self._centrar_ventana(1180, 720)   # ← NUEVO
        self._recalcular()
        self._refrescar()

        self.recordador = Recordador(lambda: self.datos, intervalo_seg=10, repetir_cada_min=1/3)
        self.recordador.iniciar()
        print("[APP] Notificador PERSISTENTE iniciado - Cada 20 segundos")
        
        # Forzar comprobación inmediata
        try:
            self.recordador.forzar_comprobacion()
        except Exception as e:
            print(f"[APP] Error forzando comprobación: {e}")

        self.after(30000, self._auto_refrescar)
        self.after(600, self._alerta_inicio)
        self.after(2000, self._notificar_atrasados_inicio)
        self.after(3000, lambda: self.recordador.forzar_comprobacion() if hasattr(self, 'recordador') else None)

    def destroy(self):
        """Detiene el hilo al cerrar la ventana."""
        if hasattr(self, "recordador"):
            self.recordador.detener()
        super().destroy()

    def _aplicar_icono(self):
        """Aplica el .ico a la ventana. Si falla, intenta con .png."""
        try:
            if os.path.isfile(ICONO):
                # iconbitmap funciona con .ico en Windows
                self.iconbitmap(default=ICONO)
            else:
                # Fallback: PNG (necesario en Linux/Mac, y por si falta el .ico)
                png = ICONO.replace(".ico", ".png")
                if os.path.isfile(png):
                    img = tk.PhotoImage(file=png)
                    self.iconphoto(True, img)
                    self._icono_ref = img   # mantener referencia
        except Exception as e:
            print(f"[icono] No se pudo cargar: {e}")

    # ---------- auto refresco ----------
    def _auto_refrescar(self):
        try:
            self._refrescar()
        except Exception:
            pass
        self.after(30000, self._auto_refrescar)

    def _alerta_inicio(self):
        atrasados = [(i, d) for i, d in enumerate(self.datos)
                     if estado_registro(d[3])[1] == "atrasado"]
        if not atrasados:
            return
        nombres = "\n".join(f"• {d[0]} – {d[1]} (era: {d[3]})"
                            for _, d in atrasados[:10])
        extra = f"\n... y {len(atrasados)-10} más" if len(atrasados) > 10 else ""
        messagebox.showwarning(
            "Medicamentos NO consumidos",
            f"Hay {len(atrasados)} medicamento(s) que NO se consumieron a la hora prevista:\n\n"
            f"{nombres}{extra}"
        )

    def _notificar_atrasados_inicio(self):
        """Muestra notificaciones para medicamentos ya atrasados al iniciar."""
        try:
            from utils import parse_fecha
            from datetime import datetime
            ahora = datetime.now()
            print(f"[APP] Revisando notificaciones al inicio - {len(self.datos)} registros")
            for d in self.datos:
                try:
                    paciente, med, _, sgte, _ = d
                    dt_sgte = parse_fecha(sgte)
                    if dt_sgte and ahora >= dt_sgte:
                        print(f"[APP] Notificando atrasado: {paciente} - {med}")
                        if hasattr(self, 'recordador'):
                            self.recordador._lanzar_notificacion(paciente, med, sgte, primera_vez=True)
                except Exception:
                    continue
        except Exception as e:
            print(f"[APP] Error en notificaciones inicio: {e}")

    # ---------------- UI ----------------
    def _build_ui(self):
        # -------- FORMULARIO --------
        form = ttk.LabelFrame(self, text="Nuevo medicamento")
        form.pack(fill="x", padx=10, pady=6)

        ttk.Label(form, text="Paciente:").grid(row=0, column=0, sticky="e", padx=6, pady=4)
        self.e_paciente = ttk.Entry(form, width=26)
        self.e_paciente.grid(row=0, column=1, padx=6, pady=4)

        ttk.Label(form, text="Medicamento:").grid(row=0, column=2, sticky="e", padx=6, pady=4)
        self.e_med = ttk.Entry(form, width=26)
        self.e_med.grid(row=0, column=3, padx=6, pady=4)

        # ---- Último consumo (picker) ----
        ttk.Label(form, text="Último consumo:").grid(row=1, column=0, sticky="e", padx=6, pady=4)
        self.ultimo_picker = DateTimePicker(form, initial=datetime.now())
        self.ultimo_picker.grid(row=1, column=1, padx=6, pady=4, sticky="w")
        self.ultimo_picker.set_on_change(self._recalcular)

        ttk.Button(form, text="Ahora", width=8,
                   command=self._set_ahora).grid(
            row=1, column=2, sticky="w", padx=6, pady=4)

        # ---- Frecuencia ----
        ttk.Label(form, text="Frecuencia:").grid(row=2, column=0, sticky="e", padx=6, pady=4)
        self.var_frec = tk.StringVar(value="8 horas")
        self.var_frec.trace_add("write", self._recalcular)
        ttk.Combobox(
            form,
            values=FRECUENCIAS,
            width=23,
            textvariable=self.var_frec,
            state="readonly"
            ).grid(
                row=2, column=1, padx=6, pady=4
                )

        # ---- Siguiente consumo (SOLO LECTURA, auto-calculado) ----
        ttk.Label(form, text="Siguiente consumo:").grid(row=3, column=0, sticky="e", padx=6, pady=4)
        self.var_sgte = tk.StringVar()
        ttk.Entry(form, width=24, textvariable=self.var_sgte,
                  state="readonly").grid(row=3, column=1, padx=6, pady=4)

        ttk.Button(form, text="Añadir medicamento",
                   command=self._anadir).grid(row=3, column=3, padx=6, pady=4)

        # -------- FILTROS --------
        filtro = ttk.Frame(self)
        filtro.pack(fill="x", padx=10, pady=4)
        ttk.Label(filtro, text="Filtrar por paciente:").pack(side="left", padx=4)
        self.e_filtro = ttk.Entry(filtro, width=22)
        self.e_filtro.pack(side="left", padx=4)
        self.e_filtro.bind("<KeyRelease>", lambda e: self._refrescar())

        self.var_solo_atrasados = tk.BooleanVar(value=False)
        ttk.Checkbutton(filtro, text="Solo NO consumidos",
                        variable=self.var_solo_atrasados,
                        command=self._refrescar).pack(side="left", padx=8)

        ttk.Button(filtro, text="Limpiar filtros",
                   command=self._limpiar_filtro).pack(side="left", padx=4)

        # -------- TABLA --------
        cols = ("sel", "paciente", "medicamento", "ultimo", "sgte", "frecuencia", "estado")
        titulos = ("", "Paciente", "Medicamento", "Último consumo",
                   "Siguiente consumo", "Frecuencia", "Estado")
        cont = ttk.Frame(self)
        cont.pack(fill="both", expand=True, padx=10, pady=6)

        self.tree = ttk.Treeview(cont, columns=cols, show="headings")
        for c, t in zip(cols, titulos):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=160, anchor="center")
        self.tree.column("sel", width=36, minwidth=36, stretch=False)
        self.tree.column("estado", width=210)

        self.tree.tag_configure("atrasado",    background="#ffb3b3", foreground="#7a0000")
        self.tree.tag_configure("cercano",     background="#fff3b0")
        self.tree.tag_configure("ok",          background="#d4edda")
        self.tree.tag_configure("desconocido", background="#eeeeee")

        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(cont, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

        # Click sobre la 1ª columna → toggle check
        self.tree.bind("<Button-1>", self._on_tree_click)

        # -------- BOTONES ACCIONES --------
        btns = ttk.Frame(self)
        btns.pack(fill="x", padx=10, pady=6)

        tk.Button(btns, text="✔  CONSUMIDO  (actualizar fechas)",
                  bg="#28a745", fg="white", activebackground="#1e7e34",
                  font=("Segoe UI", 10, "bold"), padx=12, pady=4,
                  command=self._consumido).pack(side="left", padx=4)

        ttk.Button(btns, text="Editar seleccionado",
                   command=self._editar).pack(side="left", padx=4)

        ttk.Button(btns, text="Eliminar marcados (☑)",
                   command=self._eliminar_sel).pack(side="left", padx=4)

        ttk.Button(btns, text="Eliminar todos",
                   command=self._eliminar_todos).pack(side="left", padx=4)

        ttk.Button(btns, text="Actualizar lista",
                   command=self._refrescar).pack(side="left", padx=4)

        # -------- BARRA DE ESTADO --------
        self.status = ttk.Label(self, text="", anchor="w")
        self.status.pack(fill="x", padx=12, pady=6)

    def _centrar_ventana(self, width=None, height=None):
        """Centra la ventana principal en la pantalla."""
        self.update_idletasks()
        w = width or self.winfo_width()
        h = height or self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        
    # ---------- AUTO-CÁLCULO ----------
    def _recalcular(self, *args):
        ultimo = self.ultimo_picker.get_string()
        frec = self.var_frec.get().strip()
        sgte = calcular_siguiente(ultimo, frec)
        self.var_sgte.set(sgte or "")

    def _set_ahora(self):
        self.ultimo_picker.set_datetime(datetime.now())

    # ---------- CHECKBOX DE LA TABLA ----------
    def _on_tree_click(self, event):
        if self.tree.identify("region", event.x, event.y) != "cell":
            return
        if self.tree.identify_column(event.x) != "#1":
            return
        iid = self.tree.identify_row(event.y)
        if not iid:
            return
        self._toggle_check(iid)

    def _toggle_check(self, iid):
        values = self.tree.item(iid, "values")
        # key = (paciente, med, ultimo, sgte, frec)
        key = tuple(values[1:6])
        if key in self.checked:
            self.checked.discard(key)
            self.tree.set(iid, "sel", "☐")
        else:
            self.checked.add(key)
            self.tree.set(iid, "sel", "☑")
        self._refresh_status_only()

    # ---------- REFRESCO ----------
    def _refrescar(self):
        # Solo conservamos marcas cuyos datos aún existan
        valid_keys = {tuple(d) for d in self.datos}
        self.checked &= valid_keys

        old_sel = self.tree.selection()
        for i in self.tree.get_children():
            self.tree.delete(i)

        filtro = self.e_filtro.get().strip().lower()
        solo_atr = self.var_solo_atrasados.get()

        for idx, d in enumerate(self.datos):
            txt_estado, tag = estado_registro(d[3])
            if filtro and filtro not in d[0].lower():
                continue
            if solo_atr and tag != "atrasado":
                continue

            mark = "☑" if tuple(d) in self.checked else "☐"
            self.tree.insert("", "end", iid=str(idx),
                             values=(mark, d[0], d[1], d[2], d[3], d[4], txt_estado),
                             tags=(tag,))

        # Restaurar selección (fila resaltada) si sigue existiendo
        keep = [s for s in old_sel if self.tree.exists(s)]
        if keep:
            self.tree.selection_set(keep)

        self._refresh_status_only()

    def _refresh_status_only(self):
        total = len(self.datos)
        atrasados = sum(1 for d in self.datos
                        if estado_registro(d[3])[1] == "atrasado")
        mostrados = len(self.tree.get_children())
        self.status.config(
            text=(f"Total: {total}   |   Mostrados: {mostrados}   |   "
                  f"NO consumidos: {atrasados}   |   Marcados: {len(self.checked)}   |   "
                  f"Archivo: {ARCHIVO}")
        )

    def _limpiar_filtro(self):
        self.e_filtro.delete(0, "end")
        self.var_solo_atrasados.set(False)
        self._refrescar()

    # ---------- ACCIONES ----------
    def _anadir(self):
        paciente = limpiar(self.e_paciente.get())
        med = limpiar(self.e_med.get())
        ultimo = self.ultimo_picker.get_string()
        frec = limpiar(self.var_frec.get())
        sgte = self.var_sgte.get().strip()

        if not paciente or not med:
            messagebox.showwarning("Faltan datos",
                                   "Debe indicar paciente y medicamento.")
            return
        if not ultimo:
            messagebox.showerror("Fecha inválida",
                                 "Verifica la fecha del último consumo.")
            return
        if not sgte:
            sgte = calcular_siguiente(ultimo, frec) or ""

        self.datos.append([paciente, med, ultimo, sgte, frec])
        guardar(self.datos)
        if hasattr(self, 'recordador'):
            self.recordador.limpiar_notificaciones()
        self._refrescar()

        self.e_med.delete(0, "end")
        self._set_ahora()
        messagebox.showinfo("Guardado", "Medicamento añadido correctamente.")

    def _editar(self):
        sel = self.tree.selection()
        if len(sel) != 1:
            messagebox.showinfo("Selección",
                                "Selecciona exactamente un registro para editar.")
            return
        idx = int(sel[0])
        EditDialog(self, idx, self.datos[idx], self._on_edit_saved)

    def _on_edit_saved(self, idx, nuevo):
        self.datos[idx] = nuevo
        guardar(self.datos)
        self._refrescar()

    def _consumido(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selección",
                                "Selecciona el/los medicamento(s) que has consumido.")
            return

        ahora = datetime.now()
        atrasados = []
        for item in sel:
            d = self.datos[int(item)]
            sgte_dt = parse_fecha(d[3])
            if sgte_dt and ahora > sgte_dt:
                atrasados.append((int(item), d))

        if atrasados:
            nombres = "\n".join(f"• {d[0]} – {d[1]}   (programado: {d[3]})"
                                for _, d in atrasados)
            if not messagebox.askyesno(
                "Consumo atrasado",
                f"Estos medicamentos NO se consumieron a tiempo:\n\n"
                f"{nombres}\n\n"
                "¿Registrar el consumo AHORA (hora actual) y recalcular "
                "la próxima dosis?"):
                return

        for item in sel:
            idx = int(item)
            d = self.datos[idx]
            ahora_str = ahora.strftime(FMT)
            nuevo_sgte = calcular_siguiente(ahora_str, d[4]) or ""
            self.datos[idx] = [d[0], d[1], ahora_str, nuevo_sgte, d[4]]

        guardar(self.datos)
        if hasattr(self, 'recordador'):
            self.recordador.limpiar_notificaciones()
        self._refrescar()
        messagebox.showinfo("Consumido",
                            f"Se actualizaron {len(sel)} registro(s).\n"
                            "Hora de consumo registrada y próxima dosis recalculada.")

    def _eliminar_sel(self):
        if not self.checked:
            messagebox.showinfo(
                "Sin marcados",
                "Marca al menos un registro con la casilla ☐ de la izquierda.")
            return
        if not messagebox.askyesno(
            "Confirmar",
            f"¿Eliminar {len(self.checked)} registro(s) marcado(s)?"):
            return

        to_remove = list(self.checked)
        nuevos = []
        for d in self.datos:
            key = tuple(d)
            if key in to_remove:
                to_remove.remove(key)   # solo una ocurrencia por tupla
                continue
            nuevos.append(d)
        self.datos = nuevos
        self.checked = set()
        guardar(self.datos)
        self._refrescar()

    def _eliminar_todos(self):
        if not self.datos:
            messagebox.showinfo("Vacío", "No hay registros para eliminar.")
            return
        if not messagebox.askyesno(
            "Confirmar",
            "¿Eliminar TODOS los registros?\nEsta acción no se puede deshacer."):
            return
        self.datos = []
        self.checked = set()
        guardar(self.datos)
        self._refrescar()


if __name__ == "__main__":
    App().mainloop()