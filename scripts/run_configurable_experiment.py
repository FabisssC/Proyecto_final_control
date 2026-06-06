import argparse
import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from AReS.utils.enums import DisturbanceType
from control_anestesia.scenarios.closed_loop_pid_observer import run_pid_observer

FIG_W = 6.0
FIG_H = 1.4
FIG_H_DOBLE = FIG_H * 1.4  # para residuos (2 subplots)

def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def resolve_patient_profile(patient_cfg):
    """
    Devuelve el patient_profile a pasar a run_pid_observer y el ares_patient_id.
    """
    if patient_cfg is None:
        return None, None

    mode = patient_cfg.get("mode", "demographic")

    if mode == "demographic":
        return None, patient_cfg.get("ares_patient_id", 0)

    if mode == "profile":
        profiles_file = Path(patient_cfg["profiles_file"])
        profile_key = patient_cfg["profile_key"]
        profiles = json.loads(profiles_file.read_text(encoding="utf-8"))

        if profile_key not in profiles:
            raise ValueError(f"Perfil '{profile_key}' no encontrado en {profiles_file}")

        profile = profiles[profile_key]
        ares_id = profile.get("ares_patient_id") or 0
        return profile, ares_id

    raise ValueError(f"Modo de paciente no reconocido: {mode}")

def build_stimuli(stimuli_cfg):
    if not stimuli_cfg.get("enabled", False):
        return None

    profile = stimuli_cfg.get("profile", "default_ares")

    if profile == "default_ares":
        return {
            600: (DisturbanceType.INTUBATION, 120, [10, 10, 20]),
            1200: (DisturbanceType.INCISION, 120, [50, 50, 70]),
            2100: (DisturbanceType.SKIN_MANIPULATION, 600, [15, 15, 10]),
            3000: (DisturbanceType.SUTURE, 300, [2, 2, 4]),
        }

    raise ValueError(f"Perfil de estímulos no reconocido: {profile}")


def make_output_dir(config):
    scenario_name = config["scenario_name"]
    base_dir = Path(config["output"].get("base_dir", "outputs/runs"))

    use_hardware = config["hardware"].get("use_hardware", False)
    mode_dir = "hardware_py" if use_hardware else "simulation_py"

    out_dir = base_dir / mode_dir / scenario_name
    out_dir.mkdir(parents=True, exist_ok=True)

    return out_dir


def save_config(config, out_dir):
    config_path = out_dir / "config_used.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def save_figure(fig, out_dir, label_p, escenario, nombre_señal, save_pdf=True):
    stem = f"F_{label_p}_{nombre_señal}_{escenario}_py"
    fig.savefig(out_dir / f"{stem}.pdf", bbox_inches="tight")


def configure_plot_style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 8,
        "axes.labelsize": 9,
        "axes.titlesize": 9,
        "legend.fontsize": 7,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "lines.linewidth": 1.8,
        "axes.grid": True,
        "grid.alpha": 0.35,
    })


def plot_bis(df, out_dir, label_p, escenario, save_pdf=True):
    # Tamaño estándar en pulgadas — igual que MATLAB PW=6, PH=1.8
    t = df["time_min"]

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.plot(t, df["BIS_mas"], "r--", label=r"$BIS^{+}$")
    ax.plot(t, df["BIS"], "k", label="BIS")
    ax.plot(t, df["BIS_menos"], "b--", label=r"$BIS^{-}$")

    ax.set_xlabel("Time [min]")
    ax.set_ylabel("BIS")
    ax.set_title("BIS real y bandas estimadas")
    ax.legend(loc="best", framealpha=1.0)
    ax.set_ylim(40, 100)

    save_figure(fig, out_dir, label_p, escenario, "BIS", save_pdf)
    return fig


def plot_ce_prop(df, out_dir, label_p, escenario, save_pdf=True):
    t = df["time_min"]
    ce_prom = 0.5 * (df["Ce_prop_mas"] + df["Ce_prop_menos"])

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.plot(t, df["Ce_prop_mas"], "r--", label=r"$Ce_p^{+}$")
    ax.plot(t, df["Ce_prop_obs"], "k", label=r"$\overline{Ce_p}$")
    ax.plot(t, df["Ce_prop_menos"], "b--", label=r"$Ce_p^{-}$")
    ax.plot(t, df["Ce_prop"], "k:", label=r"$Ce_p$ real")

    ax.set_xlabel("Time [min]")
    ax.set_ylabel(r"$Ce_p$")
    ax.set_title("Concentración de propofol en sitio de efecto")
    ax.legend(loc="best", framealpha=1.0)

    save_figure(fig, out_dir, label_p, escenario, "yp", save_pdf)
    return fig


