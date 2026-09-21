import csv
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiment_session import ExperimentSession
from telemetry_buffer import TelemetryBuffer


def sample(t=0, state=3):
    return dict(Time=t, theta=0, thetaDot=0, x=0, xDotObs=0,
                xDotXActual=0, u=0, state=state, mode=1, energy=12)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.events = []
        self.session = ExperimentSession(lambda *event: self.events.append(event), self.tmp.name)
        self.session.start()

    def tearDown(self):
        self.session.close()
        self.tmp.cleanup()

    def drain(self):
        self.session._queue.join()

    def test_logging_without_gui_and_bounded_visual_history(self):
        self.session.submit('message', 'RUNNING')
        for i in range(10000):
            self.session.submit('data', sample(i / 100))
        self.session.close()
        files = list(Path(self.tmp.name).glob('*.csv'))
        with files[0].open() as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(len(rows), 10000)
        visual = self.session.buffer.snapshot(('Time', 'energy'))
        self.assertLess(len(visual['Time']), 1600)
        self.assertEqual(visual['energy'][-1], 12)

    def test_pause_resume_and_finish_while_running(self):
        for state in (3, 2, 2, 3):
            self.session.submit('data', sample(state=state))
        self.drain()
        self.assertTrue(self.session.active)
        self.assertEqual(len([e for e in self.events if e[0]=='started']), 1)
        self.session.finish_when_ready()
        self.session.submit('data', sample(state=3))
        self.session.submit('data', sample(state=2))
        self.drain()
        self.assertFalse(self.session.active)
        end = next(e for e in self.events if e[0]=='finished')
        self.assertEqual(end[2], 3)

    def test_fault_stale_running_and_reset(self):
        self.session.submit('data', sample())
        self.session.submit('command', 'X')
        self.session.submit('data', sample())
        self.drain()
        self.assertFalse(self.session.active)
        self.session.submit('message', 'INIT - Waiting for HOME command')
        self.session.submit('data', sample())
        self.drain()
        self.assertTrue(self.session.active)
        self.assertEqual(len(list(Path(self.tmp.name).glob('*.csv'))), 2)

    def test_home_and_finish_paused(self):
        self.session.submit('data', sample())
        self.session.submit('data', sample(state=2))
        self.session.submit('command', 'H')
        self.drain()
        self.assertFalse(self.session.active)
        self.session.submit('data', sample())
        self.session.submit('data', sample(state=2))
        self.session.finish_when_ready()
        self.drain()
        self.assertFalse(self.session.active)

    def test_disk_error_reported_and_thread_survives(self):
        def fail(data):
            raise OSError('disk full')
        self.session._logger.write = fail
        self.session.submit('data', sample())
        self.drain()
        self.assertTrue(any(e[0]=='error' and 'disk full' in e[1] for e in self.events))
        self.assertFalse(self.session.active)
        self.assertTrue(self.session._thread.is_alive())

    def test_buffer_snapshot_independent_and_reset_time(self):
        b=TelemetryBuffer(max_samples=2)
        data=sample(10)
        b.append(data)
        data['theta']=999
        self.assertEqual(b.snapshot(('theta',))['theta'], [0])
        b.append(sample(1))
        self.assertEqual(b.snapshot(('Time',))['Time'], [1])


if __name__ == '__main__':
    unittest.main()
