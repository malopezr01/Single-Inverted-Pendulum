import csv
import os
import threading
import time

from datetime import datetime

from serial_link import SerialLink
from realtime_plot import plot_experiment


SERIAL_PORT = '/dev/ttyACM0'
BAUDRATE = 115200

EXPERIMENTS_DIR = 'experiments'


# ============================================================
# CREAR ARCHIVO DE ENSAYO
# ============================================================

def create_experiment_file():

    os.makedirs(
        EXPERIMENTS_DIR,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        '%Y-%m-%d_%H-%M-%S'
    )

    filename = os.path.join(
        EXPERIMENTS_DIR,
        f'experiment_{timestamp}.csv'
    )

    return filename


# ============================================================
# HILO DE TECLADO
# ============================================================

def keyboard_thread(
    serial_link,
    state
):

    while not state["quit"]:

        command = input().strip().upper()

        # ====================================================
        # START
        # ====================================================

        if command == "R":

            if not state["running"]:

                # Limpiar cualquier telemetría antigua
                serial_link.ser.reset_input_buffer()

                serial_link.send_command(
                    "R"
                )

                state["running"] = True

                print()
                print(
                    ">>> R enviada al ESP32"
                )

                print(
                    ">>> Experimento iniciado"
                )

                print()

        # ====================================================
        # STOP
        # ====================================================

        elif command == "S":

            if state["running"]:

                serial_link.send_command(
                    "S"
                )

                state["running"] = False
                state["finished"] = True

                print()
                print(
                    ">>> S enviada al ESP32"
                )

                print(
                    ">>> Experimento detenido"
                )

                print()

        # ====================================================
        # QUIT
        # ====================================================

        elif command == "Q":

            if state["running"]:

                serial_link.send_command(
                    "S"
                )

            state["running"] = False
            state["quit"] = True


# ============================================================
# MAIN
# ============================================================

def main():

    # ========================================================
    # ABRIR SERIAL
    # ========================================================

    serial_link = SerialLink(
        port=SERIAL_PORT,
        baudrate=BAUDRATE
    )

    # ========================================================
    # CREAR ARCHIVO
    # ========================================================

    csv_filename = create_experiment_file()

    # ========================================================
    # ESTADO
    # ========================================================

    state = {
        "running": False,
        "finished": False,
        "quit": False
    }

    # ========================================================
    # INTERFAZ
    # ========================================================

    print()
    print(
        "======================================"
    )

    print(
        " SIMPLE INVERTED PENDULUM"
    )

    print(
        "======================================"
    )

    print()

    print(
        "R + ENTER -> iniciar experimento"
    )

    print(
        "S + ENTER -> detener y graficar"
    )

    print(
        "Q + ENTER -> salir"
    )

    print()

    print(
        f"Datos: {csv_filename}"
    )

    print()

    # ========================================================
    # HILO DE TECLADO
    # ========================================================

    thread = threading.Thread(
        target=keyboard_thread,
        args=(
            serial_link,
            state
        ),
        daemon=True
    )

    thread.start()

    # ========================================================
    # CONTADORES
    # ========================================================

    sample_counter = 0

    last_status_time = (
        time.perf_counter()
    )

    last_esp_time = None

    # ========================================================
    # ADQUISICIÓN
    # ========================================================

    try:

        with open(
            csv_filename,
            'w',
            newline='',
            buffering=8192
        ) as csv_file:

            writer = csv.writer(
                csv_file
            )

            # =================================================
            # CABECERA CSV
            # =================================================

            writer.writerow([
                'Time',
                'theta',
                'thetaDot',
                'x',
                'xDotObs',
                'xDotXActual',
                'u'
            ])

            # =================================================
            # BUCLE PRINCIPAL
            # =================================================

            while not state["quit"]:

                # ---------------------------------------------
                # Ensayo terminado
                # ---------------------------------------------

                if state["finished"]:
                    break

                # ---------------------------------------------
                # Esperando R
                # ---------------------------------------------

                if not state["running"]:

                    time.sleep(
                        0.01
                    )

                    continue

                # ---------------------------------------------
                # Leer ESP32
                # ---------------------------------------------

                data = serial_link.read_packet()

                if data is None:
                    continue

                # ---------------------------------------------
                # Guardar CSV
                # ---------------------------------------------

                writer.writerow([
                    data['Time'],
                    data['theta'],
                    data['thetaDot'],
                    data['x'],
                    data['xDotObs'],
                    data['xDotXActual'],
                    data['u']
                ])

                sample_counter += 1

                # ---------------------------------------------
                # Detectar saltos temporales
                # ---------------------------------------------

                if last_esp_time is not None:

                    dt = (
                        data['Time']
                        - last_esp_time
                    )

                    if dt < 0:

                        print()
                        print(
                            f"AVISO: Time retrocede "
                            f"{last_esp_time:.4f} "
                            f"-> {data['Time']:.4f}"
                        )

                last_esp_time = (
                    data['Time']
                )

                # ---------------------------------------------
                # Estado una vez por segundo
                # ---------------------------------------------

                now = (
                    time.perf_counter()
                )

                if (
                    now
                    - last_status_time
                    >= 1.0
                ):

                    print(
                        f"\r"
                        f"Recibiendo... "
                        f"t={data['Time']:.4f} s | "
                        f"muestras={sample_counter}",
                        end='',
                        flush=True
                    )

                    last_status_time = now

            # =================================================
            # FORZAR ESCRITURA FINAL
            # =================================================

            csv_file.flush()

    # ========================================================
    # CTRL+C
    # ========================================================

    except KeyboardInterrupt:

        print()
        print()

        if state["running"]:

            serial_link.send_command(
                "S"
            )

        print(
            "Ctrl+C detectado."
        )

    # ========================================================
    # CIERRE SERIAL
    # ========================================================

    finally:

        serial_link.close()

    # ========================================================
    # RESULTADO
    # ========================================================

    print()
    print()

    print(
        f"Ensayo guardado: "
        f"{csv_filename}"
    )

    print(
        f"Muestras recibidas: "
        f"{sample_counter}"
    )

    # ========================================================
    # GRAFICAR
    # ========================================================

    if sample_counter > 0:

        print()
        print(
            "Generando gráficas..."
        )

        plot_experiment(
            csv_filename
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == '__main__':
    main()
