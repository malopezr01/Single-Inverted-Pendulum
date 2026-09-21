import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sys
import math
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtWidgets import QApplication
from telemetry_buffer import TelemetryBuffer
from serial_link import SerialWorker
from gui_runtime import MainWindow
from test_pipeline_qt import FakeSerial


class BufferTests(unittest.TestCase):
    def test_dynamic_signals_window_and_snapshot_revision(self):
        b=TelemetryBuffer(window_seconds=10)
        for i in range(10001):
            b.append({'Time':i/500, 'energy':i, 'uNN':i*2})
        revision, values=b.snapshot_if_changed(('Time','energy','uNN'))
        self.assertEqual(len(values['Time']),5001)
        self.assertEqual(values['Time'][0],10)
        self.assertEqual(values['uNN'][-1],20000)
        self.assertIsNone(b.snapshot_if_changed(('Time',),revision))
        b.window_seconds=2
        self.assertEqual(len(b.snapshot(('Time',))['Time']),1001)
        b.clear()
        self.assertEqual(b.snapshot(('energy',))['energy'],[])

    def test_capacity_missing_signal_and_invalid_time(self):
        b=TelemetryBuffer(max_samples=3)
        for i in range(5): b.append({'Time':1, 'theta':i})
        b.append({'Time':float('nan')})
        data=b.snapshot(('theta','energy'))
        self.assertEqual(data['theta'],[2,3,4])
        self.assertTrue(all(math.isnan(v) for v in data['energy']))
        for width in (0,-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError): b.window_seconds=width


class PlotTests(unittest.TestCase):
    def test_qt_window_range_and_no_redundant_redraw(self):
        app=QApplication.instance() or QApplication([])
        app.setQuitOnLastWindowClosed(False)
        worker=SerialWorker(FakeSerial())
        window=MainWindow(worker)
        try:
            self.assertEqual(window.plot_timer.interval(),40)
            for i in range(2001):
                worker.session.buffer.append(dict(Time=i/100,theta=i,x=i*2,u=i*3,energy=4))
            window._update_plots()
            x,y=window.theta_curve.getData()
            self.assertEqual(len(x),1001)
            self.assertEqual(y[-1],2000)
            self.assertAlmostEqual(window.theta_plot.viewRange()[0][0],10)
            with patch.object(window.theta_curve,'setData') as redraw:
                window._update_plots()
                redraw.assert_not_called()
            window.plot_window_spin.setValue(2)
            x,y=window.theta_curve.getData()
            self.assertEqual(len(x),201)
            self.assertAlmostEqual(window.theta_plot.viewRange()[0][0],18)
            self.assertAlmostEqual(window.theta_plot.viewRange()[0][1],20)
            worker.session.buffer.clear()
            window._update_plots()
            self.assertIsNone(window.theta_curve.getData()[0])
        finally:
            window.close()
            window.deleteLater()
            app.processEvents()

if __name__=='__main__': unittest.main()
