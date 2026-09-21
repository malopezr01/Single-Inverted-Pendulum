import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import tempfile
import unittest
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from realtime_plot import read_experiment, plot_experiment, close_all_plots, plt


class SavedViewerTests(unittest.TestCase):
    def test_dynamic_and_legacy_csv(self):
        app=QApplication.instance() or QApplication([])
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'data.csv'
            path.write_text('Time,energy,uNN,state\n0,12,4,3\n0.01,13,5,3\n')
            _,data=read_experiment(tmp)
            self.assertEqual(data['energy'],[12,13])
            viewer=plot_experiment(path)
            try:
                for i in range(viewer.signals.count()):
                    viewer.signals.item(i).setCheckState(Qt.Checked)
                viewer.open_selected();app.processEvents()
                self.assertEqual(len(plt.get_fignums()),3)
                plotted={plt.figure(n).axes[0].get_title():list(plt.figure(n).axes[0].lines[0].get_ydata()) for n in plt.get_fignums()}
                self.assertEqual(plotted['uNN'],[4,5])
            finally:close_all_plots();app.processEvents()
            legacy=Path(tmp)/'experiment_old.csv'
            legacy.write_text('Time,theta,x,u\n0,1,2,3\n')
            self.assertEqual(list(read_experiment(legacy)[1]),['Time','theta','x','u'])
            legacy.write_text('Time,theta\n0\n')
            with self.assertRaises(ValueError):read_experiment(legacy)

if __name__=='__main__':unittest.main()
