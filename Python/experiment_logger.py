"""CSV dinámico y metadatos; usado únicamente por el hilo de registro."""
import csv
import json
import math
import os
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4


class ExperimentLogger:
    def __init__(self, experiments_dir='experiments', port=None, baudrate=None):
        self.experiments_dir = Path(experiments_dir)
        self.port = port
        self.baudrate = baudrate
        self.csv_file = None
        self.writer = None
        self.filename = None
        self.sample_count = 0
        self.active = False
        self.signals = ()
        self.metadata = {}

    def start(self, signals):
        if self.active:
            return self.filename
        signals = tuple(signals)
        if not signals or len(set(signals)) != len(signals) or any(not s for s in signals):
            raise ValueError('Invalid experiment signal schema')
        now = datetime.now().astimezone()
        folder = self.experiments_dir / (
            f'experiment_{now:%Y-%m-%d_%H-%M-%S_%f}_{uuid4().hex[:8]}'
        )
        folder.mkdir(parents=True, exist_ok=False)
        self.filename = str(folder / 'data.csv')
        self._metadata_path = folder / 'metadata.json'
        self.signals = signals
        self.sample_count = 0
        self._started_monotonic = time.monotonic()
        self._previous_time = None
        self._sample_span = 0.0
        self._interval_count = 0
        self._time_signal = next((s for s in ('Time', 'time') if s in signals), None)
        self.metadata = {
            'format_version': 1,
            'status': 'recording',
            'started_at': now.isoformat(),
            'finished_at': None,
            'port': self.port,
            'baudrate': self.baudrate,
            'signals': list(signals),
            'sample_count': 0,
            'duration_seconds': 0.0,
            'active_sample_span_seconds': 0.0,
            'estimated_acquisition_hz': None,
            'frequency_basis': 'positive telemetry time intervals within RUNNING segments',
            'time_signal': self._time_signal,
            'first_sample_time': None,
            'last_sample_time': None,
            'logging_policy': 'RUNNING samples only; READY pauses keep the file open',
            'stop_reason': None,
        }
        self.csv_file = open(self.filename, 'x', encoding='utf-8', newline='', buffering=8192)
        self.writer = csv.writer(self.csv_file)
        try:
            self.writer.writerow(signals)
            self.csv_file.flush()
            self._save_metadata()
        except Exception:
            self.csv_file.close()
            self.csv_file = None
            self.writer = None
            raise
        self.active = True
        return self.filename

    def pause(self):
        # No incluir en la estimación de frecuencia el salto entre dos tramos.
        self._previous_time = None

    def write(self, data):
        if not self.active:
            return
        if set(data) != set(self.signals):
            raise ValueError('DATA schema differs from the active CSV HEADER')
        self.writer.writerow([data[name] for name in self.signals])
        self.sample_count += 1
        value = data.get(self._time_signal)
        if isinstance(value, (int, float)) and math.isfinite(value):
            if self.metadata['first_sample_time'] is None:
                self.metadata['first_sample_time'] = value
            self.metadata['last_sample_time'] = value
            if self._previous_time is not None and value > self._previous_time:
                self._sample_span += value - self._previous_time
                self._interval_count += 1
            self._previous_time = value
        else:
            self._previous_time = None
        if self.sample_count % 50 == 0:
            self.csv_file.flush()
            self._save_metadata()

    def _save_metadata(self):
        self.metadata.update(
            sample_count=self.sample_count,
            duration_seconds=max(0.0, time.monotonic() - self._started_monotonic),
            active_sample_span_seconds=self._sample_span,
            estimated_acquisition_hz=(self._interval_count / self._sample_span
                                      if self._sample_span > 0 else None),
        )
        temporary = self._metadata_path.with_suffix('.json.tmp')
        with temporary.open('w', encoding='utf-8') as stream:
            json.dump(self.metadata, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.write('\n')
        os.replace(temporary, self._metadata_path)

    def stop(self, reason='Finished by user'):
        if not self.active:
            return self.filename, self.sample_count
        try:
            try:
                self.csv_file.flush()
            finally:
                self.csv_file.close()
        except Exception:
            self.metadata['status'] = 'error'
            self.metadata['stop_reason'] = reason
            # No marcar como completado si no se pudo cerrar correctamente.
            raise
        else:
            self.metadata.update(
                status='error' if reason == 'Logging stopped after error' else 'completed',
                finished_at=datetime.now().astimezone().isoformat(),
                stop_reason=reason,
            )
            self._save_metadata()
        finally:
            self.csv_file = None
            self.writer = None
            self.active = False
        return self.filename, self.sample_count
