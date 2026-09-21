"""Buffer visual independiente del registro, con copias protegidas entre hilos."""
from collections import deque
from threading import Lock


class TelemetryBuffer:
    def __init__(self, window_seconds=15.0, max_samples=20000):
        self.window_seconds = window_seconds
        self._samples = deque(maxlen=max_samples)
        self._lock = Lock()

    def clear(self):
        with self._lock:
            self._samples.clear()

    def append(self, data):
        sample = dict(data)
        now = sample['Time']
        with self._lock:
            if self._samples and now < self._samples[-1]['Time']:
                self._samples.clear()
            self._samples.append(sample)
            while self._samples and self._samples[0]['Time'] < now - self.window_seconds:
                self._samples.popleft()

    def snapshot(self, signals):
        with self._lock:
            return {name: [sample.get(name, float('nan')) for sample in self._samples]
                    for name in signals}
