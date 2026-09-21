import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import unittest
from unittest.mock import Mock, patch
from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication
from gui_runtime import MainWindow
from serial_link import SerialWorker
from test_pipeline_qt import FakeSerial


class PlotWindowTests(unittest.TestCase):
    def test_laptop_geometry_and_popup_lifecycle(self):
        app=QApplication.instance() or QApplication([])
        app.setQuitOnLastWindowClosed(False)
        worker=SerialWorker(FakeSerial())
        window=MainWindow(worker)
        try:
            screen=Mock()
            screen.availableGeometry.return_value=QRect(0,0,1024,600)
            with patch.object(window,'screen',return_value=screen):
                window._fit_to_screen(window,980,610)
            window.show();app.processEvents()
            self.assertLessEqual(window.width(),964)
            self.assertLessEqual(window.height(),520)
            for button in (window.home_button,window.start_button,window.stop_button,
                           window.finish_button,window.estop_button):
                self.assertTrue(button.isVisible())
                self.assertLess(button.mapTo(window,button.rect().bottomRight()).y(),window.height())
            worker.session.buffer.append(dict(Time=1,theta=.1,x=.2,u=3))
            window._open_plot('theta');app.processEvents()
            popup=window.plot_windows['theta']
            self.assertTrue(popup.isVisible())
            self.assertFalse(popup.isModal())
            self.assertEqual(window.theta_curve.opts['pen'].color().name(),'#0072bd')
            popup.close()
            worker.session.buffer.append(dict(Time=2,theta=.2,x=.3,u=4))
            window._update_plots()
            window._open_plot('theta');app.processEvents()
            self.assertIs(popup,window.plot_windows['theta'])
            self.assertEqual(list(window.theta_curve.getData()[0]),[1,2])
            self.assertTrue(window.plot_timer.isActive())
            window.close();app.processEvents()
            self.assertFalse(popup.isVisible())
        finally:
            window.close();window.deleteLater();app.processEvents()
