from PySide6.QtGui import QFont
from PySide6.QtWidgets import QPushButton, QSizePolicy

from gui import MainWindow as BaseMainWindow
from gui import SystemState


class MainWindow(BaseMainWindow):
    """
    Extensión incremental de la GUI actual para el nuevo arranque seguro.

    Añade HOME sin reescribir la interfaz existente y mantiene toda la
    lógica actual de START/PAUSE/FINISH/E-STOP y gráficos.
    """

    def __init__(self, serial_worker, parent=None):
        self.home_pending = False
        super().__init__(serial_worker, parent)

    def _build_ui(self):
        super()._build_ui()

        self.home_button = QPushButton("HOME")

        button_font = QFont()
        button_font.setPointSize(12)
        button_font.setBold(True)

        self.home_button.setMinimumHeight(45)
        self.home_button.setMaximumHeight(50)
        self.home_button.setFont(button_font)
        self.home_button.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Fixed,
        )

        self.home_button.setStyleSheet(
            """
            QPushButton {
                background-color: #1976d2;
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

        self.home_button.clicked.connect(self._home_clicked)

        # START/STOP/FINISH/E-STOP ya comparten este layout.
        # Insertamos HOME al principio sin alterar la GUI base.
        control_layout = self.start_button.parentWidget().layout()
        control_layout.insertWidget(0, self.home_button)

    def handle_connection_changed(self, connected, description):
        if not connected:
            self.home_pending = False

        super().handle_connection_changed(connected, description)

    def handle_telemetry(self, data):
        super().handle_telemetry(data)

        if self.current_state in {
            SystemState.READY,
            SystemState.FAULT,
        }:
            if self.home_pending:
                self.home_pending = False
                self._update_buttons()

    def _update_buttons(self):
        # Conservamos primero toda la política de habilitación existente.
        super()._update_buttons()

        if not hasattr(self, "home_button"):
            return

        if (
            not self.connected
            or self.shutdown_started
            or self.home_pending
        ):
            self.home_button.setEnabled(False)
            return

        # HOME sólo es válido donde también lo acepta el firmware.
        # No permitimos recalibrar dentro de un experimento pausado.
        self.home_button.setEnabled(
            self.current_state in {
                SystemState.INIT,
                SystemState.READY,
            }
            and not self.logger.active
            and not self.start_pending
            and not self.finish_pending
        )

    def _home_clicked(self):
        if (
            not self.connected
            or self.current_state
            not in {
                SystemState.INIT,
                SystemState.READY,
            }
            or self.logger.active
        ):
            return

        self.home_pending = True
        self.serial_worker.queue_command("H")

        self._append_console(
            "PC",
            "HOME sent. Waiting for homing to finish...",
        )

        self._update_buttons()
