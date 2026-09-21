"""Historial visual acotado; independiente del CSV y seguro entre hilos."""
from collections import deque
from math import isfinite
from threading import Lock


class TelemetryBuffer:
    def __init__(self, window_seconds=10.0, max_samples=20000):
        if max_samples <= 0:
            raise ValueError('max_samples must be positive')
        self._samples = deque(maxlen=max_samples)
        self._lock = Lock()
        self._revision = 0
        self.window_seconds = window_seconds

    @property
    def window_seconds(self):
        with self._lock:
            return self._window_seconds

    @window_seconds.setter
    def window_seconds(self, seconds):
        seconds = float(seconds)
        if not isfinite(seconds) or seconds <= 0:
            raise ValueError('window_seconds must be finite and positive')
        with self._lock:
            self._window_seconds = seconds
            self._trim()
            self._revision += 1

    def _trim(self):
        if self._samples:
            cutoff = self._samples[-1]['Time'] - self._window_seconds
            while self._samples and self._samples[0]['Time'] < cutoff:
                self._samples.popleft()

    def clear(self):
        with self._lock:
            self._samples.clear()
            self._revision += 1

    def append(self, data):
        sample = dict(data)
        now = sample['Time']
        if not isfinite(now):
            return
        with self._lock:
            if self._samples and now < self._samples[-1]['Time']:
                self._samples.clear()
            self._samples.append(sample)
            self._trim()
            self._revision += 1

    def snapshot_if_changed(self, signals, revision=None):
        """Copia referencias bajo bloqueo; construye las series fuera del bloqueo."""
        with self._lock:
            if revision == self._revision:
                return None
            current_revision = self._revision
            samples = tuple(self._samples)
        # Las muestras internas nunca se modifican después de append().
        values = {name: [sample.get(name, float('nan')) for sample in samples]
                  for name in signals}
        return current_revision, values

    def snapshot(self, signals):
        return self.snapshot_if_changed(signals)[1]
