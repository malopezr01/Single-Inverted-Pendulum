from collections import deque
from enum import IntEnum

import pyqtgraph as pg

from PySide6.QtCore import (
    QTime,
    QTimer,
    Qt,
    Signal,
)

from PySide6.QtGui import QFont

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from experiment_logger import ExperimentLogger

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

    PLOT_WINDOW_SECONDS = 15.0

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

        self.logger = ExperimentLogger(
            experiments_dir="experiments"
        )

        self.connected = False

        self.current_state = None

        self.current_mode = None

        self.start_pending = False

        self.finish_pending = False

        self.shutdown_started = False

        # =============================================
        # Buffers
        # =============================================

        self.time_buffer = deque()

        self.theta_buffer = deque()

        self.x_buffer = deque()

        self.u_buffer = deque()

        # =============================================
        # Window
        # =============================================

        self.setWindowTitle(
            "Inverted Pendulum Control"
        )

        self.resize(
            1100,
            720,
        )

        self._build_ui()

        # =============================================
        # Plot refresh
        # =============================================

        self.plot_timer = QTimer(
            self
        )

        self.plot_timer.timeout.connect(
            self._update_plots
        )

        self.plot_timer.start(
            100
        )

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

        self.setCentralWidget(
            central_widget
        )

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

        plots_group = QGroupBox(
            (
                "Real-time plots "
                f"(last "
                f"{self.PLOT_WINDOW_SECONDS:.0f} s "
                "active time)"
            )
        )

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

        self.plot_splitter = QSplitter(
            Qt.Vertical
        )

        self.plot_splitter.setChildrenCollapsible(
            False
        )

        self.theta_plot = (
            self._create_plot(
                "Pendulum angle",
                "theta [rad]",
            )
        )

        self.x_plot = (
            self._create_plot(
                "Cart position",
                "x [m]",
            )
        )

        self.u_plot = (
            self._create_plot(
                "Control acceleration",
                "u [m/s²]",
            )
        )

        self.theta_curve = (
            self.theta_plot.plot()
        )

        self.x_curve = (
            self.x_plot.plot()
        )

        self.u_curve = (
            self.u_plot.plot()
        )

        self.plot_splitter.addWidget(
            self.theta_plot
        )

        self.plot_splitter.addWidget(
            self.x_plot
        )

        self.plot_splitter.addWidget(
            self.u_plot
        )

        self.plot_splitter.setStretchFactor(
            0,
            1,
        )

        self.plot_splitter.setStretchFactor(
            1,
            1,
        )

        self.plot_splitter.setStretchFactor(
            2,
            1,
        )

        self.plot_splitter.setSizes(
            [
                140,
                140,
                140,
            ]
        )

        plots_layout.addWidget(
            self.plot_splitter
        )

        main_layout.addWidget(
            plots_group,
            stretch=1,
        )

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

        control_layout = QHBoxLayout(
            control_frame
        )

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

        control_layout.addWidget(
            self.start_button
        )

        control_layout.addWidget(
            self.stop_button
        )

        control_layout.addWidget(
            self.finish_button
        )

        control_layout.addWidget(
            self.estop_button,
            stretch=2,
        )

        main_layout.addWidget(
            control_frame
        )

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

        plot = pg.PlotWidget()

        plot.setTitle(
            title
        )

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
            40
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

    def handle_serial_error(
        self,
        message,
    ):

        self._append_console(
            "ERROR",
            message,
        )

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

        previous_state = (
            self.current_state
        )

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

        # =============================================
        # Entrada RUNNING
        # =============================================

        if (
            previous_state
            != SystemState.RUNNING
            and new_state
            == SystemState.RUNNING
        ):

            self.start_pending = False

            if not self.logger.active:

                self._clear_plot_buffers()

                filename = (
                    self.logger.start()
                )

                self._append_console(
                    "PC",
                    (
                        "New experiment started. "
                        f"CSV: {filename}"
                    ),
                )

            else:

                self._append_console(
                    "PC",
                    "Experiment resumed.",
                )

        # =============================================
        # Logging
        # =============================================

        if (
            new_state
            == SystemState.RUNNING
        ):

            if self.logger.active:

                self.logger.write(
                    data
                )

            self._append_plot_sample(
                data
            )

        # =============================================
        # RUNNING -> READY
        # =============================================

        if (
            previous_state
            == SystemState.RUNNING
            and new_state
            == SystemState.READY
        ):

            if self.finish_pending:

                self.finish_pending = False

                self._finish_experiment(
                    "Finished by user"
                )

            elif self.logger.active:

                self._append_console(
                    "PC",
                    "Experiment paused.",
                )

        # =============================================
        # FAULT
        # =============================================

        if (
            previous_state
            != SystemState.FAULT
            and new_state
            == SystemState.FAULT
        ):

            self.start_pending = False

            self.finish_pending = False

            if self.logger.active:

                self._finish_experiment(
                    "FAULT"
                )

        self._update_buttons()

    # =================================================
    # Experiment
    # =================================================

    def _finish_experiment(
        self,
        reason,
    ):

        if not self.logger.active:
            return

        (
            filename,
            samples,
        ) = self.logger.stop()

        self._append_console(
            "PC",
            (
                f"{reason}. "
                f"{samples} samples saved."
            ),
        )

        if (
            filename
            and samples > 0
        ):

            plot_experiment(
                filename,
                block=False,
            )

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
                self.logger.active
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

    def _finish_clicked(
        self,
    ):

        if not self.logger.active:
            return

        if (
            self.current_state
            == SystemState.RUNNING
        ):

            self.finish_pending = True

            self.serial_worker.queue_command(
                "S"
            )

            self._append_console(
                "PC",
                (
                    "FINISH requested. "
                    "Waiting for READY..."
                ),
            )

        elif (
            self.current_state
            == SystemState.READY
        ):

            self._finish_experiment(
                "Finished by user"
            )

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

    def _clear_plot_buffers(
        self,
    ):

        self.time_buffer.clear()

        self.theta_buffer.clear()

        self.x_buffer.clear()

        self.u_buffer.clear()

        self.theta_curve.setData(
            [],
            [],
        )

        self.x_curve.setData(
            [],
            [],
        )

        self.u_curve.setData(
            [],
            [],
        )

    def _append_plot_sample(
        self,
        data,
    ):

        current_time = data[
            "Time"
        ]

        self.time_buffer.append(
            current_time
        )

        self.theta_buffer.append(
            data["theta"]
        )

        self.x_buffer.append(
            data["x"]
        )

        self.u_buffer.append(
            data["u"]
        )

        minimum_time = (
            current_time
            - self.PLOT_WINDOW_SECONDS
        )

        while (
            self.time_buffer
            and self.time_buffer[0]
            < minimum_time
        ):

            self.time_buffer.popleft()

            self.theta_buffer.popleft()

            self.x_buffer.popleft()

            self.u_buffer.popleft()

    def _update_plots(
        self,
    ):

        if (
            self.shutdown_started
            or not self.time_buffer
        ):

            return

        time_data = list(
            self.time_buffer
        )

        self.theta_curve.setData(
            time_data,
            list(
                self.theta_buffer
            ),
        )

        self.x_curve.setData(
            time_data,
            list(
                self.x_buffer
            ),
        )

        self.u_curve.setData(
            time_data,
            list(
                self.u_buffer
            ),
        )

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

        # -----------------------------------------
        # Si existe un experimento abierto,
        # cerramos el CSV.
        #
        # Al salir de la aplicación NO abrimos
        # nuevas gráficas.
        # -----------------------------------------

        if self.logger.active:

            try:

                (
                    filename,
                    samples,
                ) = self.logger.stop()

                print(
                    (
                        "Experiment saved on exit: "
                        f"{filename} "
                        f"({samples} samples)"
                    )
                )

            except Exception as exc:

                print(
                    (
                        "Error closing experiment: "
                        f"{exc}"
                    )
                )

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
