import matplotlib.pyplot as plt

from control_anestesia.scenarios.closed_loop_pid_observer import run_pid_observer
from AReS.utils.enums import DisturbanceType


stimuli = {
    60: (DisturbanceType.INTUBATION, 120, [1, 1, 2]),
    1200: (DisturbanceType.INCISION, 120, [100, 100, 20]),
    2100: (DisturbanceType.SKIN_MANIPULATION, 600, [5, 5, 10]),
    3000: (DisturbanceType.SUTURE, 300, [2, 2, 4]),
}

def main():
    df = run_pid_observer(

        Ts_s=5,
        duracion_min=60,
        paciente=0,
        stimuli=None,
        fault_enabled=True,
        fault_drug="prop",
        fault_start_min=30.0,
        fault_factor=0.7,
    )
    #df = run_pid_observer(
    #    Ts_s=5,
    #    duracion_min=60,
    #    paciente=0,
    #    stimuli=None,
    #    fault_enabled=True,
    #    fault_start_min=30,
    #    fault_factor=0.0,
    #)

    print(df.head())

    t = df["time_min"]

    plt.figure()
    plt.plot(t, df["BIS"], label="BIS AReS")
    plt.plot(t, df["BIS_ref"], "--", label="BIS ref")
    plt.plot(t, df["BIS_mas"], "--", label="BIS superior")
    plt.plot(t, df["BIS_menos"], "--", label="BIS inferior")
    plt.plot(t, df["BIS_desde_Ce_bis"], label="BIS desde Ce_bis")
    plt.xlabel("Tiempo [min]")
    plt.ylabel("BIS")
    plt.title("BIS real y bandas estimadas")
    plt.legend()
    plt.grid(True)

    plt.figure()
    plt.plot(t, df["Ce_bis"], label="Ce_bis AReS")
    plt.plot(t, df["Ce_bis_mas"], "--", label="Ce_bis superior")
    plt.plot(t, df["Ce_bis_menos"], "--", label="Ce_bis inferior")
    plt.xlabel("Tiempo [min]")
    plt.ylabel("Ce_bis")
    plt.title("Filtro BIS aplicado a las cotas de propofol")
    plt.legend()
    plt.grid(True)

    plt.figure()
    plt.plot(t, df["Ce_prop"], label="Ce_prop real")
    plt.plot(t, df["Ce_prop_mas"], "--", label="Ce_prop superior")
    plt.plot(t, df["Ce_prop_menos"], "--", label="Ce_prop inferior")
    plt.xlabel("Tiempo [min]")
    plt.ylabel("Ce_prop")
    plt.title("Observador por intervalo - Propofol")
    plt.legend()
    plt.grid(True)

    plt.figure()
    plt.plot(t, df["Ce_remi"], label="Ce_remi real")
    plt.plot(t, df["Ce_remi_mas"], "--", label="Ce_remi superior")
    plt.plot(t, df["Ce_remi_menos"], "--", label="Ce_remi inferior")
    plt.xlabel("Tiempo [min]")
    plt.ylabel("Ce_remi")
    plt.title("Observador por intervalo - Remifentanilo")
    plt.legend()
    plt.grid(True)

    plt.figure()
    plt.plot(t, df["fallo_prop"].astype(int), label="Fallo prop detectado")
    plt.plot(t, df["fallo_remi"].astype(int), label="Fallo remi detectado")
    plt.plot(t, df["falla_prop_inyectada"].astype(int), "--", label="Falla prop inyectada")
    plt.xlabel("Tiempo [min]")
    plt.ylabel("Estado lógico")
    plt.title("Detección de fallas")
    plt.legend()
    plt.grid(True)

    plt.figure()
    plt.plot(t, df["r_prop_sup"], label="r_prop_sup")
    plt.plot(t, df["r_prop_inf"], label="r_prop_inf")
    plt.plot(t, df["r_remi_sup"], label="r_remi_sup")
    plt.plot(t, df["r_remi_inf"], label="r_remi_inf")
    plt.axhline(0)
    plt.axvline(20, linestyle="--")
    plt.axhline(0)
    plt.xlabel("Tiempo [min]")
    plt.title("Residuos del sistema")
    plt.legend()
    plt.grid(True)


    plt.figure()
    plt.plot(t, df["u_prop_app"], label="u_prop aplicada [mg/s]")
    plt.plot(t, df["u_remi_app"], label="u_remi aplicada [µg/s]")
    plt.xlabel("Tiempo [min]")
    plt.ylabel("Tasa de infusión aplicada")
    plt.title("Entradas aplicadas a la planta")
    plt.legend()
    plt.grid(True)
    print(df[["BIS", "BIS_desde_Ce_real", "Ce_prop", "Ce_remi"]].tail(10))
    plt.show()


if __name__ == "__main__":
    main()