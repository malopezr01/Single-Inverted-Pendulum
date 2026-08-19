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


def keyboard_thread(
    serial_link,
    state
):

    while not state["quit"]:

        command = input().strip().upper()

        if command == "R":

            if not state["running"]:

                serial_link.send_command("R")
                state["running"] = True

                print()
                print(">>> R enviada al ESP32")
                print(">>> Experimento iniciado")
                print()

        elif command == "S":

            if state["running"]:

                serial_link.send_command("S")

                state["running"] = False
                state["finished"] = True

                print()
                print(">>> S enviada al ESP32")
                print(">>> Experimento detenido")
                print()

        elif command == "X":

            serial_link.send_command("X")

            state["running"] = False
            state["finished"] = True

            print()
            print(">>> EMERGENCY STOP enviado")
            print()

        elif command == "Q":

            if state["running"]:
                serial_link.send_command("S")

            state["running"] = False
            state["quit"] = True


def main():

    serial_link = SerialLink(
        port=SERIAL_PORT,
        baudrate=BAUDRATE
    )

    csv_filename = create_experiment_file()

    state = {
        "running": False,
        "finished": False,
        "quit": False
    }

    print()
    print("======================================")
    print(" SIMPLE INVERTED PENDULUM")
    print("======================================")
    print()
    print("R + ENTER -> iniciar experimento")
    print("S + ENTER -> detener y graficar")
    print("X + ENTER -> emergency stop")
    print("Q + ENTER -> salir")
    print()
    print(f"Datos: {csv_filename}")
    print()

    thread = threading.Thread(
        target=keyboard_thread,
        args=(
            serial_link,
            state
        ),
        daemon=True
    )

    thread.start()

    sample_counter = 0
    last_status_time = time.perf_counter()
    last_esp_time = None

    try:

        with open(
            csv_filename,
            'w',
            newline='',
            buffering=8192
        ) as csv_file:

            writer = csv.writer(csv_file)

            writer.writerow([
                'Time',
                'theta',
                'thetaDot',
                'x',
                'xDotObs',
                'xDotXActual',
                'u',
                'state',
                'mode'
            ])

            while not state["quit"]:

                if state["finished"]:
                    break

                message_type, data = serial_link.read_message()

                if message_type is None:
                    continue

                if message_type == 'message':
                    print(f"\nESP32: {data}")
                    continue

                if message_type != 'telemetry':
                    continue

                if not state["running"]:
                    continue

                writer.writerow([
                    data['Time'],
                    data['theta'],
                    data['thetaDot'],
                    data['x'],
                    data['xDotObs'],
                    data['xDotXActual'],
                    data['u'],
                    data['state'],
                    data['mode']
                ])

                sample_counter += 1

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

                last_esp_time = data['Time']

                now = time.perf_counter()

                if (
                    now
                    - last_status_time
                    >= 1.0
                ):

                    print(
                        f"\r"
                        f"Recibiendo... "
                        f"t={data['Time']:.4f} s | "
                        f"state={data['state']} | "
                        f"mode={data['mode']} | "
                        f"muestras={sample_counter}",
                        end='',
                        flush=True
                    )

                    last_status_time = now

            csv_file.flush()

    except KeyboardInterrupt:

        print()
        print()

        if state["running"]:
            serial_link.send_command("S")

        print("Ctrl+C detectado.")

    finally:
        serial_link.close()

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

    if sample_counter > 0:

        print()
        print("Generando gráficas...")

        plot_experiment(
            csv_filename
        )


if __name__ == '__main__':
    main()
