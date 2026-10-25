import threading
import time
from datetime import datetime
from utils import parse_fecha

try:
    from winotify import Notification, audio
    WINOTIFY_OK = True
except Exception as e:
    print(f"[NOTIFICADOR] winotify no disponible: {e}")
    WINOTIFY_OK = False

try:
    from plyer import notification as plyer_notification
    PLYER_OK = True
except Exception as e:
    print(f"[NOTIFICADOR] plyer no disponible: {e}")
    PLYER_OK = False


class Recordador:
    def __init__(self, get_datos_func, intervalo_seg=10, repetir_cada_min=1/3):
        """
        get_datos_func: función que devuelve la lista de registros actual.
        intervalo_seg: cada cuántos segundos revisa si hay dosis vencidas.
        repetir_cada_min: cada cuántos minutos vuelve a notificar si sigue sin consumirse.
        """
        self.get_datos = get_datos_func
        self.intervalo = intervalo_seg
        self.repetir_cada_min = repetir_cada_min
        self._notificados = {}  # clave -> última vez que se notificó (timestamp)
        self._stop = threading.Event()
        self._hilo = threading.Thread(target=self._bucle, daemon=True)
        self.activo = False

    def iniciar(self):
        self.activo = True
        if not self._hilo.is_alive():
            self._hilo = threading.Thread(target=self._bucle, daemon=True)
        self._hilo.start()
        print(f"[NOTIFICADOR] Iniciado PERSISTENTE cada 20s (winotify={WINOTIFY_OK}, plyer={PLYER_OK})")
        # Comprobar inmediatamente al iniciar
        try:
            threading.Thread(target=self._revisar, daemon=True).start()
        except Exception as e:
            print(f"[NOTIFICADOR] Error en comprobación inicial: {e}")

    def forzar_comprobacion(self):
        """Fuerza una comprobación inmediata de todas las dosis."""
        try:
            print("[NOTIFICADOR] Forzando comprobación inmediata...")
            threading.Thread(target=self._revisar, daemon=True).start()
        except Exception as e:
            print(f"[NOTIFICADOR] Error al forzar comprobación: {e}")

    def detener(self):
        self.activo = False
        self._stop.set()

    def limpiar_notificaciones(self):
        """Limpia el historial de notificaciones."""
        self._notificados.clear()
        print("[NOTIFICADOR] Historial de notificaciones limpiado")

    def _bucle(self):
        print(f"[NOTIFICADOR] Revisando cada {self.intervalo} segundos - MODO PERSISTENTE")
        while not self._stop.is_set():
            try:
                self._revisar()
            except Exception as e:
                print(f"[NOTIFICADOR] Error en bucle: {e}")
            time.sleep(self.intervalo)

    def _revisar(self):
        ahora = datetime.now()
        try:
            datos_actuales = self.get_datos()
        except Exception as e:
            print(f"[NOTIFICADOR] Error obteniendo datos: {e}")
            return
        
        if not datos_actuales:
            return
        
        # Limpiar notificaciones de registros que ya no existen o cuya fecha cambió
        claves_actuales = set()
        for d in datos_actuales:
            try:
                paciente, med, _, sgte, _ = d
                clave = (paciente, med, sgte)
                claves_actuales.add(clave)
            except Exception:
                continue
        
        # Eliminar claves obsoletas
        for clave in list(self._notificados.keys()):
            if clave not in claves_actuales:
                self._notificados.pop(clave, None)
        
        for d in datos_actuales:
            try:
                # d = [paciente, medicamento, ultimo, sgte, frecuencia]
                paciente, med, _, sgte, frec = d
                dt_sgte = parse_fecha(sgte)
                if not dt_sgte:
                    continue

                if ahora >= dt_sgte:
                    clave = (paciente, med, sgte)
                    ahora_ts = time.time()
                    
                    if clave not in self._notificados:
                        # Primera notificación
                        self._notificados[clave] = ahora_ts
                        print(f"[NOTIFICADOR] PRIMERA ALERTA: {paciente} - {med} a las {sgte}")
                        self._lanzar_notificacion(paciente, med, sgte, primera_vez=True)
                    else:
                        # Verificar si ha pasado suficiente tiempo para repetir (20 segundos)
                        ultima_notif = self._notificados[clave]
                        segundos_transcurridos = ahora_ts - ultima_notif
                        if segundos_transcurridos >= 20:
                            self._notificados[clave] = ahora_ts
                            print(f"[NOTIFICADOR] ALERTA PERSISTENTE: {paciente} - {med} (hace {int(segundos_transcurridos)} seg)")
                            self._lanzar_notificacion(paciente, med, sgte, primera_vez=False)
            except Exception as e:
                print(f"[NOTIFICADOR] Error procesando registro: {e}")
                continue

    def _lanzar_notificacion(self, paciente, med, sgte, primera_vez=True):
        if primera_vez:
            titulo = "!!! TOMA URGENTE !!!"
            mensaje = f"Paciente: {paciente} | Med: {med} | Hora: {sgte} | TOMALO AHORA!"
        else:
            titulo = "!!! ALERTA PERSISTENTE !!!"
            mensaje = f"Paciente: {paciente} | SIN TOMAR: {med} | Programado: {sgte} | TOMALO YA!"
        
        enviado = False
        
        # Sonido escandaloso - ejecutar en thread separado
        def _sonido():
            try:
                import winsound
                for _ in range(8):
                    winsound.Beep(3500, 80)
                    winsound.Beep(3000, 80)
                    winsound.Beep(2500, 80)
                winsound.MessageBeep(-1)
            except Exception as e:
                print(f"[NOTIFICADOR] Error sonido: {e}")
        
        try:
            threading.Thread(target=_sonido, daemon=True).start()
        except Exception:
            pass
        
        if WINOTIFY_OK:
            try:
                toast = Notification(
                    app_id="GesMed",
                    title=titulo,
                    msg=mensaje,
                    duration="long",
                )
                try:
                    toast.set_audio(audio.Reminder, loop=False)
                except Exception:
                    try:
                        toast.set_audio(audio.Mail, loop=False)
                    except Exception:
                        try:
                            toast.set_audio(audio.Default, loop=False)
                        except Exception:
                            pass
                try:
                    toast.show()
                    print(f"[NOTIFICADOR] Enviada con winotify: {titulo}")
                    enviado = True
                except Exception as e:
                    print(f"[NOTIFICADOR] Error winotify show: {e}")
            except Exception as e:
                print(f"[NOTIFICADOR] Error winotify: {e}")
        
        if PLYER_OK:
            try:
                plyer_notification.notify(
                    title=titulo,
                    message=mensaje,
                    app_name="GesMed",
                    timeout=15
                )
                print(f"[NOTIFICADOR] Enviada con plyer: {titulo}")
                enviado = True
            except Exception as e:
                print(f"[NOTIFICADOR] Error plyer: {e}")
        
        if not enviado:
            print(f"[NOTIFICADOR] NO SE PUDO ENVIAR NOTIFICACIÓN: {titulo}")