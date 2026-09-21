from enum import IntEnum

import pyqtgraph as pg

from PySide6.QtCore import (
    QTime,
    QTimer,
    Qt,
    Signal,
    Slot,
)

from PySide6.QtGui import QFont

from PySide6.QtWidgets import (
    QFrame,
    QDialog,
    QScrollArea,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


from realtime_plot import (
    close_all_plots,
    plot_experiment,
)


class SystemState(IntEnum):

    INIT = 0
    HOMING = 1
    READY = 2
    RUNNING = 3
    FAULT = 4


class ControlMode(IntEnum):

    NONE = 0
    LQR = 1
    LQR_FRICTION = 2
    SWING_UP = 3


class MainWindow(QMainWindow):

    # =============================================
    # Shutdown request
    #
    # bool:
    #
    # True  -> mandar S antes de cerrar Serial
    # False -> cerrar Serial directamente
    #
    # Esta señal es la clave para no llamar
    # SerialWorker.stop() desde el GUI thread.
    # =============================================

    shutdown_requested = Signal(
        bool
    )

    PLOT_WINDOW_SECONDS = 10.0
    PLOT_REFRESH_MS = 40  # 25 Hz; independiente del registro y del puerto serie.

    def __init__(
        self,
        serial_worker,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.serial_worker = (
            serial_worker
        )

        self.session = serial_worker.session
        self.visual_buffer = self.session.buffer
        self.visual_buffer.window_seconds = self.PLOT_WINDOW_SECONDS
        self._plot_revision = None

        self.connected = False

        self.current_state = None

        self.current_mode = None

        self.start_pending = False

        self.finish_pending = False

        self.shutdown_started = False

        # =============================================
        # Buffers
        # =============================================

        # =============================================
        # Window
        # =============================================

        self.setWindowTitle(
            "Inverted Pendulum Control"
        )

        self._build_ui()
        self._fit_to_screen(self, 980, 610)

        # =============================================
        # Plot refresh
        # =============================================

        self.plot_timer = QTimer(
            self
        )

        self.plot_timer.timeout.connect(
            self._update_plots
        )

        self.plot_timer.start(self.PLOT_REFRESH_MS)

        self._update_buttons()

    # =================================================
    # UI
    # =================================================

    def _build_ui(self):

        central_widget = QWidget()

        central_widget.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(8, 8, 8, 8)
        self.setCentralWidget(root)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(central_widget)
        root_layout.addWidget(scroll, 1)

        main_layout = QVBoxLayout(
            central_widget
        )

        main_layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        main_layout.setSpacing(
            6
        )

        # =============================================
        # Header
        # =============================================

        header_layout = QHBoxLayout()

        title_label = QLabel(
            "INVERTED PENDULUM CONTROL"
        )

        title_font = QFont()

        title_font.setPointSize(
            15
        )

        title_font.setBold(
            True
        )

        title_label.setFont(
            title_font
        )

        header_layout.addWidget(
            title_label
        )

        header_layout.addStretch()

        main_layout.addLayout(
            header_layout
        )

        # =============================================
        # System status
        # =============================================

        status_group = QGroupBox(
            "System status"
        )

        status_group.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        status_layout = QGridLayout(
            status_group
        )

        status_layout.setContentsMargins(
            8,
            6,
            8,
            6,
        )

        status_layout.addWidget(
            QLabel(
                "Connection"
            ),
            0,
            0,
        )

        self.connection_label = QLabel(
            "DISCONNECTED"
        )

        self.connection_label.setFont(
            self._bold_font()
        )

        status_layout.addWidget(
            self.connection_label,
            0,
            1,
        )

        status_layout.addWidget(
            QLabel(
                "SystemState"
            ),
            0,
            2,
        )

        self.state_label = QLabel(
            "---"
        )

        self.state_label.setFont(
            self._bold_font()
        )

        status_layout.addWidget(
            self.state_label,
            0,
            3,
        )

        status_layout.addWidget(
            QLabel(
                "ControlMode"
            ),
            0,
            4,
        )

        self.mode_label = QLabel(
            "---"
        )

        self.mode_label.setFont(
            self._bold_font()
        )

        status_layout.addWidget(
            self.mode_label,
            0,
            5,
        )

        status_layout.setColumnStretch(
            1,
            1,
        )

        status_layout.setColumnStretch(
            3,
            1,
        )

        status_layout.setColumnStretch(
            5,
            1,
        )

        main_layout.addWidget(
            status_group
        )

        # =============================================
        # Telemetry
        # =============================================

        values_group = QGroupBox(
            "Real-time telemetry"
        )

        values_group.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        values_layout = QGridLayout(
            values_group
        )

        values_layout.setContentsMargins(
            8,
            6,
            8,
            6,
        )

        self.value_labels = {}

        telemetry_fields = [
            (
                "Time",
                "Time",
                "s",
            ),
            (
                "theta",
                "theta",
                "rad",
            ),
            (
                "thetaDot",
                "thetaDot",
                "rad/s",
            ),
            (
                "x",
                "x",
                "m",
            ),
            (
                "xDotObs",
                "xDotObs",
                "m/s",
            ),
            (
                "xDotXActual",
                "xDotXActual",
                "m/s",
            ),
            (
                "u",
                "u",
                "m/s²",
            ),
        ]

        for index, (
            key,
            display_name,
            unit,
        ) in enumerate(
            telemetry_fields
        ):

            row = index // 2

            column = (
                index % 2
            ) * 3

            name_label = QLabel(
                display_name
            )

            value_label = QLabel(
                "0.0000"
            )

            value_label.setFont(
                self._value_font()
            )

            unit_label = QLabel(
                unit
            )

            values_layout.addWidget(
                name_label,
                row,
                column,
            )

            values_layout.addWidget(
                value_label,
                row,
                column + 1,
            )

            values_layout.addWidget(
                unit_label,
                row,
                column + 2,
            )

            self.value_labels[
                key
            ] = value_label

        values_layout.setColumnStretch(
            1,
            1,
        )

        values_layout.setColumnStretch(
            4,
            1,
        )

        main_layout.addWidget(
            values_group
        )

        # =============================================
        # Real-time plots
        # =============================================

        plots_group = QGroupBox("Real-time plots")

        plots_group.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding,
        )

        plots_layout = QVBoxLayout(
            plots_group
        )

        plots_layout.setContentsMargins(
            4,
            4,
            4,
            4,
        )

        window_controls = QHBoxLayout()
        window_controls.addWidget(QLabel("Visible window (s):"))
        self.plot_window_spin = QDoubleSpinBox()
        self.plot_window_spin.setRange(1.0, 30.0)
        self.plot_window_spin.setDecimals(1)
        self.plot_window_spin.setValue(self.PLOT_WINDOW_SECONDS)
        self.plot_window_spin.setToolTip(
            "Active time. Increasing the window fills it with new samples."
        )
        self.plot_window_spin.valueChanged.connect(self._set_plot_window)
        window_controls.addWidget(self.plot_window_spin)
        window_controls.addStretch()
        plots_layout.addLayout(window_controls)

        self.plot_windows = {}
        self.plot_series = {}
        plot_buttons = QHBoxLayout()
        specs = (
            ("theta", "Pendulum angle", "theta [rad]", "#0072BD"),
            ("x", "Cart position", "x [m]", "#D95319"),
            ("u", "Control acceleration", "u [m/s²]", "#7E2F8E"),
        )
        for name, title, label, color in specs:
            dialog = QDialog(self, Qt.Window)
            dialog.setWindowTitle(title)
            dialog.setModal(False)
            layout = QVBoxLayout(dialog)
            plot = self._create_plot(title, label)
            curve = plot.plot(pen=pg.mkPen(color, width=2), antialias=True)
            plot.setXRange(0, self.PLOT_WINDOW_SECONDS, padding=0)
            layout.addWidget(plot)
            self.plot_windows[name] = dialog
            self.plot_series[name] = (plot, curve)
            # Mantener los nombres actuales para los controles y las pruebas.
            setattr(self, f"{name}_plot", plot)
            setattr(self, f"{name}_curve", curve)
            button = QPushButton(f"Open {name} plot")
            button.setStyleSheet(f"color: {color}; font-weight: bold; padding: 8px;")
            button.clicked.connect(lambda checked=False, signal=name: self._open_plot(signal))
            plot_buttons.addWidget(button)
        plots_layout.addLayout(plot_buttons)
        plots_layout.addWidget(QLabel("Each plot opens in its own window. Closing it keeps recording active."))
        main_layout.addWidget(plots_group)

        # =============================================
        # Console
        # =============================================

        console_group = QGroupBox(
            "ESP32 / Application log"
        )

        console_group.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        console_layout = QVBoxLayout(
            console_group
        )

        self.console = QTextEdit()

        self.console.setReadOnly(
            True
        )

        self.console.setMinimumHeight(
            60
        )

        self.console.setMaximumHeight(
            100
        )

        console_layout.addWidget(
            self.console
        )

        main_layout.addWidget(
            console_group
        )

        # =============================================
        # Buttons
        # =============================================

        control_frame = QFrame()

        control_layout = QGridLayout(control_frame)

        control_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        self.start_button = QPushButton(
            "START / RESUME"
        )

        self.stop_button = QPushButton(
            "STOP / PAUSE"
        )

        self.finish_button = QPushButton(
            "FINISH EXPERIMENT"
        )

        self.estop_button = QPushButton(
            "EMERGENCY STOP"
        )

        button_font = QFont()

        button_font.setPointSize(
            12
        )

        button_font.setBold(
            True
        )

        for button in [
            self.start_button,
            self.stop_button,
            self.finish_button,
            self.estop_button,
        ]:

            button.setMinimumHeight(
                45
            )

            button.setMaximumHeight(
                50
            )

            button.setFont(
                button_font
            )

            button.setSizePolicy(
                QSizePolicy.Expanding,
                QSizePolicy.Fixed,
            )

        self.start_button.setStyleSheet(
            """
            QPushButton {
                background-color: #2e8b57;
                color: white;
                border-radius: 6px;
                padding: 8px;
            }

            QPushButton:disabled {
                background-color: #555555;
                color: #999999;
            }
            """
        )

        self.stop_button.setStyleSheet(
            """
            QPushButton {
                background-color: #c08020;
                color: white;
                border-radius: 6px;
                padding: 8px;
            }

            QPushButton:disabled {
                background-color: #555555;
                color: #999999;
            }
            """
        )

        self.finish_button.setStyleSheet(
            """
            QPushButton {
                background-color: #4f5b66;
                color: white;
                border-radius: 6px;
                padding: 8px;
            }

            QPushButton:disabled {
                background-color: #555555;
                color: #999999;
            }
            """
        )

        self.estop_button.setStyleSheet(
            """
            QPushButton {
                background-color: #c62828;
                color: white;
                border-radius: 6px;
                padding: 8px;
            }

            QPushButton:disabled {
                background-color: #555555;
                color: #999999;
            }
            """
        )

        self.start_button.clicked.connect(
            self._start_clicked
        )

        self.stop_button.clicked.connect(
            self._stop_clicked
        )

        self.finish_button.clicked.connect(
            self._finish_clicked
        )

        self.estop_button.clicked.connect(
            self._estop_clicked
        )

        control_layout.addWidget(self.start_button, 0, 1)
        control_layout.addWidget(self.stop_button, 0, 2)
        control_layout.addWidget(self.finish_button, 1, 0, 1, 2)
        control_layout.addWidget(self.estop_button, 1, 2)
        for column in range(3):
            control_layout.setColumnStretch(column, 1)
        root_layout.addWidget(control_frame)

    # =================================================
    # Helpers
    # =================================================

    @staticmethod
    def _bold_font():

        font = QFont()

        font.setBold(
            True
        )

        return font

    @staticmethod
    def _value_font():

        font = QFont()

        font.setFamily(
            "monospace"
        )

        font.setPointSize(
            10
        )

        font.setBold(
            True
        )

        return font

    @staticmethod
    def _create_plot(
        title,
        y_label,
    ):

        plot = pg.PlotWidget(background="white")
        for axis_name in ("left", "bottom"):
            axis = plot.getAxis(axis_name)
            axis.setPen(pg.mkPen("#555555"))
            axis.setTextPen(pg.mkPen("#333333"))

        plot.setTitle(title, color="#222222", size="12pt")

        plot.setLabel(
            "left",
            y_label,
        )

        plot.setLabel(
            "bottom",
            "Time [s]",
        )

        plot.showGrid(
            x=True,
            y=True,
            alpha=0.25,
        )

        plot.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Ignored,
        )

        plot.setMinimumHeight(
            120
        )

        return plot

    # =================================================
    # Console
    # =================================================

    def _append_console(
        self,
        source,
        text,
    ):

        if self.shutdown_started:
            return

        timestamp = (
            QTime
            .currentTime()
            .toString(
                "HH:mm:ss.zzz"
            )
        )

        self.console.append(
            (
                f"[{timestamp}] "
                f"[{source}] "
                f"{text}"
            )
        )

    # =================================================
    # Connection
    # =================================================

    @Slot(bool, str)
    def handle_connection_changed(
        self,
        connected,
        description,
    ):

        self.connected = (
            connected
        )

        if self.shutdown_started:
            return

        if connected:

            self.connection_label.setText(
                "CONNECTED"
            )

            self.connection_label.setStyleSheet(
                "color: #2e8b57;"
            )

        else:

            self.connection_label.setText(
                "DISCONNECTED"
            )

            self.connection_label.setStyleSheet(
                "color: #c62828;"
            )

        self._append_console(
            "PC",
            description,
        )

        self._update_buttons()

    @Slot(str)
    def handle_serial_error(
        self,
        message,
    ):

        self._append_console(
            "ERROR",
            message,
        )

    @Slot(str)
    def handle_message(
        self,
        message,
    ):

        self._append_console(
            "ESP32",
            message,
        )

    # =================================================
    # Telemetry
    # =================================================

    @Slot(dict)
    def handle_telemetry(
        self,
        data,
    ):

        if self.shutdown_started:
            return

        self.value_labels[
            "Time"
        ].setText(
            f"{data['Time']:.4f}"
        )

        self.value_labels[
            "theta"
        ].setText(
            f"{data['theta']:.4f}"
        )

        self.value_labels[
            "thetaDot"
        ].setText(
            f"{data['thetaDot']:.4f}"
        )

        self.value_labels[
            "x"
        ].setText(
            f"{data['x']:.4f}"
        )

        self.value_labels[
            "xDotObs"
        ].setText(
            f"{data['xDotObs']:.4f}"
        )

        self.value_labels[
            "xDotXActual"
        ].setText(
            f"{data['xDotXActual']:.4f}"
        )

        self.value_labels[
            "u"
        ].setText(
            f"{data['u']:.4f}"
        )

        new_state = data[
            "state"
        ]

        new_mode = data[
            "mode"
        ]

        self.current_state = (
            new_state
        )

        self.current_mode = (
            new_mode
        )

        self.state_label.setText(
            self._state_name(
                new_state
            )
        )

        self.mode_label.setText(
            self._mode_name(
                new_mode
            )
        )

        self._update_state_style(
            new_state
        )

        if new_state == SystemState.RUNNING:
            self.start_pending = False

        if new_state == SystemState.FAULT:
            self.start_pending = False
            self.finish_pending = False

        self._update_buttons()

    # =================================================
    # Experiment
    # =================================================

    @Slot(str)
    def handle_experiment_started(self, filename):
        self._append_console("PC", f"New experiment started. CSV: {filename}")
        self._update_buttons()

    @Slot(str)
    def handle_experiment_message(self, message):
        self._append_console("PC", message)

    @Slot(str, int, str)
    def handle_experiment_finished(self, filename, samples, reason):
        self.finish_pending = False
        self._append_console("PC", f"{reason}. {samples} samples saved.")
        self._update_buttons()
        if filename and samples > 0 and not self.shutdown_started:
            plot_experiment(filename, block=False)

    # =================================================
    # State names
    # =================================================

    @staticmethod
    def _state_name(
        state,
    ):

        try:

            return SystemState(
                state
            ).name

        except ValueError:

            return (
                f"UNKNOWN ({state})"
            )

    @staticmethod
    def _mode_name(
        mode,
    ):

        try:

            return ControlMode(
                mode
            ).name

        except ValueError:

            return (
                f"UNKNOWN ({mode})"
            )

    def _update_state_style(
        self,
        state,
    ):

        if state == SystemState.READY:

            self.state_label.setStyleSheet(
                "color: #2e8b57;"
            )

        elif state == SystemState.RUNNING:

            self.state_label.setStyleSheet(
                "color: #1976d2;"
            )

        elif state == SystemState.FAULT:

            self.state_label.setStyleSheet(
                "color: #c62828;"
            )

        elif state == SystemState.HOMING:

            self.state_label.setStyleSheet(
                "color: #c08020;"
            )

        else:

            self.state_label.setStyleSheet(
                ""
            )

    # =================================================
    # Buttons
    # =================================================

    def _update_buttons(
        self,
    ):

        if (
            not self.connected
            or self.shutdown_started
        ):

            self.start_button.setEnabled(
                False
            )

            self.stop_button.setEnabled(
                False
            )

            self.finish_button.setEnabled(
                False
            )

            self.estop_button.setEnabled(
                False
            )

            return

        self.start_button.setEnabled(
            (
                self.current_state
                == SystemState.READY
                and not self.start_pending
                and not self.finish_pending
            )
        )

        self.stop_button.setEnabled(
            (
                self.current_state
                == SystemState.RUNNING
                and not self.finish_pending
            )
        )

        self.finish_button.setEnabled(
            (
                self.session.active
                and not self.finish_pending
            )
        )

        self.estop_button.setEnabled(
            True
        )

    def _start_clicked(
        self,
    ):

        if (
            self.current_state
            != SystemState.READY
        ):
            return

        self.start_pending = True

        self.serial_worker.queue_command(
            "R"
        )

        self._append_console(
            "PC",
            "START / RESUME sent.",
        )

        self._update_buttons()

        QTimer.singleShot(
            1000,
            self._clear_start_pending,
        )

    def _clear_start_pending(
        self,
    ):

        if (
            self.current_state
            != SystemState.RUNNING
        ):

            self.start_pending = False

        self._update_buttons()

    def _stop_clicked(
        self,
    ):

        if (
            self.current_state
            != SystemState.RUNNING
        ):
            return

        self.serial_worker.queue_command(
            "S"
        )

        self._append_console(
            "PC",
            "PAUSE sent.",
        )

    def _finish_clicked(self):
        if not self.session.active or self.finish_pending:
            return
        self.finish_pending = True
        self.session.finish_when_ready()
        if self.current_state == SystemState.RUNNING:
            self.serial_worker.queue_command("S")
            self._append_console("PC", "FINISH requested. Waiting for READY...")
        self._update_buttons()

    def _estop_clicked(
        self,
    ):

        if not self.connected:
            return

        self.serial_worker.queue_command(
            "X"
        )

        self.start_pending = False

        self._append_console(
            "PC",
            "EMERGENCY STOP sent.",
        )

    # =================================================
    # Plots
    # =================================================

    @staticmethod
    def _fit_to_screen(window, width, height):
        area = window.screen().availableGeometry()
        window.resize(min(width, max(1, area.width() - 60)),
                      min(height, max(1, area.height() - 80)))
        window.move(area.x() + max(0, (area.width() - window.width()) // 2),
                    area.y() + max(0, (area.height() - window.height()) // 2))

    def _open_plot(self, name):
        dialog = self.plot_windows[name]
        if not dialog.isVisible():
            self._fit_to_screen(dialog, 800, 450)
        self._plot_revision = None
        self._update_plots()
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()

    def _clear_plot_buffers(self):
        self.visual_buffer.clear()
        for curve in (self.theta_curve, self.x_curve, self.u_curve):
            curve.setData([], [])

    @Slot(float)
    def _set_plot_window(self, seconds):
        self.visual_buffer.window_seconds = seconds
        self._update_plots()

    def _update_plots(self):
        if self.shutdown_started:
            return
        snapshot = self.visual_buffer.snapshot_if_changed(
            ("Time", *self.plot_series), self._plot_revision
        )
        if snapshot is None:
            return
        self._plot_revision, values = snapshot
        times = values["Time"]
        width = self.visual_buffer.window_seconds
        right = max(width, times[-1]) if times else width
        for name, (plot, curve) in self.plot_series.items():
            curve.setData(times, values[name])
            plot.setXRange(right - width, right, padding=0)

    # =================================================
    # Shutdown
    # =================================================

    def closeEvent(
        self,
        event,
    ):
        """
        Cierre limpio.

        MUY IMPORTANTE:

        Aquí NO llamamos:

            serial_worker.stop()

        porque SerialWorker pertenece a otro thread.

        Emitimos shutdown_requested y Qt ejecutará
        el slot stop() dentro del Serial thread.
        """

        if self.shutdown_started:

            event.accept()

            return

        self.shutdown_started = True

        # -----------------------------------------
        # Detener refresco GUI
        #
        # Este timer pertenece al GUI thread,
        # así que sí podemos detenerlo aquí.
        # -----------------------------------------

        self.plot_timer.stop()
        for dialog in self.plot_windows.values():
            dialog.close()

        # SerialWorker drena y cierra el registro antes de emitir finished.

        # -----------------------------------------
        # Cerrar TODAS las ventanas matplotlib
        # antes de terminar QApplication.
        # -----------------------------------------

        close_all_plots()

        # -----------------------------------------
        # Si estamos controlando físicamente,
        # SerialWorker intentará mandar S antes
        # de cerrar el puerto.
        # -----------------------------------------

        send_stop = (
            self.connected
            and self.current_state
            == SystemState.RUNNING
        )

        # -----------------------------------------
        # Esta SIGNAL cruza correctamente al
        # SerialWorker thread.
        # -----------------------------------------

        self.shutdown_requested.emit(
            send_stop
        )

        event.accept()
