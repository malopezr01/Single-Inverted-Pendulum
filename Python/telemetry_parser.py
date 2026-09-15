class TelemetryParser:
    """
    Parser dinámico del protocolo de telemetría.

    Protocolo ESP32 -> PC:

        HEADER,Time,theta,thetaDot,x,u,state
        DATA,0.010,0.002,-0.13,0.001,0.4,3
        MSG,READY
        EVENT,BALANCEUP
        ERROR,Pendulo fuera de rango

    El parser no conoce de antemano ninguna señal.
    Los nombres y el orden los define HEADER.

    Durante la migración también acepta la telemetría
    antigua basada en pares key=value.
    """

    def __init__(self):
        self.signal_names = []
        self.header_received = False

    def reset(self):
        """Olvida el HEADER conocido al iniciar una conexión nueva."""
        self.signal_names = []
        self.header_received = False

    def parse(self, line):
        """
        Analiza una línea recibida del ESP32.

        Devuelve una tupla (tipo, payload):

            ("header", list[str])
            ("data", dict)
            ("message", str)
            ("event", str)
            ("error", str)
            ("protocol_error", str)
            (None, None)
        """
        line = line.strip()

        if not line:
            return None, None

        if line.startswith("HEADER,"):
            return self._parse_header(line)

        if line.startswith("DATA,"):
            return self._parse_data(line)

        if line.startswith("MSG,"):
            return "message", line[4:]

        if line.startswith("EVENT,"):
            return "event", line[6:]

        if line.startswith("ERROR,"):
            return "error", line[6:]

        legacy_data = self._parse_legacy_key_value(line)
        if legacy_data is not None:
            return "data", legacy_data

        return "message", line

    def _parse_header(self, line):
        fields = line.split(",")
        signal_names = [field.strip() for field in fields[1:]]

        if not signal_names or any(not name for name in signal_names):
            return "protocol_error", "HEADER inválido: nombre de señal vacío."

        if len(signal_names) != len(set(signal_names)):
            return "protocol_error", "HEADER inválido: señales duplicadas."

        self.signal_names = signal_names
        self.header_received = True

        return "header", self.signal_names.copy()

    def _parse_data(self, line):
        # Al conectarnos a un ESP32 que ya estaba funcionando podemos
        # empezar a recibir DATA antes de ver su siguiente HEADER.
        # No es un fallo de protocolo útil para el usuario: simplemente
        # esperamos al HEADER y descartamos esas muestras iniciales.
        if not self.header_received:
            return None, None

        raw_values = line.split(",")[1:]

        if len(raw_values) != len(self.signal_names):
            return (
                "protocol_error",
                (
                    "DATA no coincide con HEADER: "
                    f"{len(raw_values)} valores recibidos, "
                    f"{len(self.signal_names)} esperados."
                ),
            )

        values = {}

        try:
            for signal_name, raw_value in zip(self.signal_names, raw_values):
                values[signal_name] = self._parse_number(raw_value)
        except ValueError as exc:
            return "protocol_error", f"Valor DATA no numérico: {exc}"

        return "data", values

    @staticmethod
    def _parse_number(value):
        """
        Convierte automáticamente enteros y flotantes sin
        depender del nombre de la señal.
        """
        value = value.strip()

        try:
            return int(value)
        except ValueError:
            return float(value)

    @staticmethod
    def _parse_legacy_key_value(line):
        """
        Compatibilidad con el formato anterior.

        No exige una lista fija de campos: cualquier línea
        compuesta únicamente por pares key=value numéricos se
        convierte dinámicamente en un diccionario.
        """
        fields = line.split()

        if not fields or not all("=" in field for field in fields):
            return None

        values = {}

        try:
            for field in fields:
                key, raw_value = field.split("=", 1)
                key = key.strip()

                if not key:
                    return None

                values[key] = TelemetryParser._parse_number(raw_value)
        except (ValueError, TypeError):
            return None

        return values
