import threading
from collections import deque

import serial

from PySide6.QtCore import (
    QObject,
    QTimer,
    Signal,
    Slot,
)


class SerialLink:

    REQUIRED_FIELDS = [
        "Time",
        "theta",
        "thetaDot",
        "x",
        "xDotObs",
        "xDotXActual",
        "u",
        "state",
        "mode",
    ]

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

        self._serial_lock = (
            threading.RLock()
        )

    @property
    def is_open(self):

        with self._serial_lock:

            return (
                self.ser is not None
                and self.ser.is_open
            )

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

    def send_command(
        self,
        command,
    ):

        command = (
            command
            .strip()
            .upper()
        )

        if (
            command
            not in self.VALID_COMMANDS
        ):

            raise ValueError(
                (
                    "Comando Serial "
                    f"no válido: {command}"
                )
            )

        with self._serial_lock:

            if not self.is_open:

                raise serial.SerialException(
                    (
                        "El puerto Serial "
                        "no está abierto."
                    )
                )

            self.ser.write(
                command.encode(
                    "ascii"
                )
            )

            self.ser.flush()

    def read_message(self):

        with self._serial_lock:

            if not self.is_open:

                return (
                    None,
                    None,
                )

            line = (
                self.ser.readline()
            )

        if not line:

            return (
                None,
                None,
            )

        try:

            line = line.decode(
                "utf-8",
                errors="ignore",
            ).strip()

        except Exception:

            return (
                None,
                None,
            )

        if not line:

            return (
                None,
                None,
            )

        try:

            values = {}

            fields = line.split()

            for field in fields:

                if "=" not in field:
                    continue

                key, value = (
                    field.split(
                        "=",
                        1,
                    )
                )

                values[key] = float(
                    value
                )

            for field in self.REQUIRED_FIELDS:

                if field not in values:

                    return (
                        "message",
                        line,
                    )

            values["state"] = int(
                values["state"]
            )

            values["mode"] = int(
                values["mode"]
            )

            return (
                "telemetry",
                values,
            )

        except (
            ValueError,
            TypeError,
        ):

            return (
                "message",
                line,
            )

    def close(self):

        with self._serial_lock:

            if self.ser is None:
                return

            if self.ser.is_open:

                self.ser.close()

            self.ser = None


