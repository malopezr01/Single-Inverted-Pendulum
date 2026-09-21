"""Gestiona el CSV en un hilo propio. La GUI nunca abre ni escribe archivos.

La cola conserva todas las muestras recibidas; el buffer visual es independiente.
El cierre drena la cola antes de cerrar el CSV y terminar el hilo.
"""
from queue import Queue
from threading import Lock, Thread

from experiment_logger import ExperimentLogger
from telemetry_buffer import TelemetryBuffer


class ExperimentSession:
    INIT, HOMING, READY, RUNNING, FAULT = range(5)

    def __init__(self, notify, experiments_dir='experiments', logger=None):
        self.buffer = TelemetryBuffer()
        self._notify = notify
        self._logger = logger if logger is not None else ExperimentLogger(experiments_dir)
        self._queue = Queue()
        self._lock = Lock()
        self._active = False
        self._closed = False
        self._thread = None
        self._state = None
        self._fault = False
        self._logging_failed = False
        self._finish_requested = False

    @property
    def active(self):
        with self._lock:
            return self._active

    def start(self):
        self._thread = Thread(target=self._run, name='experiment-writer', daemon=False)
        self._thread.start()

    def submit(self, kind, payload):
        with self._lock:
            if not self._closed:
                self._queue.put((kind, dict(payload) if kind == 'data' else payload))

    def finish(self, reason):
        self.submit('finish', reason)

    def finish_when_ready(self):
        self.submit("finish_when_ready", None)

    def close(self):
        with self._lock:
            if not self._closed:
                self._closed = True
                self._queue.put(('shutdown', None))
        if self._thread is not None:
            self._thread.join()

    def _set_active(self, value):
        with self._lock:
            self._active = value

    def _finish(self, reason):
        self._finish_requested = False
        if not self._logger.active:
            return
        try:
            filename, samples = self._logger.stop()
        finally:
            self._set_active(False)
        self._notify('finished', filename or '', samples, reason)

    def _process(self, kind, payload):
        if kind == 'finish_when_ready':
            if self._state == self.RUNNING:
                self._finish_requested = True
            else:
                self._finish('Finished by user')
        elif kind == 'finish':
            self._finish(payload)
        elif kind == 'command':
            if payload == 'X':
                self._fault = True
                self._finish('EMERGENCY STOP')
            elif payload == 'H':
                self._finish('Experiment closed before homing')
        elif kind == 'message' and payload == 'INIT - Waiting for HOME command':
            self._finish('ESP32 restarted')
            self._fault = False
            self._logging_failed = False
            self._state = self.INIT
        elif kind == 'error' and 'EMERGENCY STOP' in payload.upper():
            self._fault = True
            self._finish('EMERGENCY STOP')
        elif kind == 'data':
            state = payload['state']
            if state == self.FAULT:
                self._fault = True
                self._finish('FAULT')
            if self._fault:
                return
            if state == self.RUNNING:
                if not self._logger.active and not self._logging_failed:
                    filename = self._logger.start()
                    self.buffer.clear()
                    self._set_active(True)
                    self._notify('started', filename)
                elif self._state != self.RUNNING and self._logger.active:
                    self._notify('message', 'Experiment resumed.')
                if self._logger.active:
                    self._logger.write(payload)
                self.buffer.append(payload)
            elif state == self.READY and self._state == self.RUNNING and self._logger.active:
                self._notify('message', 'Experiment paused.')
            self._state = state
            if state == self.READY and self._finish_requested:
                self._finish("Finished by user")

    def _run(self):
        while True:
            kind, payload = self._queue.get()
            try:
                if kind == 'shutdown':
                    self._finish('Experiment saved on exit')
                    return
                self._process(kind, payload)
            except Exception as exc:
                # Un fallo de disco no debe matar la adquisición ni pasar inadvertido.
                self._logging_failed = True
                self._notify('error', f'Experiment logging failed: {exc}')
                try:
                    self._finish('Logging stopped after error')
                except Exception as close_exc:
                    self._notify('error', f'Could not close CSV: {close_exc}')
                if kind == 'shutdown':
                    return
            finally:
                self._queue.task_done()
