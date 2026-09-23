# Adquisición y experimentos — fases 2, 3, 4 y 6

- `SerialLink` y `SerialWorker`: puerto serie, comandos y parser en el QThread serie.
- `ExperimentSession`: cola FIFO y un hilo de registro independiente. Es el único propietario de `ExperimentLogger`. Abre el experimento en la primera DATA RUNNING, conserva el CSV durante READY y lo cierra en FINISH, HOME, FAULT, E-STOP, reinicio o cierre de la aplicación.
- `TelemetryBuffer`: historial visual con bloqueo y snapshots por señal; no contiene ni elimina datos del CSV. Ventana de 10 s por defecto, ajustable entre 1 y 30 s, con límite adicional de 20 000 muestras. Las muestras contienen todas las señales recibidas.
- GUI: muestra estados, solicita acciones y dibuja snapshots. Recibe avisos del registro mediante señales Qt; nunca escribe el CSV.

Se conservan las muestras de RUNNING, como antes. Las muestras de READY no se guardan. El cierre de la aplicación detiene primero la adquisición y drena la cola de registro antes de terminar. Un fallo de escritura se comunica a la GUI y suspende el registro hasta un nuevo INIT; no detiene el hilo serie. La cola no descarta muestras: un disco persistentemente más lento que la entrada aumentará la memoria utilizada.

El CSV utiliza las columnas del HEADER. La fase 5 (pausa/limpieza visual) se ha descartado. Las señales adicionales se conservan tanto en el buffer visual como en el CSV.

## Verificación

Desde `Python`, con el entorno virtual activado:

```sh
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
```

Incluye 10 000 muestras sin GUI, pausa/reanudación, FINISH, HOME, FAULT, reinicio, error de disco y una integración con Qt real y puerto simulado. En hardware: HOME → START → STOP/PAUSE → START → STOP/PAUSE → FINISH; comprobar CSV, gráficas finales y cierre de la aplicación durante RUNNING.

## Visualización — fase 3

PyQtGraph consulta el buffer cada 40 ms (25 Hz nominales). Solo redibuja si cambia la revisión del buffer; la escritura del CSV no depende de ese temporizador. El bloqueo del buffer se mantiene únicamente durante la copia de referencias: la construcción de las series se realiza después, sin bloquear al productor.

El control «Visible window (s)» ajusta la ventana temporal. Reducirla descarta únicamente historial visual; ampliarla se completa con muestras nuevas. Se usa Time del ESP32 (tiempo activo), por lo que la pausa del controlador conserva las curvas. Un retroceso del tiempo limpia el historial visual; tiempos no finitos no se añaden al buffer. El CSV no se modifica por estas decisiones de visualización.

Las curvas se crean dinámicamente mediante el selector de señales. La prueba a 500 muestras/s utiliza tiempos simulados y comprueba retención y señales adicionales; no certifica el rendimiento del enlace físico del ESP32.

## Ventanas de gráficas

La ventana principal se ajusta al área disponible de la pantalla y mantiene los controles en dos filas fuera del área desplazable. El botón Open selected plots abre ventanas independientes no modales para las señales marcadas. Cerrar una gráfica la oculta: adquisición, CSV y buffer continúan, y se puede reabrir con el historial disponible. Al cerrar la aplicación se cierran todas las ventanas. Las curvas usan fondo blanco y colores azul, naranja y violeta.

## Selector de señales — fase 4

HEADER genera automáticamente una lista de casillas. Time se reserva como eje horizontal; todas las demás señales, incluidos state y mode, se pueden representar. theta, x y u aparecen marcadas inicialmente, pero no se abren ventanas hasta pulsar Open selected plots. Las señales nuevas no necesitan configuración Python; se asigna un color automáticamente y se usa su nombre como etiqueta, sin inventar unidades.

Las cabeceras repetidas no recrean ventanas ni cambian selecciones. Si el esquema cambia, se conserva la selección de las señales restantes, se añaden las nuevas y se cierran las retiradas. Desmarcar oculta la gráfica; los datos siguen llegando al buffer y al registro bajo las reglas de la fase 2. Cerrar manualmente una ventana permite volver a abrirla con el botón. Las columnas CSV siguen el HEADER desde la fase 6.

## CSV y metadatos — fase 6

Cada experimento crea una carpeta exclusiva `experiments/experiment_FECHA_HORA_ID/` con `data.csv` y `metadata.json`. El orden del CSV es exactamente el del HEADER. SerialWorker entrega HEADER y DATA por la misma cola FIFO; las repeticiones idénticas no abren archivos nuevos. Un cambio de nombres u orden cierra el segmento anterior con motivo `Telemetry HEADER changed`; la siguiente DATA RUNNING abre otro. En READY no se abre un archivo vacío: se espera a reanudar. Los CSV de segmentos previos se conservan sin mezclarlos. Las tramas antiguas key=value usan sus claves como esquema inicial.

Se mantiene la política de guardar únicamente RUNNING; una pausa conserva el archivo abierto. Metadatos: inicio y final con zona horaria, puerto, baudrate, señales, muestras, duración real de la sesión, tiempo cubierto por intervalos dentro de RUNNING, frecuencia estimada y motivo de cierre. La frecuencia se calcula usando intervalos positivos de Time/time, sin cruzar pausas; no es una medida de la frecuencia del control. Si no hay intervalos suficientes se guarda null.

Los metadatos se crean al abrir y se actualizan tras vaciar el CSV cada 50 muestras y al cerrar. Se escriben a un temporal y se sustituyen de forma atómica. El estado `recording` indica que no se confirmó un cierre limpio; los contadores son los del último checkpoint y pueden ir por detrás del CSV. Esto no garantiza conservar los datos aún en memoria ante corte de corriente. Un fallo de escritura sigue notificándose a la GUI y detiene el registro hasta INIT.

Al finalizar se abre un selector de señales del CSV guardado. Open selected plots crea gráficas matplotlib independientes con los datos completos, incluidas señales nuevas. Las curvas state/mode usan escalones; las demás son continuas. Los CSV antiguos siguen siendo legibles. Un cambio de HEADER cierra el segmento sin abrir automáticamente el visor en mitad del control. Los segmentos anteriores y cualquier CSV antiguo se pueden abrir desde Open saved CSV en la ventana principal.

Prueba en hardware: añadir una señal solo en HEADER/DATA, ejecutar START → PAUSE → RESUME → PAUSE → FINISH; revisar la columna nueva, su gráfica y metadata. La frecuencia física del ESP32 no se cambia en esta fase.

## Codificación del modo de control

El firmware y la GUI usan `NONE = 0`, `LQR = 1` y `SWING_UP = 2`. La GUI también muestra `SWING_UP` al recibir el valor anterior `3`, para admitir el firmware previo. Hay que actualizar la GUI junto con el firmware nuevo: la GUI antigua interpretaba `2` como `LQR_FRICTION`.

El parser, el registro y el visor CSV conservan los valores originales: los experimentos previos con swing-up siguen mostrando `3` en sus gráficas y los nuevos muestran `2`. No se recodifican automáticamente los archivos históricos, porque en versiones antiguas `2` identificaba `LQR_FRICTION`; sin conocer la versión de origen no se puede distinguir ese caso del swing-up actual.
