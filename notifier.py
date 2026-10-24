import threading
import time
from datetime import datetime
from winotify import Notification, audio
from utils import parse_fecha

class Recordador:
    def __init__(self, get_datos_func, intervalo_seg=30):
        """
        get_datos_func: función que devuelve la lista de registros actual.
        intervalo_seg: cada cuántos segundos revisa si hay dosis vencidas.
        """
        self.get_datos = get_datos_func
        self.intervalo = intervalo_seg
        self._notificados = set()   # evita repetir la misma dosis
        self._stop = threading.Event()
        self._hilo = threading.Thread(target=self._bucle, daemon=True)

    def iniciar(self):
        self._hilo.start()

    def detener(self):
        self._stop.set()

    def _bucle(self):
        while not self._stop.is_set():
            try:
                self._revisar()
            except Exception:
                pass
            time.sleep(self.intervalo)

    def _revisar(self):
        ahora = datetime.now()
        for d in self.get_datos():
            # d = [paciente, medicamento, ultimo, sgte, frecuencia]
            paciente, med, _, sgte, _ = d
            dt_sgte = parse_fecha(sgte)
            if not dt_sgte:
                continue

            if ahora >= dt_sgte:
                clave = (paciente, med, sgte)   # identifica la dosis concreta
                if clave in self._notificados:
                    continue

                self._notificados.add(clave)
                self._lanzar_notificacion(paciente, med, sgte)

    def _lanzar_notificacion(self, paciente, med, sgte):
        toast = Notification(
            app_id="Gestor de Medicamentos",
            title=f"💊 {paciente} – {med}",
            msg=f"Es hora de consumir: {med}\nProgramado: {sgte}",
            duration="long",
        )
        toast.set_audio(audio.Reminder, loop=False)  # sonido de recordatorio
        toast.show()