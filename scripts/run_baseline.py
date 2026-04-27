from control_anestesia.models.plant import planta_ares
from control_anestesia.scenarios.baseline_no_disturbance import escenario_base
from control_anestesia.visualization.plots import plot_baseline


def main():
    Ts_s = 5
    h_min = Ts_s / 60
    duracion_min = 60
    paciente = 0

    u_prop, u_remi = escenario_base(
        Ts_s=Ts_s,
        duracion_min=duracion_min
    )

    result = planta_ares(
        u_prop=u_prop,
        u_remi=u_remi,
        paciente=paciente,
        Ts=Ts_s
    )

    df = result.data

    print("Simulación en lazo abierto terminada")
    print(f"Paciente: {paciente}")
    print(f"Ts = {Ts_s} s")
    print(f"h = {h_min:.4f} min")
    print(f"Duración = {duracion_min} min")
    print(df.head())

    plot_baseline(df)


if __name__ == "__main__":
    main()