def plot_ce_remi(df, out_dir, label_p, escenario, save_pdf=True):
    t = df["time_min"]
    ce_prom = 0.5 * (df["Ce_remi_mas"] + df["Ce_remi_menos"])

    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.plot(t, df["Ce_remi_mas"], "r--", label=r"$Ce_r^{+}$")
    ax.plot(t, df["Ce_remi_obs"], "k", label=r"$\overline{Ce_r}$")
    ax.plot(t, df["Ce_remi_menos"], "b--", label=r"$Ce_r^{-}$")
    ax.plot(t, df["Ce_remi"], "k:", label=r"$Ce_r$ real")

    ax.set_xlabel("Time [min]")
    ax.set_ylabel(r"$Ce_r$")
    ax.set_title("Concentración de remifentanilo en sitio de efecto")
    ax.legend(loc="best", framealpha=1.0)

    save_figure(fig, out_dir, label_p, escenario, "yr", save_pdf)
    return fig


def plot_rates_prop(df, out_dir, save_pdf=True):
    t = df["time_min"]

    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(t, df["u_prop_cmd"], "r--", label=r"$u_{p,cmd}$")
    ax.plot(t, df["u_prop_app"], "r", label=r"$u_{p,app}$")

    ax.set_xlabel("Time [min]")
    ax.set_ylabel(r"$u_p$ [mg/s]")
    ax.set_title("Propofol comandado vs aplicado")
    ax.legend(loc="best", framealpha=1.0)

    save_figure(fig, out_dir, "U_prop_cmd_app", save_pdf)
    return fig


def plot_rates_remi(df, out_dir, save_pdf=True):
    t = df["time_min"]

    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(t, df["u_remi_cmd"], "b--", label=r"$u_{r,cmd}$")
    ax.plot(t, df["u_remi_app"], "b", label=r"$u_{r,app}$")

    ax.set_xlabel("Time [min]")
    ax.set_ylabel(r"$u_r$ [$\mu$g/s]")
    ax.set_title("Remifentanilo comandado vs aplicado")
    ax.legend(loc="best", framealpha=1.0)

    save_figure(fig, out_dir, "U_remi_cmd_app", save_pdf)
    return fig


def plot_rates_combined(df, out_dir, label_p, escenario, save_pdf=True):
    t = df["time_min"]

    fig, ax1 = plt.subplots(figsize=(FIG_W, FIG_H))

    ax1.plot(t, df["u_prop_app"], "r", label=r"$u_p$")
    ax1.set_xlabel("Time [min]")
    ax1.set_ylabel(r"$u_p$ [mg/s]", color="r")
    ax1.tick_params(axis="y", labelcolor="r")

    ax2 = ax1.twinx()
    ax2.plot(t, df["u_remi_app"], "b", label=r"$u_r$")
    ax2.set_ylabel(r"$u_r$ [$\mu$g/s]", color="b")
    ax2.tick_params(axis="y", labelcolor="b")

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc="best", framealpha=1.0)

    ax1.set_title("Tasas de infusión aplicadas")

    save_figure(fig, out_dir, label_p, escenario, "U", save_pdf)
    return fig


def plot_residuals_combined(df, out_dir, label_p, escenario, save_pdf=True):
    fig, axes = plt.subplots(2, 1, figsize=(FIG_W, FIG_H_DOBLE), sharex=True)
    # subplot 1
    axes[0].plot(df["time_min"], df["r_prop_sup"], "r", label=r"$R_p^{+}$")
    axes[0].plot(df["time_min"], df["r_prop_inf"], "b", label=r"$R_p^{-}$")
    axes[0].axhline(0.0, color="k", linewidth=1.0)
    axes[0].set_ylabel(r"$R_p$")
    axes[0].legend(loc="best", framealpha=1.0)
    # subplot 2
    axes[1].plot(df["time_min"], df["r_remi_sup"], "r", label=r"$R_r^{+}$")
    axes[1].plot(df["time_min"], df["r_remi_inf"], "b", label=r"$R_r^{-}$")
    axes[1].axhline(0.0, color="k", linewidth=1.0)
    axes[1].set_ylabel(r"$R_r$")
    axes[1].set_xlabel("Time [min]")
    axes[1].legend(loc="best", framealpha=1.0)
    save_figure(fig, out_dir, label_p, escenario, "R", save_pdf)


