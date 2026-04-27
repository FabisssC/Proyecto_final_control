from control_anestesia.scenarios.closed_loop_pid_ratio import run_pid_ratio
from control_anestesia.visualization.plots import plot_baseline


def main():
    df = run_pid_ratio(
        Ts_s=5,
        duracion_min=60,
        paciente=0
    )

    print(df.head())

    plot_baseline(df)


if __name__ == "__main__":
    main()