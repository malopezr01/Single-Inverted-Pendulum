import csv

import matplotlib

# La aplicación principal utiliza Qt/PySide6.
matplotlib.use("QtAgg")

import matplotlib.pyplot as plt


def plot_experiment(
    filename,
    block=False,
):
    """
    Genera las gráficas finales de un experimento.

    Mantiene el mismo formato CSV del programa
    original y utiliza Time enviado por el ESP32
    como eje temporal.

    Parameters
    ----------
    filename : str
        Ruta del CSV del experimento.

    block : bool
        Si True, plt.show() bloquea.
        En la GUI normalmente usamos False.
    """

    time_data = []

    theta = []
    theta_dot = []

    x = []

    x_dot_obs = []
    x_dot_xactual = []

    u = []

    state = []
    mode = []

    try:

        with open(
            filename,
            "r",
        ) as csv_file:

            reader = csv.DictReader(
                csv_file
            )

            for row in reader:

                time_data.append(
                    float(
                        row["Time"]
                    )
                )

                theta.append(
                    float(
                        row["theta"]
                    )
                )

                theta_dot.append(
                    float(
                        row["thetaDot"]
                    )
                )

                x.append(
                    float(
                        row["x"]
                    )
                )

                x_dot_obs.append(
                    float(
                        row["xDotObs"]
                    )
                )

                x_dot_xactual.append(
                    float(
                        row["xDotXActual"]
                    )
                )

                u.append(
                    float(
                        row["u"]
                    )
                )

                state.append(
                    int(
                        float(
                            row["state"]
                        )
                    )
                )

                mode.append(
                    int(
                        float(
                            row["mode"]
                        )
                    )
                )

    except Exception as exc:

        print(
            f"Error leyendo CSV: {exc}"
        )

        return

    if len(time_data) == 0:

        print(
            "No hay datos para graficar."
        )

        return

    print(
        f"Graficando "
        f"{len(time_data)} muestras..."
    )

    # -------------------------------------------------
    # Pendulum
    # -------------------------------------------------

    plt.figure(
        "Pendulum state"
    )

    plt.plot(
        time_data,
        theta,
        label="theta [rad]",
    )

    plt.plot(
        time_data,
        theta_dot,
        label="thetaDot [rad/s]",
    )

    plt.xlabel(
        "Time [s]"
    )

    plt.ylabel(
        "Pendulum state"
    )

    plt.title(
        "Pendulum angle and angular velocity"
    )

    plt.grid(
        True
    )

    plt.legend()

    # -------------------------------------------------
    # Cart position
    # -------------------------------------------------

    plt.figure(
        "Cart position"
    )

    plt.plot(
        time_data,
        x,
        label="x [m]",
    )

    plt.xlabel(
        "Time [s]"
    )

    plt.ylabel(
        "Position [m]"
    )

    plt.title(
        "Cart position"
    )

    plt.grid(
        True
    )

    plt.legend()

    # -------------------------------------------------
    # Cart velocity
    # -------------------------------------------------

    plt.figure(
        "Cart velocity"
    )

    plt.plot(
        time_data,
        x_dot_obs,
        label="xDotObs [m/s]",
    )

    plt.plot(
        time_data,
        x_dot_xactual,
        label="xDotXActual [m/s]",
    )

    plt.xlabel(
        "Time [s]"
    )

    plt.ylabel(
        "Velocity [m/s]"
    )

    plt.title(
        "Cart velocity comparison"
    )

    plt.grid(
        True
    )

    plt.legend()

    # -------------------------------------------------
    # Control action
    # -------------------------------------------------

    plt.figure(
        "Control action"
    )

    plt.plot(
        time_data,
        u,
        label="u [m/s²]",
    )

    plt.xlabel(
        "Time [s]"
    )

    plt.ylabel(
        "Control acceleration [m/s²]"
    )

    plt.title(
        "Control action"
    )

    plt.grid(
        True
    )

    plt.legend()

    # -------------------------------------------------
    # System state / control mode
    # -------------------------------------------------

    plt.figure(
        "System state"
    )

    plt.step(
        time_data,
        state,
        where="post",
        label="SystemState",
    )

    plt.step(
        time_data,
        mode,
        where="post",
        label="ControlMode",
    )

    plt.xlabel(
        "Time [s]"
    )

    plt.ylabel(
        "State / Mode"
    )

    plt.title(
        "System state and control mode"
    )

    plt.grid(
        True
    )

    plt.legend()

    plt.show(
        block=block
    )
