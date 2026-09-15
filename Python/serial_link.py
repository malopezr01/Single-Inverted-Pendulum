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
    lee líneas y envía comandos de un carácter al ESP32.
    """

    VALID_COMMANDS = {
        "H",
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
            )

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
        Protocolo PC -> ESP32:

            H -> HOME
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

    La aplicación permanece viva aunque el ESP32 no esté conectado.
    El worker reintenta abrir el puerto periódicamente y sólo emite
    finished cuando la aplicación solicita el cierre.
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

    RECONNECT_INTERVAL_MS = 1000
    POLL_INTERVAL_MS = 5
    STARTUP_DELAY_MS = 2000

    def __init__(
        self,
        serial_link,
        parent=None,
    ):
        super().__init__(parent)

        self.serial_link = serial_link
        self.parser = TelemetryParser()

        self._poll_timer = None
        self._reconnect_timer = None
        self._startup_timer = None

        self._stopping = False
        self._finished_emitted = False
        self._acquisition_enabled = False
        self._last_connection_state = None
        self._last_connection_description = None

        self._command_queue = deque()
        self._command_lock = threading.Lock()

    @Slot()
    def start(self):
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(self.POLL_INTERVAL_MS)
        self._poll_timer.timeout.connect(self._poll_serial)
        self._poll_timer.start()

        self._reconnect_timer = QTimer(self)
        self._reconnect_timer.setInterval(self.RECONNECT_INTERVAL_MS)
        self._reconnect_timer.timeout.connect(self._ensure_connection)
        self._reconnect_timer.start()

        self._ensure_connection()

    def _emit_connection_state(self, connected, description):
        if (
            connected == self._last_connection_state
            and description == self._last_connection_description
        ):
            return

        self._last_connection_state = connected
        self._last_connection_description = description
        self.connection_changed.emit(connected, description)

    @Slot()
    def _ensure_connection(self):
        if self._stopping or self.serial_link.is_open:
            return

        try:
            self.parser.reset()
            self.serial_link.open()
            self._acquisition_enabled = False

            self._emit_connection_state(
                True,
                f"{self.serial_link.port} @ {self.serial_link.baudrate}",
            )
            self.message_received.emit("Puerto serie abierto.")

            # Muchos ESP32 se reinician al abrir el USB. Esperamos sin
            # bloquear el GUI ni vaciar el buffer de entrada, para no
            # perder HEADER u otros mensajes de arranque.
            if self._startup_timer is not None:
                self._startup_timer.stop()
                self._startup_timer.deleteLater()

            self._startup_timer = QTimer(self)
            self._startup_timer.setSingleShot(True)
            self._startup_timer.timeout.connect(self._begin_acquisition)
            self._startup_timer.start(self.STARTUP_DELAY_MS)

        except (serial.SerialException, OSError) as exc:
            self._acquisition_enabled = False
            self._emit_connection_state(
                False,
                f"Esperando {self.serial_link.port}: {exc}",
            )

        except Exception as exc:
            self._acquisition_enabled = False
            self._emit_connection_state(
                False,
                f"Esperando {self.serial_link.port}: {exc}",
            )

    @Slot()
    def _begin_acquisition(self):
        if self._stopping or not self.serial_link.is_open:
            return

        self._acquisition_enabled = True
        self.message_received.emit("Adquisición serie iniciada.")

    def queue_command(self, command):
        command = command.strip().upper()

        if command not in SerialLink.VALID_COMMANDS:
            return

        with self._command_lock:
            if command == "X":
                self._command_queue.clear()
                self._command_queue.appendleft("X")

            elif command == "S":
                self._command_queue = deque(
                    item
                    for item in self._command_queue
                    if item not in {"R", "H"}
                )
                self._command_queue.appendleft("S")

            elif command == "H":
                self._command_queue = deque(
                    item
                    for item in self._command_queue
                    if item != "R"
                )
                if "H" not in self._command_queue:
                    self._command_queue.append("H")

            elif command == "R":
                if "R" not in self._command_queue:
                    self._command_queue.append("R")

    def _get_next_command(self):
        with self._command_lock:
            if not self._command_queue:
                return None

            return self._command_queue.popleft()

    def _clear_commands(self):
        with self._command_lock:
            self._command_queue.clear()

    @Slot()
    def _poll_serial(self):
        if (
            self._stopping
            or not self._acquisition_enabled
            or not self.serial_link.is_open
        ):
            return

        try:
            while True:
                command = self._get_next_command()

                if command is None:
                    break

                self.serial_link.send_command(command)

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
                    self.telemetry_received.emit(payload)

                elif frame_type == "message":
                    self.message_received.emit(payload)

                elif frame_type == "event":
                    self.event_received.emit(payload)

                elif frame_type == "error":
                    self.esp_error_received.emit(payload)

                elif frame_type == "protocol_error":
                    self.protocol_error.emit(payload)

        except (serial.SerialException, OSError) as exc:
            self._handle_connection_loss(f"Error Serial: {exc}")

        except Exception as exc:
            self._handle_connection_loss(
                f"Error inesperado en adquisición: {exc}"
            )

    def _handle_connection_loss(self, message):
        if self._stopping:
            return

        self._acquisition_enabled = False
        self.parser.reset()
        self._clear_commands()

        if self._startup_timer is not None:
            self._startup_timer.stop()

        try:
            self.serial_link.close()
        except Exception:
            pass

        self.serial_error.emit(message)
        self._emit_connection_state(False, message)
        # No emitimos finished: el reconnect timer seguirá intentando
        # recuperar automáticamente el ESP32.

    def _stop_timers(self):
        for timer_name in (
            "_startup_timer",
            "_poll_timer",
            "_reconnect_timer",
        ):
            timer = getattr(self, timer_name)

            if timer is not None:
                timer.stop()
                timer.deleteLater()
                setattr(self, timer_name, None)

    @Slot(bool)
    def stop(self, send_stop=False):
        if self._stopping:
            return

        self._stopping = True
        self._acquisition_enabled = False
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

        self._emit_connection_state(False, "Puerto cerrado")
        self._emit_finished()

    def _emit_finished(self):
        if self._finished_emitted:
            return

        self._finished_emitted = True
        self.finished.emit()