def plot_fault_flags(df, out_dir, label_p, escenario, save_pdf=True):
    t = df["time_min"]
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    ax.step(t, df["falla_prop_inyectada"].astype(int), "r--", where="post",
            label="Falla propofol inyectada")
    ax.step(t, df["fallo_prop"].astype(int), "r", where="post",
            label="Falla propofol detectada")
    ax.step(t, df["falla_remi_inyectada"].astype(int), "b--", where="post",
            label="Falla remifentanilo inyectada")
    ax.step(t, df["fallo_remi"].astype(int), "b", where="post",
            label="Falla remifentanilo detectada")
    ax.set_xlabel("Time [min]")
    ax.set_ylabel("Estado lógico")
    ax.set_yticks([0, 1])
    ax.set_ylim(-0.1, 1.1)
    ax.legend(loc="best", framealpha=1.0)
    save_figure(fig, out_dir, label_p, escenario, "Fallas", save_pdf)
    return fig


def run_experiment(config):
    configure_plot_style()
    # Extraer label del paciente y escenario del JSON
    patient_cfg = config.get("patient", {})
    label_p = patient_cfg.get("label_p", "P0")     
    escenario = config.get("escenario", "S1")
    out_dir = make_output_dir(config)
    save_config(config, out_dir)

    sim_cfg = config["simulation"]
    ctrl_cfg = config["controller"]
    obs_cfg = config["observer"]
    fault_cfg = config["fault"]
    hw_cfg = config["hardware"]
    out_cfg = config["output"]

    patient_profile, ares_id = resolve_patient_profile(
        config.get("patient", {"mode": "demographic",
                               "ares_patient_id": sim_cfg.get("paciente", 0)})
    )
      
    stimuli = build_stimuli(config["stimuli"])

    df = run_pid_observer(
        Ts_s=sim_cfg["Ts_s"],
        duracion_min=sim_cfg["duracion_min"],
        paciente=ares_id,
        stimuli=stimuli,
        patient_profile=patient_profile,

        fault_enabled=fault_cfg["fault_enabled"],
        fault_drug=fault_cfg["fault_drug"],
        fault_start_min=fault_cfg["fault_start_min"],
        fault_factor=fault_cfg["fault_factor"],

        use_hardware=hw_cfg["use_hardware"],
        hardware_port=hw_cfg["hardware_port"],

        observer_measurement_mode=obs_cfg.get("observer_measurement_mode", "bis_inverse"),
        detector_epsilon=obs_cfg.get("detector_epsilon", 0.3),
        detector_enable_time_min=obs_cfg.get("detector_enable_time_min", 10.0),
        
        x_lower_0=obs_cfg.get("x_lower_0", None),
        x_upper_0=obs_cfg.get("x_upper_0", None),
        w_lower=obs_cfg.get("w_lower", None),
        w_upper=obs_cfg.get("w_upper", None),
        
        BIS_ref=ctrl_cfg["BIS_ref"],
        ratio=ctrl_cfg["ratio"],
        Kp=ctrl_cfg["Kp"],
        Ki=ctrl_cfg["Ki"],
        Kd=ctrl_cfg["Kd"],
        u_prop_min=ctrl_cfg["u_prop_min"],
        u_prop_max=ctrl_cfg["u_prop_max"],
        u_remi_min=ctrl_cfg["u_remi_min"],
        u_remi_max=ctrl_cfg["u_remi_max"],
    )

    csv_path = out_dir / "results_python.csv"
    df.to_csv(csv_path, index=False)

    save_pdf = out_cfg.get("save_pdf", True)

    plot_bis(df, out_dir, label_p, escenario, save_pdf=True)
    plot_ce_prop(df, out_dir, label_p, escenario, save_pdf=True)
    plot_ce_remi(df, out_dir, label_p, escenario, save_pdf=True)
    plot_rates_combined(df, out_dir, label_p, escenario, save_pdf=True)
    plot_residuals_combined(df, out_dir, label_p, escenario, save_pdf=True)
    plot_fault_flags(df, out_dir, label_p, escenario, save_pdf)

    print(f"\nResultados guardados en:\n{out_dir}")
    print(f"\nCSV:\n{csv_path}")

    if out_cfg.get("show_figures", True):
        plt.show()
    else:
        plt.close("all")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default="configs/experimento_pid_observer_py.json",
        help="Ruta del archivo de configuración JSON.",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    run_experiment(config)


if __name__ == "__main__":
    main()