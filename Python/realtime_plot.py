"""Visor posterior al experimento: descubre todas las columnas del CSV."""
import csv
from pathlib import Path

import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QDialog, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout,
)

_viewers = []
PALETTE = ('#0072BD', '#D95319', '#7E2F8E', '#77AC30', '#A2142F', '#4DBEEE', '#B58900')


def read_experiment(filename):
    """Admite data.csv nuevos y CSV antiguos con sus columnas originales."""
    path = Path(filename)
    if path.is_dir():
        path = path / 'data.csv'
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.reader(stream)
        names = next(reader, [])
        if not names or any(not name for name in names) or len(set(names)) != len(names):
            raise ValueError('CSV header is empty or contains duplicate names')
        data = {name: [] for name in names}
        for line_number, row in enumerate(reader, 2):
            if not row:
                continue
            if len(row) != len(names):
                raise ValueError(f'CSV row {line_number} has an unexpected column count')
            values = [float(value) for value in row]
            for name, value in zip(names, values):
                data[name].append(value)
    return path, data


class ExperimentViewer(QDialog):
    def __init__(self, path, data):
        super().__init__()
        self.path = path
        self.data = data
        self.time_signal = next((name for name in ('Time', 'time') if name in data), None)
        self.signal_names = [name for name in data if name != self.time_signal]
        self.setWindowTitle(f'Saved experiment — {path.parent.name}')
        self.setAttribute(Qt.WA_DeleteOnClose)
        layout = QVBoxLayout(self)
        filename_label = QLabel(str(path))
        filename_label.setWordWrap(True)
        filename_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(filename_label)
        count = len(next(iter(data.values())))
        layout.addWidget(QLabel(f'{count} saved samples. Select signals to plot:'))
        self.signals = QListWidget()
        defaults = {'theta', 'x', 'u'} & set(self.signal_names)
        if not defaults and self.signal_names:
            defaults.add(self.signal_names[0])
        for name in self.signal_names:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if name in defaults else Qt.Unchecked)
            self.signals.addItem(item)
        layout.addWidget(self.signals)
        self.open_button = QPushButton('Open selected plots')
        self.open_button.clicked.connect(self.open_selected)
        layout.addWidget(self.open_button)
        area = self.screen().availableGeometry()
        self.resize(min(640, area.width()-60), min(440, area.height()-80))

    def open_selected(self):
        count = len(next(iter(self.data.values())))
        times = self.data[self.time_signal] if self.time_signal else range(count)
        for index, name in enumerate(self.signal_names):
            if self.signals.item(index).checkState() != Qt.Checked:
                continue
            figure = plt.figure(num=f'{self.path.resolve()} — {name}', clear=True,
                                figsize=(8, 4.5), facecolor='white')
            axis = figure.add_subplot(111)
            color = {'theta':'#0072BD', 'x':'#D95319', 'u':'#7E2F8E'}.get(name, PALETTE[index % len(PALETTE)])
            if name in {'state', 'mode'}:
                axis.step(times, self.data[name], where='post', color=color, linewidth=1.5)
            else:
                axis.plot(times, self.data[name], color=color, linewidth=1.5)
            axis.set(title=name, xlabel='Time [s]' if self.time_signal else 'Sample', ylabel=name)
            axis.grid(True, alpha=.25)
            figure.tight_layout()
            area = self.screen().availableGeometry()
            figure.canvas.manager.window.resize(min(800, area.width()-60), min(450, area.height()-80))
            figure.show()


def plot_experiment(filename, block=False):
    try:
        path, data = read_experiment(filename)
    except Exception as exc:
        print(f'Error leyendo CSV: {exc}')
        return None
    if not next(iter(data.values())):
        print('No hay datos para graficar.')
        return None
    if QApplication.instance() is None:
        raise RuntimeError('The experiment viewer requires QApplication')
    viewer = ExperimentViewer(path, data)
    _viewers.append(viewer)
    viewer.finished.connect(lambda _result: _viewers.remove(viewer) if viewer in _viewers else None)
    if block:
        viewer.exec()
    else:
        viewer.show()
    return viewer


def close_all_plots():
    for viewer in list(_viewers):
        viewer.close()
    plt.close('all')
