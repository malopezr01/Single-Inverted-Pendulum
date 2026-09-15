from PySide6.QtGui import QFont
from PySide6.QtWidgets import QPushButton, QSizePolicy

from gui import MainWindow as BaseMainWindow
from gui import ControlMode, SystemState


class MainWindow(BaseMainWindow):
    """
    Extensión incremental de la GUI actual para el nuevo arranque seguro.

    Añade HOME y mantiene un FAULT local enclavado después de un
    EMERGENCY STOP. El enclavamiento sólo se libera cuando el ESP32
    anuncia explícitamente un nuevo INIT después de reiniciarse.
    """

    def __init__(self, serial_worker, parent=None):
        self.home_pending = False
        self.known_header = None
        self.fault_latched = False
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
            # recibido. El FAULT local, si existe, se conserva hasta que
            # el ESP32 confirme un nuevo INIT tras reiniciarse.
            self.current_state = None
            self.current_mode = None
            self.state_label.setText("---")
            self.mode_label.setText("---")

        super().handle_connection_changed(connected, description)

    def handle_message(self, message):
        super().handle_message(message)

        # INIT es la evidencia de que el ESP32 se ha reiniciado. Sólo aquí
        # liberamos el enclavamiento local producido por EMERGENCY STOP.
        if message == "INIT - Waiting for HOME command":
            self.fault_latched = False
            self.current_state = SystemState.INIT
            self.current_mode = ControlMode.NONE
            self.state_label.setText("INIT")
            self.mode_label.setText("NONE")
            self._update_state_style(SystemState.INIT)
            self._update_buttons()

        elif self.fault_latched:
            # Después de un E-STOP no permitimos que mensajes atrasados como
            # READY o RUNNING vuelvan a habilitar controles en la interfaz.
            self._update_buttons()
            return

        elif message == "H received -> starting homing":
            self.current_state = SystemState.HOMING
            self.current_mode = ControlMode.NONE
            self.state_label.setText("HOMING")
            self.mode_label.setText("NONE")
            self._update_state_style(SystemState.HOMING)
            self._update_buttons()

        elif message == "READY":
            self.current_state = SystemState.READY
            self.current_mode = ControlMode.NONE
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

    def handle_esp_error(self, message):
        """Procesa errores explícitos enviados por el firmware."""
        self._append_console(
            "ESP32",
            f"ERROR: {message}",
        )

        if "EMERGENCY STOP" in message.upper():
            self._enter_fault_ui("EMERGENCY STOP")

    def handle_telemetry(self, data):
        incoming_state = data.get("state")

        # Un FAULT recibido por DATA también enclava inmediatamente la GUI.
        if incoming_state == SystemState.FAULT:
            self.fault_latched = True

        # Si acabamos de pulsar E-STOP pueden quedar algunas tramas READY o
        # RUNNING ya almacenadas en el puerto serie. No dejamos que esas
        # muestras antiguas saquen visualmente a la aplicación de FAULT.
        if self.fault_latched and incoming_state != SystemState.FAULT:
            data = dict(data)
            data["state"] = int(SystemState.FAULT)
            data["mode"] = int(ControlMode.NONE)

        super().handle_telemetry(data)

        if self.current_state in {
            SystemState.READY,
            SystemState.FAULT,
        }:
            if self.home_pending:
                self.home_pending = False

        self._update_buttons()

    def _enter_fault_ui(self, reason):
        """Enclava toda la interfaz en FAULT hasta un nuevo INIT."""
        already_faulted = self.fault_latched

        self.fault_latched = True
        self.home_pending = False
        self.start_pending = False
        self.finish_pending = False

        self.current_state = SystemState.FAULT
        self.current_mode = ControlMode.NONE

        self.state_label.setText("FAULT")
        self.mode_label.setText("NONE")
        self._update_state_style(SystemState.FAULT)

        # Si el E-STOP sucede durante un experimento, lo cerramos ahora.
        # Al fijar FAULT localmente no dependemos de esperar otra trama DATA.
        if self.logger.active and not already_faulted:
            self._finish_experiment(reason)

        self._update_buttons()

    def _update_buttons(self):
        super()._update_buttons()

        if not hasattr(self, "home_button"):
            return

        # FAULT es enclavado: ninguna acción de control queda disponible.
        # La única forma de recuperar la GUI es reiniciar el ESP32 y recibir
        # de nuevo "INIT - Waiting for HOME command".
        if self.fault_latched or self.current_state == SystemState.FAULT:
            self.home_button.setEnabled(False)
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.finish_button.setEnabled(False)
            self.estop_button.setEnabled(False)
            return

        if (
            not self.connected
            or self.shutdown_started
            or self.home_pending
        ):
            self.home_button.setEnabled(False)
            return

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
            self.fault_latched
            or not self.connected
            or self.logger.active
            or self.home_pending
        ):
            return

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

    def _estop_clicked(self):
        if not self.connected or self.fault_latched:
            return

        # La GUI se enclava en FAULT inmediatamente al pulsar el botón,
        # sin esperar a que vuelva la confirmación por Serial.
        self.serial_worker.queue_command("X")

        self._append_console(
            "PC",
            "EMERGENCY STOP sent.",
        )

        self._enter_fault_ui("EMERGENCY STOP")
