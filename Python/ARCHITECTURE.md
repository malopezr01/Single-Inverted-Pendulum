# Adquisición y experimentos — fases 2 y 3

- `SerialLink` y `SerialWorker`: puerto serie, comandos y parser en el QThread serie.
- `ExperimentSession`: cola FIFO y un hilo de registro independiente. Es el único propietario de `ExperimentLogger`. Abre el experimento en la primera DATA RUNNING, conserva el CSV durante READY y lo cierra en FINISH, HOME, FAULT, E-STOP, reinicio o cierre de la aplicación.
- `TelemetryBuffer`: historial visual con bloqueo y snapshots por señal; no contiene ni elimina datos del CSV. Ventana de 10 s por defecto, ajustable entre 1 y 30 s, con límite adicional de 20 000 muestras. Las muestras contienen todas las señales recibidas.
- GUI: muestra estados, solicita acciones y dibuja snapshots. Recibe avisos del registro mediante señales Qt; nunca escribe el CSV.

Se conservan las muestras de RUNNING, como antes. Las muestras de READY no se guardan. El cierre de la aplicación detiene primero la adquisición y drena la cola de registro antes de terminar. Un fallo de escritura se comunica a la GUI y suspende el registro hasta un nuevo INIT; no detiene el hilo serie. La cola no descarta muestras: un disco persistentemente más lento que la entrada aumentará la memoria utilizada.

El CSV sigue teniendo columnas fijas. El selector de señales, pausa/limpieza visual, columnas dinámicas y metadata pertenecen a las fases siguientes. Las señales adicionales ya se conservan en el buffer visual.

## Verificación

Desde `Python`, con el entorno virtual activado:

```sh
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
```

Incluye 10 000 muestras sin GUI, pausa/reanudación, FINISH, HOME, FAULT, reinicio, error de disco y una integración con Qt real y puerto simulado. En hardware: HOME → START → STOP/PAUSE → START → STOP/PAUSE → FINISH; comprobar CSV, gráficas finales y cierre de la aplicación durante RUNNING.

## Visualización — fase 3

PyQtGraph consulta el buffer cada 40 ms (25 Hz nominales). Solo redibuja si cambia la revisión del buffer; la escritura del CSV no depende de ese temporizador. El bloqueo del buffer se mantiene únicamente durante la copia de referencias: la construcción de las series se realiza después, sin bloquear al productor.

El control «Visible window (s)» ajusta la ventana temporal. Reducirla descarta únicamente historial visual; ampliarla se completa con muestras nuevas. Se usa Time del ESP32 (tiempo activo), por lo que la pausa del controlador conserva las curvas. Un retroceso del tiempo limpia el historial visual; tiempos no finitos no se añaden al buffer. El CSV no se modifica por estas decisiones de visualización.

Las curvas actuales siguen siendo theta, x y u; el selector dinámico pertenece a la fase 4. La prueba a 500 muestras/s utiliza tiempos simulados y comprueba retención y señales adicionales; no certifica el rendimiento del enlace físico del ESP32.

## Ventanas de gráficas

La ventana principal se ajusta al área disponible de la pantalla y mantiene los controles en dos filas fuera del área desplazable. Los botones Open theta/x/u plot abren ventanas independientes no modales. Cerrar una gráfica la oculta: adquisición, CSV y buffer continúan, y se puede reabrir con el historial disponible. Al cerrar la aplicación se cierran todas las ventanas. Las curvas usan fondo blanco y colores azul, naranja y violeta.
