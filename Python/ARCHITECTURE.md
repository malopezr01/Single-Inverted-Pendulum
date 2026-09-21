# Adquisición y experimentos — fase 2

- `SerialLink` y `SerialWorker`: puerto serie, comandos y parser en el QThread serie.
- `ExperimentSession`: cola FIFO y un hilo de registro independiente. Es el único propietario de `ExperimentLogger`. Abre el experimento en la primera DATA RUNNING, conserva el CSV durante READY y lo cierra en FINISH, HOME, FAULT, E-STOP, reinicio o cierre de la aplicación.
- `TelemetryBuffer`: historial visual con bloqueo y snapshots por señal; no contiene ni elimina datos del CSV. Ventana actual de 15 s, con límite adicional de 20 000 muestras.
- GUI: muestra estados, solicita acciones y dibuja snapshots. Recibe avisos del registro mediante señales Qt; nunca escribe el CSV.

Se conservan las muestras de RUNNING, como antes. Las muestras de READY no se guardan. El cierre de la aplicación detiene primero la adquisición y drena la cola de registro antes de terminar. Un fallo de escritura se comunica a la GUI y suspende el registro hasta un nuevo INIT; no detiene el hilo serie. La cola no descarta muestras: un disco persistentemente más lento que la entrada aumentará la memoria utilizada.

El CSV sigue teniendo columnas fijas. El selector de señales, pausa/limpieza visual, columnas dinámicas y metadata pertenecen a las fases siguientes. Las señales adicionales ya se conservan en el buffer visual.

## Verificación

Desde `Python`, con el entorno virtual activado:

```sh
QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
```

Incluye 10 000 muestras sin GUI, pausa/reanudación, FINISH, HOME, FAULT, reinicio, error de disco y una integración con Qt real y puerto simulado. En hardware: HOME → START → STOP/PAUSE → START → STOP/PAUSE → FINISH; comprobar CSV, gráficas finales y cierre de la aplicación durante RUNNING.
