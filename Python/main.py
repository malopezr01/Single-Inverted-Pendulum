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

        # IMPORTANTE:
    #
    # No queremos que Qt termine automáticamente
    # cuando se cierre MainWindow.
    #
    # Primero necesitamos:
    #
    # 1. cerrar plots matplotlib
    # 2. pedir al SerialWorker que termine
    # 3. cerrar Serial
    # 4. terminar su QThread
    # 5. entonces cerrar QApplication

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

    serial_worker.connection_changed.connect(
        window.handle_connection_changed
    )

    serial_worker.serial_error.connect(
        window.handle_serial_error
    )

    # =============================================
    # GUI -> Serial
    #
    # MUY IMPORTANTE:
    #
    # No llamamos serial_worker.stop() directamente
    # desde MainWindow.
    #
    # MainWindow emite una SIGNAL.
    #
    # Como SerialWorker vive en serial_thread,
    # Qt ejecutará SerialWorker.stop() dentro de
    # ese thread.
    # =============================================

    window.shutdown_requested.connect(
        serial_worker.stop
    )

    # =============================================
    # Finalización ordenada
    # =============================================

    serial_worker.finished.connect(
        serial_thread.quit
    )

    # Sólo cuando el thread Serial ha terminado
    # dejamos terminar QApplication.
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
        """
        Ctrl+C ya no genera KeyboardInterrupt
        dentro de los callbacks de Qt.

        En su lugar pedimos a Qt que cierre
        MainWindow normalmente.
        """

        if shutdown_requested["value"]:
            return

        shutdown_requested["value"] = True

        print()
        print(
            "Ctrl+C detectado. "
            "Cerrando aplicación..."
        )

        # No ejecutamos window.close() directamente
        # dentro del signal handler.
        #
        # Lo ponemos en la cola de eventos Qt.
        QTimer.singleShot(
            0,
            window.close,
        )

    signal.signal(
        signal.SIGINT,
        handle_sigint,
    )

    # =============================================
    # Timer para procesamiento de señales Python
    # =============================================

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

    # =============================================
    # Aquí el Serial thread YA debería haber
    # terminado.
    #
    # No llamamos worker.stop() desde aquí porque
    # sería volver a cruzar threads incorrectamente.
    # =============================================

    serial_thread.wait(
        1500
    )

    sys.exit(
        exit_code
    )


if __name__ == "__main__":
    main()
