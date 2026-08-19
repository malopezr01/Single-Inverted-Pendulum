import sys

from PySide6.QtCore import QThread

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
    # Serial thread startup
    # =============================================

    serial_thread.started.connect(
        serial_worker.start
    )

    serial_worker.finished.connect(
        serial_thread.quit
    )

    # =============================================
    # Serial -> GUI signals
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
    # Start
    # =============================================

    print("minimumSize:", window.minimumSize())
    print("minimumSizeHint:", window.minimumSizeHint())
    print("maximumSize:", window.maximumSize())
    print("sizeHint:", window.sizeHint())
    print("flags:", window.windowFlags())
    window.show()

    serial_thread.start()

    exit_code = app.exec()

    # =============================================
    # Final cleanup
    # =============================================

    try:

        serial_worker.stop(
            send_stop=False
        )

    except Exception:
        pass

    serial_thread.quit()

    serial_thread.wait(
        1500
    )

    sys.exit(
        exit_code
    )


if __name__ == "__main__":
    main()
