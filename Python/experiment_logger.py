import csv
import os

from datetime import datetime


CSV_HEADER = [
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


class ExperimentLogger:
    """
    Gestiona exclusivamente el almacenamiento
    de telemetría de experimentos.

    El CSV mantiene exactamente el mismo formato
    que el programa anterior.
    """

    def __init__(
        self,
        experiments_dir="experiments",
    ):
        self.experiments_dir = (
            experiments_dir
        )

        self.csv_file = None
        self.writer = None

        self.filename = None
        self.sample_count = 0

        self.active = False

    def _create_filename(self):

        os.makedirs(
            self.experiments_dir,
            exist_ok=True,
        )

        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        return os.path.join(
            self.experiments_dir,
            f"experiment_{timestamp}.csv",
        )

    def start(self):
        """
        Inicia un nuevo experimento.

        Este método debe llamarse únicamente cuando
        el ESP32 confirme realmente RUNNING.
        """

        if self.active:
            return self.filename

        self.filename = (
            self._create_filename()
        )

        self.csv_file = open(
            self.filename,
            "w",
            newline="",
            buffering=8192,
        )

        self.writer = csv.writer(
            self.csv_file
        )

        self.writer.writerow(
            CSV_HEADER
        )

        self.sample_count = 0

        self.active = True

        return self.filename

    def write(self, data):
        """
        Guarda una muestra de telemetría.
        """

        if not self.active:
            return

        self.writer.writerow([
            data["Time"],
            data["theta"],
            data["thetaDot"],
            data["x"],
            data["xDotObs"],
            data["xDotXActual"],
            data["u"],
            data["state"],
            data["mode"],
        ])

        self.sample_count += 1

        # Flush periódico para reducir la pérdida
        # de información ante un cierre inesperado.
        if self.sample_count % 50 == 0:
            self.csv_file.flush()

    def stop(self):
        """
        Finaliza el experimento.

        Devuelve:

            filename
            sample_count
        """

        if not self.active:

            return (
                self.filename,
                self.sample_count,
            )

        try:
            self.csv_file.flush()
        finally:
            self.csv_file.close()

        self.csv_file = None
        self.writer = None

        self.active = False

        return (
            self.filename,
            self.sample_count,
        )
