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
        self.known_header = None
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

    def handle_header(self, signals):
        """Muestra el esquema sólo cuando aparece o cambia."""
        header = tuple(signals)

        if header != self.known_header:
            self.known_header = header
            self.handle_message(
                "HEADER: " + ", ".join(signals)
            )

    def handle_connection_changed(self, connected, description):
        if not connected:
            self.home_pending = False

            # Al perder el enlace dejamos de confiar en el último estado
            # recibido. Evita que START quede habilitado al reconectar sólo
            # porque antes de desconectar el ESP32 estaba en READY.
            self.current_state = None
            self.current_mode = None
            self.state_label.setText("---")
            self.mode_label.setText("---")

        super().handle_connection_changed(connected, description)

    def handle_message(self, message):
        super().handle_message(message)

        # Estas transiciones por MSG son sólo una ayuda de interfaz.
        # La telemetría DATA sigue siendo la fuente normal del estado.
        # Sirven para que HOME pueda operar aunque todavía estemos
        # esperando al primer DATA válido después de conectar.
        if message == "INIT - Waiting for HOME command":
            self.current_state = SystemState.INIT
            self.current_mode = 0
            self.state_label.setText("INIT")
            self.mode_label.setText("NONE")
            self._update_state_style(SystemState.INIT)
            self._update_buttons()

        elif message == "H received -> starting homing":
            self.current_state = SystemState.HOMING
            self.current_mode = 0
            self.state_label.setText("HOMING")
            self.mode_label.setText("NONE")
            self._update_state_style(SystemState.HOMING)
            self._update_buttons()

        elif message == "READY":
            self.current_state = SystemState.READY
            self.current_mode = 0
            self.home_pending = False
            self.state_label.setText("READY")
            self.mode_label.setText("NONE")
            self._update_state_style(SystemState.READY)
            self._update_buttons()

        elif message == "RUNNING":
            self.current_state = SystemState.RUNNING
            self.state_label.setText("RUNNING")
            self._update_state_style(SystemState.RUNNING)
            self._update_buttons()

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

        # Si todavía no conocemos el estado tras conectar, permitimos HOME.
        # Es seguro porque el firmware vuelve a validar H y sólo lo ejecuta
        # desde INIT o READY. START continúa deshabilitado hasta conocer READY.
        safe_for_home = (
            self.current_state is None
            or self.current_state in {
                SystemState.INIT,
                SystemState.READY,
            }
        )

        self.home_button.setEnabled(
            safe_for_home
            and not self.logger.active
            and not self.start_pending
            and not self.finish_pending
        )

    def _home_clicked(self):
        if (
            not self.connected
            or self.logger.active
            or self.home_pending
        ):
            return

        # Con estado conocido sólo aceptamos los mismos estados que firmware.
        # Con estado todavía desconocido dejamos que firmware haga la última
        # validación de seguridad del comando H.
        if (
            self.current_state is not None
            and self.current_state not in {
                SystemState.INIT,
                SystemState.READY,
            }
        ):
            return

        self.home_pending = True
        self.serial_worker.queue_command("H")

        self._append_console(
            "PC",
            "HOME sent. Waiting for homing to finish...",
        )

        self._update_buttons()