class SerialWorker(QObject):

    telemetry_received = Signal(
        dict
    )

    message_received = Signal(
        str
    )

    connection_changed = Signal(
        bool,
        str,
    )

    serial_error = Signal(
        str
    )

    finished = Signal()

    def __init__(
        self,
        serial_link,
        parent=None,
    ):

        super().__init__(
            parent
        )

        self.serial_link = (
            serial_link
        )

        self._poll_timer = None

        self._startup_timer = None

        self._stopping = False

        self._finished_emitted = False

        self._command_queue = deque()

        self._command_lock = (
            threading.Lock()
        )

    # =============================================
    # START
    # =============================================

    @Slot()
    def start(self):

        try:

            self.serial_link.open()

            self.connection_changed.emit(
                True,
                (
                    f"{self.serial_link.port} "
                    f"@ "
                    f"{self.serial_link.baudrate}"
                ),
            )

            self.message_received.emit(
                "Puerto serie abierto."
            )

            # -------------------------------------
            # El ESP32 puede resetearse al abrir
            # el USB.
            #
            # QTimer está creado dentro del
            # SerialWorker thread.
            # -------------------------------------

            self._startup_timer = QTimer(
                self
            )

            self._startup_timer.setSingleShot(
                True
            )

            self._startup_timer.timeout.connect(
                self._begin_polling
            )

            self._startup_timer.start(
                2000
            )

        except Exception as exc:

            self.connection_changed.emit(
                False,
                str(exc),
            )

            self.serial_error.emit(
                (
                    "No se pudo abrir "
                    "el puerto Serial: "
                    f"{exc}"
                )
            )

            self._emit_finished()

    # =============================================
    # Polling
    # =============================================

    @Slot()
    def _begin_polling(self):

        if self._stopping:
            return

        self._poll_timer = QTimer(
            self
        )

        self._poll_timer.setInterval(
            10
        )

        self._poll_timer.timeout.connect(
            self._poll_serial
        )

        self._poll_timer.start()

        self.message_received.emit(
            "Lectura de telemetría iniciada."
        )

    # =============================================
    # Command queue
    # =============================================

    def queue_command(
        self,
        command,
    ):

        command = (
            command
            .strip()
            .upper()
        )

        if (
            command
            not in SerialLink.VALID_COMMANDS
        ):

            return

        with self._command_lock:

            # -------------------------------------
            # Emergency stop tiene prioridad
            # absoluta.
            # -------------------------------------

            if command == "X":

                self._command_queue.clear()

                self._command_queue.appendleft(
                    "X"
                )

            # -------------------------------------
            # STOP elimina cualquier START
            # pendiente.
            # -------------------------------------

            elif command == "S":

                self._command_queue = deque(
                    item
                    for item
                    in self._command_queue
                    if item != "R"
                )

                self._command_queue.appendleft(
                    "S"
                )

            # -------------------------------------
            # Nunca acumulamos varios R.
            # -------------------------------------

            elif command == "R":

                if (
                    "R"
                    not in self._command_queue
                ):

                    self._command_queue.append(
                        "R"
                    )

    def _get_next_command(
        self,
    ):

        with self._command_lock:

            if not self._command_queue:

                return None

            return (
                self._command_queue
                .popleft()
            )

    # =============================================
    # Serial loop
    # =============================================

    @Slot()
    def _poll_serial(self):

        if self._stopping:
            return

        try:

            # -------------------------------------
            # TX
            # -------------------------------------

            while True:

                command = (
                    self._get_next_command()
                )

                if command is None:
                    break

                self.serial_link.send_command(
                    command
                )

            # -------------------------------------
            # RX
            # -------------------------------------

            for _ in range(20):

                (
                    message_type,
                    data,
                ) = (
                    self.serial_link
                    .read_message()
                )

                if message_type is None:
                    break

                if (
                    message_type
                    == "telemetry"
                ):

                    self.telemetry_received.emit(
                        data
                    )

                elif (
                    message_type
                    == "message"
                ):

                    self.message_received.emit(
                        data
                    )

        except serial.SerialException as exc:

            self._handle_serial_error(
                f"Error Serial: {exc}"
            )

        except Exception as exc:

            self._handle_serial_error(
                (
                    "Error inesperado "
                    f"en Serial: {exc}"
                )
            )

    # =============================================
    # Serial errors
    # =============================================

    def _handle_serial_error(
        self,
        message,
    ):

        if self._stopping:
            return

        self.serial_error.emit(
            message
        )

        self.connection_changed.emit(
            False,
            message,
        )

        self._stop_timers()

        try:

            self.serial_link.close()

        except Exception:

            pass

        self._emit_finished()

    # =============================================
    # Timer cleanup
    # =============================================

    def _stop_timers(self):
        """
        Este método se ejecuta SIEMPRE dentro
        del SerialWorker thread.

        Por tanto Qt permite detener los QTimer
        sin warnings de cross-thread.
        """

        if (
            self._startup_timer
            is not None
        ):

            self._startup_timer.stop()

            self._startup_timer.deleteLater()

            self._startup_timer = None

        if (
            self._poll_timer
            is not None
        ):

            self._poll_timer.stop()

            self._poll_timer.deleteLater()

            self._poll_timer = None

    # =============================================
    # STOP
    # =============================================

    @Slot(bool)
    def stop(
        self,
        send_stop=False,
    ):
        """
        IMPORTANTE:

        Esta función NO debe llamarse directamente
        desde el GUI thread.

        MainWindow emite una señal conectada a
        este slot.

        Qt ejecuta entonces este método dentro
        del thread propietario de SerialWorker.
        """

        if self._stopping:
            return

        self._stopping = True

        # -----------------------------------------
        # Primero detenemos los timers.
        # -----------------------------------------

        self._stop_timers()

        # -----------------------------------------
        # Si cerramos mientras estamos RUNNING,
        # intentamos dejar el ESP32 en READY.
        # -----------------------------------------

        if (
            send_stop
            and self.serial_link.is_open
        ):

            try:

                self.serial_link.send_command(
                    "S"
                )

            except Exception:

                pass

        # -----------------------------------------
        # Cerrar Serial
        # -----------------------------------------

        try:

            self.serial_link.close()

        except Exception:

            pass

        self.connection_changed.emit(
            False,
            "Puerto cerrado",
        )

        self._emit_finished()

    # =============================================
    # Finished
    # =============================================

    def _emit_finished(self):

        if self._finished_emitted:
            return

        self._finished_emitted = True

        self.finished.emit()
