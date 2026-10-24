# GesMed

GesMed (Gestor de Medicamentos) es una aplicación de escritorio para Windows desarrollada en Python con Tkinter, pensada para controlar las tomas de medicamentos por paciente. Permite registrar dosis, calcular automáticamente la próxima toma según la frecuencia, marcar como consumidas, filtrar, editar/eliminar registros y recibir notificaciones de recordatorio.

## Características

- **Registro de medicamentos**: Añade paciente, medicamento, fecha/hora del último consumo y frecuencia.
- **Cálculo automático**: Calcula la fecha/hora de la siguiente toma en función de la frecuencia seleccionada (4h, 6h, 8h, 12h, 24h, 1/2/3 días, 1 semana, 15 días).
- **Seguimiento visual**: La tabla muestra el estado con colores (atrasado en rojo, próximo/cercano en amarillo, al día en verde).
- **Marcar como consumido**: Al pulsar "CONSUMIDO", se registra la hora actual como último consumo y se recalcula la siguiente dosis. Si estaba atrasado, avisa antes de actualizar.
- **Recordatorios**: Notificaciones nativas de Windows mediante `winotify` que avisan cuando llega la hora de una toma. Se revisa cada 30 segundos.
- **Filtros**: Filtra por paciente y muestra solo medicamentos "NO consumidos" (atrasados).
- **Edición y borrado**: Edita cualquier registro desde un diálogo, elimina uno/marcados o todos los registros.
- **Persistencia**: Guarda los datos en `GesMed.ini` dentro de la carpeta `Documentos` del usuario (compatible con distintos idiomas del sistema).
- **Icono y empaquetado**: Incluye `icono.ico` y archivos `.spec` para generar un ejecutable con PyInstaller.

## Estructura del proyecto

| Archivo | Descripción |
| --- | --- |
| `main.py` | Interfaz principal con Tkinter, formulario, tabla, diálogos (`EditDialog`, `DateTimePicker`) y lógica de acciones. |
| `config.py` | Configuración: ubicación del archivo de datos (`GesMed.ini` en Documentos), formato de fecha/hora, lista de frecuencias y ruta de recursos (`ruta_recurso`). |
| `utils.py` | Utilidades: parseo de fechas, cálculo de siguiente toma (`calcular_siguiente`), estado del registro (`estado_registro` con colores/etiquetas), carga/guardado (`cargar`/`guardar`) y limpieza de datos. |
| `notifier.py` | `Recordador`: hilo en segundo plano que revisa las tomas cada 30s y lanza notificaciones de Windows con `winotify`. |
| `icono.ico` / `icono.png` | Icono de la aplicación. |
| `compilar.bash` | Script para compilar a .exe con PyInstaller (Linux/WSL/Git Bash). |
| `GesMed.spec` / `GestorMedicamentos.spec` | Archivos de configuración de PyInstaller. |
| `build/`, `dist/` | Salidas de compilación. |
| `venv/` | Entorno virtual (local). |

## Requisitos

- Python 3.x
- Dependencias:
  - `tkcalendar` (calendario para selección de fecha/hora)
  - `winotify` (notificaciones en Windows)

Puedes instalarlas con:

```bash
pip install tkcalendar winotify
```

## Uso

1. Ejecuta la aplicación:
   ```bash
   python main.py
   ```
2. Añade un medicamento desde el formulario "Nuevo medicamento": indica paciente, medicamento, último consumo, frecuencia. La siguiente toma se calcula automáticamente.
3. Usa "CONSUMIDO (actualizar fechas)" para marcar tomas realizadas: se actualiza la hora de consumo y se recalcula la próxima dosis.
4. Filtra por paciente o usa "Solo NO consumidos" para ver las tomas atrasadas.
5. Edita, elimina marcados o elimina todos desde los botones inferiores.
6. Las notificaciones aparecerán automáticamente cuando llegue la hora programada.

## Datos

Los registros se guardan en:
```
<Carpeta Documentos del usuario>/GesMed.ini
```

Formato por línea (separador `|`):
```
Paciente|Medicamento|Último consumo (YYYY-MM-DD HH:MM)|Siguiente consumo (YYYY-MM-DD HH:MM)|Frecuencia
```

## Compilar a ejecutable (Windows)

El proyecto incluye archivos `.spec` para PyInstaller. También hay `compilar.bash`. Un ejemplo típico sería:

```bash
pyinstaller --onefile --windowed --icon=icono.ico main.py
```

Los recursos (`icono.ico`) se localizan mediante `ruta_recurso()` para funcionar tanto en modo desarrollo como en `.exe`.
