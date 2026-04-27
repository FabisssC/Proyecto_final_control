import matplotlib.pyplot as plt


def plot_baseline(df):
    t_min = df["time_s"] / 60.0

    plt.figure()
    plt.plot(t_min, df["BIS"])
    plt.xlabel("Tiempo [min]")
    plt.ylabel("BIS")
    plt.title("Respuesta BIS")
    plt.grid(True)

    plt.figure()
    plt.plot(t_min, df["Ce_prop"], label="Ce_prop")
    plt.plot(t_min, df["Ce_remi"], label="Ce_remi")
    plt.xlabel("Tiempo [min]")
    plt.ylabel("Concentración en sitio de efecto")
    plt.title("Concentraciones en sitio de efecto")
    plt.legend()
    plt.grid(True)




    if "Cp_prop" in df.columns and "Cp_remi" in df.columns:
        plt.figure()
        plt.plot(t_min, df["Cp_prop"], label="Cp_prop")
        plt.plot(t_min, df["Cp_remi"], label="Cp_remi")
        plt.xlabel("Tiempo [min]")
        plt.ylabel("Concentración plasmática")
        plt.title("Concentraciones plasmáticas")
        plt.legend()
        plt.grid(True)

    plt.figure()
    plt.plot(t_min, df["u_prop"])
    plt.xlabel("Tiempo [min]")
    plt.ylabel("u_prop [mg/s]")
    plt.title("Infusión de propofol aplicada")
    plt.grid(True)

    plt.figure()
    plt.plot(t_min, df["u_remi"])
    plt.xlabel("Tiempo [min]")
    plt.ylabel("u_remi [µg/s]")
    plt.title("Infusión de remifentanilo aplicada")
    plt.grid(True)

    plt.show()