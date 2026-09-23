import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import tempfile
import unittest
from pathlib import Path

from gui import ControlMode, MainWindow
from realtime_plot import read_experiment
from telemetry_parser import TelemetryParser


class ControlModeCompatibilityTests(unittest.TestCase):
    def test_current_and_previous_firmware_labels(self):
        self.assertEqual(int(ControlMode.SWING_UP), 2)
        for mode, label in [(0, 'NONE'), (1, 'LQR'), (2, 'SWING_UP'),
                            (3, 'SWING_UP'), (99, 'UNKNOWN (99)')]:
            with self.subTest(mode=mode):
                self.assertEqual(MainWindow._mode_name(mode), label)

    def test_telemetry_preserves_original_mode(self):
        parser = TelemetryParser()
        parser.parse('HEADER,Time,state,mode')
        for mode in (2, 3):
            with self.subTest(mode=mode):
                kind, data = parser.parse(f'DATA,0.01,3,{mode}')
                self.assertEqual(kind, 'data')
                self.assertEqual(data['mode'], mode)
                self.assertEqual(MainWindow._mode_name(data['mode']), 'SWING_UP')

    def test_saved_modes_are_not_reinterpreted_or_rewritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'data.csv'
            original = 'Time,state,mode\n0,3,2\n0.01,3,3\n'
            path.write_text(original)
            _, data = read_experiment(path)
            self.assertEqual(data['mode'], [2, 3])
            self.assertEqual(path.read_text(), original)


if __name__ == '__main__':
    unittest.main()
