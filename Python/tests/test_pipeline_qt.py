import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import sys
import tempfile
import time
import unittest
from collections import deque
from pathlib import Path
from threading import Lock
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import QApplication
from serial_link import SerialWorker
from experiment_session import ExperimentSession
from gui_runtime import MainWindow


class FakeSerial:
    port='simulated'; baudrate=115200; is_open=False
    def __init__(self): self.lines=deque(); self.lock=Lock()
    def open(self): self.is_open=True
    def close(self): self.is_open=False
    def send_command(self, command): pass
    def read_line(self):
        with self.lock:
            return self.lines.popleft() if self.lines else None
    def add(self, *lines):
        with self.lock: self.lines.extend(lines)


class QtPipelineTests(unittest.TestCase):
    def test_real_threads_widgets_and_paused_finish(self):
        app=QApplication.instance() or QApplication([])
        app.setQuitOnLastWindowClosed(False)
        with tempfile.TemporaryDirectory() as tmp, patch('gui.plot_experiment') as plot:
            link=FakeSerial()
            worker=SerialWorker(link)
            worker.session=ExperimentSession(worker._session_event,tmp)
            thread=QThread(); worker.moveToThread(thread)
            window=MainWindow(worker)
            for signal, slot in (
                (worker.telemetry_received,window.handle_telemetry),
                (worker.message_received,window.handle_message),
                (worker.header_received,window.handle_header),
                (worker.event_received,window.handle_event),
                (worker.protocol_error,window.handle_protocol_error),
                (worker.esp_error_received,window.handle_esp_error),
                (worker.connection_changed,window.handle_connection_changed),
                (worker.experiment_started,window.handle_experiment_started),
                (worker.experiment_finished,window.handle_experiment_finished),
                (worker.experiment_message,window.handle_experiment_message),
                (worker.experiment_error,window.handle_serial_error),
            ): signal.connect(slot,Qt.ConnectionType.QueuedConnection)
            thread.started.connect(worker.start)
            window.shutdown_requested.connect(worker.stop)
            worker.finished.connect(thread.quit)
            header='HEADER,Time,theta,thetaDot,x,xDotObs,xDotXActual,u,state,mode,energy'
            link.add(header,'MSG,RUNNING',*[f'DATA,{i/100},0,0,0,0,0,0,3,1,12' for i in range(100)],'EVENT,BALANCEUP')
            thread.start()
            try:
                # No se procesan eventos de la GUI durante la adquisición.
                deadline=time.monotonic()+3
                while worker.session._logger.sample_count < 100 and time.monotonic()<deadline:
                    time.sleep(.01)
                self.assertEqual(worker.session._logger.sample_count,100)
                self.assertTrue(worker.session.active)
                for _ in range(20): app.processEvents(); time.sleep(.005)
                link.add('DATA,1.01,0,0,0,0,0,0,2,0,12')
                deadline=time.monotonic()+2
                while window.current_state != 2 and time.monotonic()<deadline:
                    app.processEvents();time.sleep(.005)
                self.assertTrue(window.finish_button.isEnabled())
                window._finish_clicked()
                deadline=time.monotonic()+2
                while (worker.session.active or not plot.called) and time.monotonic()<deadline:
                    app.processEvents();time.sleep(.005)
                self.assertFalse(worker.session.active)
                self.assertTrue(plot.called)
            finally:
                window.close()
                deadline=time.monotonic()+3
                while thread.isRunning() and time.monotonic()<deadline:
                    app.processEvents();time.sleep(.005)
                self.assertFalse(thread.isRunning())
                thread.wait()

if __name__=='__main__': unittest.main()
