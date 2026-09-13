import signal
import sys

from PySide6.QtCore import (
    QThread,
    QTimer,
)

from PySide6.QtWidgets import QApplication

from gui import MainWindow

from serial_link import (
    SerialLink,
    SerialWorker,
)


SERIAL_PORT = "/dev/ttyACM0"
BAUDRATE = 115200


def main():

    # =============================================
    # Qt application
    # =============================================

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "Inverted Pendulum Control"
    )

    # No queremos que Qt termine automáticamente cuando se cierre
    # MainWindow. Primero se cierra correctamente el worker serie y
    # después se abandona QApplication.
    app.setQuitOnLastWindowClosed(
        False
    )

    # =============================================
    # Serial
    # =============================================

    serial_link = SerialLink(
        port=SERIAL_PORT,
        baudrate=BAUDRATE,
        timeout=0.02,
    )

    serial_worker = SerialWorker(
        serial_link
    )

    serial_thread = QThread()

    serial_worker.moveToThread(
        serial_thread
    )

    # =============================================
    # GUI
    # =============================================

    window = MainWindow(
        serial_worker
    )

    # =============================================
    # Inicio del thread Serial
    # =============================================

    serial_thread.started.connect(
        serial_worker.start
    )

    # =============================================
    # Serial -> GUI
    # =============================================

    serial_worker.telemetry_received.connect(
        window.handle_telemetry
    )

    serial_worker.message_received.connect(
        window.handle_message
    )

    # Fase 1 del nuevo protocolo dinámico. La GUI todavía no utiliza
    # HEADER para construir controles, pero dejamos visible el HEADER
    # recibido para facilitar la depuración por puerto serie.
    serial_worker.header_received.connect(
        lambda signals: window.handle_message(
            "HEADER: " + ", ".join(signals)
        )
    )

    serial_worker.event_received.connect(
        lambda message: window.handle_message(
            f"EVENT: {message}"
        )
    )

    serial_worker.esp_error_received.connect(
        lambda message: window.handle_message(
            f"ERROR: {message}"
        )
    )

    serial_worker.protocol_error.connect(
        lambda message: window.handle_serial_error(
            f"Protocol error: {message}"
        )
    )

    serial_worker.connection_changed.connect(
        window.handle_connection_changed
    )

    serial_worker.serial_error.connect(
        window.handle_serial_error
    )

    # =============================================
    # GUI -> Serial
    # =============================================
    #
    # MainWindow emite una señal. Como SerialWorker vive en
    # serial_thread, Qt ejecuta stop() dentro de ese thread y sus
    # QTimer se destruyen desde el thread correcto.

    window.shutdown_requested.connect(
        serial_worker.stop
    )

    # =============================================
    # Finalización ordenada
    # =============================================

    serial_worker.finished.connect(
        serial_thread.quit
    )

    serial_thread.finished.connect(
        app.quit
    )

    # =============================================
    # Ctrl+C
    # =============================================

    shutdown_requested = {
        "value": False
    }

    def handle_sigint(
        signum,
        frame,
    ):
        """Convierte Ctrl+C en un cierre normal de MainWindow."""

        if shutdown_requested["value"]:
            return

        shutdown_requested["value"] = True

        print()
        print(
            "Ctrl+C detectado. "
            "Cerrando aplicación..."
        )

        QTimer.singleShot(
            0,
            window.close,
        )

    signal.signal(
        signal.SIGINT,
        handle_sigint,
    )

    # Qt ejecuta su propio event loop. Este timer devuelve
    # periódicamente el control a Python para procesar SIGINT.
    signal_timer = QTimer()

    signal_timer.timeout.connect(
        lambda: None
    )

    signal_timer.start(
        100
    )

    # =============================================
    # Start
    # =============================================

    window.show()

    serial_thread.start()

    exit_code = app.exec()

    serial_thread.wait(
        1500
    )

    sys.exit(
        exit_code
    )


if __name__ == "__main__":
    main()
