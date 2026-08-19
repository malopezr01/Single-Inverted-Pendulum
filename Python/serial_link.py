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

        # Limpiar cualquier byte residual previo al arranque.
        self.ser.reset_input_buffer()

        # El ESP32 puede resetearse al abrir el puerto.
        # Los mensajes enviados durante esta espera se conservan.
        time.sleep(2.0)

        print(
            f"Puerto serie abierto: "
            f"{port} @ {baudrate} baud"
        )

    def send_command(self, command):
        """
        Envía un carácter al ESP32.

        R -> iniciar
        S -> detener
        X -> emergency stop
        """

        self.ser.write(command.encode())
        self.ser.flush()

        print(
            f"Comando enviado al ESP32: {command}"
        )

    def read_message(self):
        """
        Lee una línea del puerto serie.

        Devuelve:
            ('telemetry', dict) si es una trama válida.
            ('message', str) para cualquier otro mensaje.
            (None, None) si no hay datos.
        """

        line = self.ser.readline()

        if not line:
            return None, None

        try:
            line = line.decode(
                'utf-8',
                errors='ignore'
            ).strip()
        except Exception:
            return None, None

        if not line:
            return None, None

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
                'u',
                'state',
                'mode'
            ]

            valid_telemetry = True

            for field in required_fields:
                if field not in values:
                    valid_telemetry = False
                    break

            if valid_telemetry:
                values['state'] = int(values['state'])
                values['mode'] = int(values['mode'])
                return 'telemetry', values

        except ValueError:
            pass

        return 'message', line

    def close(self):

        if self.ser.is_open:
            self.ser.close()
            print("Puerto serie cerrado.")
