import csv

import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt


def plot_experiment(filename):

    time_data = []

    theta = []
    theta_dot = []

    x = []

    x_dot_obs = []
    x_dot_xactual = []

    u = []

    # ========================================================
    # CARGAR CSV
    # ========================================================

    with open(
        filename,
        'r'
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        for row in reader:

            time_data.append(
                float(row['Time'])
            )

            theta.append(
                float(row['theta'])
            )

            theta_dot.append(
                float(row['thetaDot'])
            )

            x.append(
                float(row['x'])
            )

            x_dot_obs.append(
                float(row['xDotObs'])
            )

            x_dot_xactual.append(
                float(row['xDotXActual'])
            )

            u.append(
                float(row['u'])
            )

    # ========================================================
    # COMPROBAR DATOS
    # ========================================================

    if len(time_data) == 0:

        print(
            "No hay datos para graficar."
        )

        return

    print(
        f"Graficando {len(time_data)} muestras..."
    )

    # ========================================================
    # 1. PÉNDULO
    # ========================================================

    plt.figure()

    plt.plot(
        time_data,
        theta,
        label='theta [rad]'
    )

    plt.plot(
        time_data,
        theta_dot,
        label='thetaDot [rad/s]'
    )

    plt.xlabel(
        'Time [s]'
    )

    plt.ylabel(
        'Pendulum state'
    )

    plt.title(
        'Pendulum angle and angular velocity'
    )

    plt.grid(True)
    plt.legend()

    # ========================================================
    # 2. POSICIÓN DEL CARRO
    # ========================================================

    plt.figure()

    plt.plot(
        time_data,
        x,
        label='x [m]'
    )

    plt.xlabel(
        'Time [s]'
    )

    plt.ylabel(
        'Position [m]'
    )

    plt.title(
        'Cart position'
    )

    plt.grid(True)
    plt.legend()

    # ========================================================
    # 3. VELOCIDAD DEL CARRO
    # ========================================================

    plt.figure()

    plt.plot(
        time_data,
        x_dot_obs,
        label='xDotObs [m/s]'
    )

    plt.plot(
        time_data,
        x_dot_xactual,
        label='xDotXActual [m/s]'
    )

    plt.xlabel(
        'Time [s]'
    )

    plt.ylabel(
        'Velocity [m/s]'
    )

    plt.title(
        'Cart velocity comparison'
    )

    plt.grid(True)
    plt.legend()

    # ========================================================
    # 4. CONTROL
    # ========================================================

    plt.figure()

    plt.plot(
        time_data,
        u,
        label='u [m/s²]'
    )

    plt.xlabel(
        'Time [s]'
    )

    plt.ylabel(
        'Control acceleration [m/s²]'
    )

    plt.title(
        'Control action'
    )

    plt.grid(True)
    plt.legend()

    # ========================================================
    # MOSTRAR TODAS LAS FIGURAS
    # ========================================================

    plt.show()
