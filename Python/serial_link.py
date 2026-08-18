import serial
import time


class SerialLink:

    def __init__(
        self,
        port='/dev/ttyACM0',
        baudrate=115200,
        timeout=0.1
    ):

        self.ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=timeout
        )

        # El ESP32 puede resetearse al abrir el puerto
        time.sleep(2.0)

        self.ser.reset_input_buffer()

        print(
            f"Puerto serie abierto: "
            f"{port} @ {baudrate} baud"
        )

    def send_command(self, command):
        """
        Envía un carácter al ESP32.

        R -> iniciar
        S -> detener
        """

        self.ser.write(command.encode())
        self.ser.flush()

        print(
            f"Comando enviado al ESP32: {command}"
        )

    def read_packet(self):
        """
        Espera una línea de telemetría del tipo:

        Time=12.3456
        theta=0.0123
        thetaDot=-0.0456
        x=0.0345
        xDotObs=0.0678
        xDotXActual=0.0654
        u=0.1234

        Todo en una sola línea.

        Devuelve un diccionario con los valores,
        o None si la línea no es telemetría válida.
        """

        line = self.ser.readline()

        if not line:
            return None

        try:
            line = line.decode(
                'utf-8',
                errors='ignore'
            ).strip()

        except Exception:
            return None

        if not line:
            return None

        try:

            values = {}

            fields = line.split()

            for field in fields:

                if '=' not in field:
                    continue

                key, value = field.split('=', 1)

                values[key] = float(value)

            required_fields = [
                'Time',
                'theta',
                'thetaDot',
                'x',
                'xDotObs',
                'xDotXActual',
                'u'
            ]

            for field in required_fields:

                if field not in values:
                    return None

            return values

        except ValueError:
            return None

    def close(self):

        if self.ser.is_open:

            self.ser.close()

            print("Puerto serie cerrado.")
