import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import unittest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from gui_runtime import MainWindow
from serial_link import SerialWorker
from telemetry_parser import TelemetryParser
from test_pipeline_qt import FakeSerial


class SelectorTests(unittest.TestCase):
    def test_new_signals_repeated_header_and_schema_changes(self):
        app=QApplication.instance() or QApplication([])
        app.setQuitOnLastWindowClosed(False)
        worker=SerialWorker(FakeSerial())
        window=MainWindow(worker)
        parser=TelemetryParser()
        try:
            self.assertFalse(window.open_signals_button.isEnabled())
            _, header=parser.parse('HEADER,Time,theta,x,u,state,mode,energy,uNN')
            window.handle_header(header)
            self.assertNotIn('Time',window.signal_items)
            self.assertEqual(set(window.signal_items),set(header)-{'Time'})
            self.assertEqual(window.plot_windows,{})
            # Solo energy y uNN: no se configuran en el código de la GUI.
            for name,item in window.signal_items.items():
                item.setCheckState(Qt.Checked if name in ('energy','uNN') else Qt.Unchecked)
            for line in ('DATA,1,0,0,0,3,1,12,4','DATA,2,0,0,0,3,1,13,5'):
                _, data=parser.parse(line);worker.session.buffer.append(data)
            window._open_selected_plots();app.processEvents()
            self.assertEqual(set(window.plot_windows),{'energy','uNN'})
            self.assertEqual(list(window.plot_series['energy'][1].getData()[1]),[12,13])
            self.assertEqual(list(window.plot_series['uNN'][1].getData()[1]),[4,5])
            dialog=window.plot_windows['energy']
            window.handle_header(header)
            self.assertIs(window.plot_windows['energy'],dialog)
            self.assertEqual(window.signal_items['theta'].checkState(),Qt.Unchecked)
            window.signal_items['energy'].setCheckState(Qt.Unchecked)
            self.assertFalse(dialog.isVisible())
            self.assertEqual(worker.session.buffer.snapshot(('energy',))['energy'],[12,13])
            window.handle_header(['Time','uNN','energyError'])
            self.assertNotIn('energy',window.plot_windows)
            self.assertIn('energyError',window.signal_items)
            self.assertEqual(window.signal_items['uNN'].checkState(),Qt.Checked)
        finally:
            window.close();window.deleteLater();app.processEvents()

if __name__=='__main__': unittest.main()
