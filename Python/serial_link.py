import threading
from collections import deque

import serial

from PySide6.QtCore import (
    QObject,
    QTimer,
    Signal,
    Slot,
)

from telemetry_parser import TelemetryParser


class SerialLink:
    """
    Capa de acceso físico al puerto serie.

    No interpreta la telemetría. Sólo abre/cierra el puerto,
    lee líneas y envía los comandos actuales R/S/X.
    """

    VALID_COMMANDS = {
        "R",
        "S",
        "X",
    }

    def __init__(
        self,
        port="/dev/ttyACM0",
        baudrate=115200,
        timeout=0.02,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self._serial_lock = threading.RLock()

    @property
    def is_open(self):
        with self._serial_lock:
            return self.ser is not None and self.ser.is_open

    def open(self):
        with self._serial_lock:
            if self.is_open:
                return

            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout,
                exclusive=True,
            )

            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()

    def read_line(self):
        """Lee una línea completa sin intentar interpretarla."""
        with self._serial_lock:
            if not self.is_open:
                return None

            raw_line = self.ser.readline()

        if not raw_line:
            return None

        try:
            line = raw_line.decode(
                "utf-8",
                errors="ignore",
            ).strip()
        except Exception:
            return None

        return line or None

    def send_command(self, command):
        """
        Mantiene el protocolo PC -> ESP32 existente:

            R -> START / RESUME
            S -> STOP / PAUSE
            X -> EMERGENCY STOP
        """
        command = command.strip().upper()

        if command not in self.VALID_COMMANDS:
            raise ValueError(f"Comando Serial no válido: {command}")

        with self._serial_lock:
            if not self.is_open:
                raise serial.SerialException("El puerto Serial no está abierto.")

            self.ser.write(command.encode("ascii"))
            self.ser.flush()

    def close(self):
        with self._serial_lock:
            if self.ser is None:
                return

            if self.ser.is_open:
                self.ser.close()

            self.ser = None


class SerialWorker(QObject):
    """
    Worker de adquisición que vive en su propio QThread.

    Flujo:

        SerialLink -> línea ASCII -> TelemetryParser -> señales Qt

    No contiene logging, buffers gráficos ni código de GUI.
    """

    telemetry_received = Signal(dict)
    header_received = Signal(list)
    message_received = Signal(str)
    event_received = Signal(str)
    esp_error_received = Signal(str)
    protocol_error = Signal(str)
    connection_changed = Signal(bool, str)
    serial_error = Signal(str)
    finished = Signal()

    def __init__(
        self,
        serial_link,
        parent=None,
    ):
        super().__init__(parent)

        self.serial_link = serial_link
        self.parser = TelemetryParser()

        self._poll_timer = None
        self._startup_timer = None
        self._stopping = False
        self._finished_emitted = False

        self._command_queue = deque()
        self._command_lock = threading.Lock()

    @Slot()
    def start(self):
        try:
            self.parser.reset()
            self.serial_link.open()

            self.connection_changed.emit(
                True,
                f"{self.serial_link.port} @ {self.serial_link.baudrate}",
            )
            self.message_received.emit("Puerto serie abierto.")

            # El ESP32 puede resetearse al abrir USB. La espera no
            # bloquea la GUI porque este objeto vive en otro QThread.
            self._startup_timer = QTimer(self)
            self._startup_timer.setSingleShot(True)
            self._startup_timer.timeout.connect(self._begin_polling)
            self._startup_timer.start(2000)

        except Exception as exc:
            self.connection_changed.emit(False, str(exc))
            self.serial_error.emit(
                f"No se pudo abrir el puerto Serial: {exc}"
            )
            self._emit_finished()

    @Slot()
    def _begin_polling(self):
        if self._stopping:
            return

        self._poll_timer = QTimer(self)

        # Este timer sólo atiende el puerto serie. La frecuencia de
        # dibujo se gestionará de forma independiente en la GUI.
        self._poll_timer.setInterval(5)
        self._poll_timer.timeout.connect(self._poll_serial)
        self._poll_timer.start()

        self.message_received.emit("Adquisición serie iniciada.")

    def queue_command(self, command):
        command = command.strip().upper()

        if command not in SerialLink.VALID_COMMANDS:
            return

        with self._command_lock:
            if command == "X":
                # Emergency stop tiene prioridad absoluta.
                self._command_queue.clear()
                self._command_queue.appendleft("X")

            elif command == "S":
                # STOP invalida cualquier START todavía pendiente.
                self._command_queue = deque(
                    item
                    for item in self._command_queue
                    if item != "R"
                )
                self._command_queue.appendleft("S")

            elif command == "R":
                # Nunca acumulamos varios START.
                if "R" not in self._command_queue:
                    self._command_queue.append("R")

    def _get_next_command(self):
        with self._command_lock:
            if not self._command_queue:
                return None

            return self._command_queue.popleft()

    @Slot()
    def _poll_serial(self):
        if self._stopping:
            return

        try:
            # Primero se atienden los comandos pendientes.
            while True:
                command = self._get_next_command()

                if command is None:
                    break

                self.serial_link.send_command(command)

            # Vaciamos varias líneas por iteración para no ligar la
            # capacidad de adquisición al periodo del QTimer.
            for _ in range(100):
                line = self.serial_link.read_line()

                if line is None:
                    break

                frame_type, payload = self.parser.parse(line)

                if frame_type is None:
                    continue

                if frame_type == "header":
                    self.header_received.emit(payload)

                elif frame_type == "data":
                    # La GUI actual sigue recibiendo un dict como antes.
                    # Con el HEADER actual no se rompe ninguna función.
                    self.telemetry_received.emit(payload)

                elif frame_type == "message":
                    self.message_received.emit(payload)

                elif frame_type == "event":
                    self.event_received.emit(payload)

                elif frame_type == "error":
                    self.esp_error_received.emit(payload)

                elif frame_type == "protocol_error":
                    self.protocol_error.emit(payload)

        except serial.SerialException as exc:
            self._handle_serial_error(f"Error Serial: {exc}")

        except Exception as exc:
            self._handle_serial_error(
                f"Error inesperado en adquisición: {exc}"
            )

    def _handle_serial_error(self, message):
        if self._stopping:
            return

        self.serial_error.emit(message)
        self.connection_changed.emit(False, message)

        self._stop_timers()

        try:
            self.serial_link.close()
        except Exception:
            pass

        self._emit_finished()

    def _stop_timers(self):
        """Se ejecuta dentro del thread propietario de los QTimer."""
        if self._startup_timer is not None:
            self._startup_timer.stop()
            self._startup_timer.deleteLater()
            self._startup_timer = None

        if self._poll_timer is not None:
            self._poll_timer.stop()
            self._poll_timer.deleteLater()
            self._poll_timer = None

    @Slot(bool)
    def stop(self, send_stop=False):
        """
        Finalización ordenada del worker.

        Este slot debe invocarse mediante una señal Qt desde la GUI para
        que la limpieza de sus timers ocurra en el thread correcto.
        """
        if self._stopping:
            return

        self._stopping = True
        self._stop_timers()

        if send_stop and self.serial_link.is_open:
            try:
                self.serial_link.send_command("S")
            except Exception:
                pass

        try:
            self.serial_link.close()
        except Exception:
            pass

        self.connection_changed.emit(False, "Puerto cerrado")
        self._emit_finished()

    def _emit_finished(self):
        if self._finished_emitted:
            return

        self._finished_emitted = True
        self.finished.emit()
