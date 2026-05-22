import argparse
import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from AReS.utils.enums import DisturbanceType
from control_anestesia.scenarios.closed_loop_pid_observer import run_pid_observer


def load_config(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"{scenario_name}_python_{timestamp}"

    out_dir = base_dir / mode_dir / run_name
    out_dir.mkdir(parents=True, exist_ok=True)

    return out_dir


def save_config(config, out_dir):
    config_path = out_dir / "config_used.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def save_figure(fig, out_dir, name, save_pdf=True):
    png_path = out_dir / f"{name}_python.png"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")

    if save_pdf:
        pdf_path = out_dir / f"{name}_python.pdf"
        fig.savefig(pdf_path, bbox_inches="tight")


def configure_plot_style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 12,
        "axes.labelsize": 13,
        "axes.titlesize": 13,
        "legend.fontsize": 11,
        "xtick.labelsize": 11,
        "ytick.labelsize": 11,
        "lines.linewidth": 1.8,
        "axes.grid": True,
        "grid.alpha": 0.35,
    })


def plot_bis(df, out_dir, save_pdf=True):
    t = df["time_min"]

    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(t, df["BIS_mas"], "r--", label=r"$BIS^{+}$")
    ax.plot(t, df["BIS"], "k", label="BIS")
    ax.plot(t, df["BIS_menos"], "b--", label=r"$BIS^{-}$")

    ax.set_xlabel("Time [min]")
    ax.set_ylabel("BIS")
    ax.set_title("BIS real y bandas estimadas")
    ax.legend(loc="best", framealpha=1.0)
    ax.set_ylim(40, 100)

    save_figure(fig, out_dir, "BIS_bandas", save_pdf)
    return fig


def plot_ce_prop(df, out_dir, save_pdf=True):
    t = df["time_min"]
    ce_prom = 0.5 * (df["Ce_prop_mas"] + df["Ce_prop_menos"])

    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(t, df["Ce_prop_mas"], "r--", label=r"$Ce_p^{+}$")
    ax.plot(t, df["Ce_prop_obs"], "k", label=r"$\overline{Ce_p}$")
    ax.plot(t, df["Ce_prop_menos"], "b--", label=r"$Ce_p^{-}$")
    ax.plot(t, df["Ce_prop"], "k:", label=r"$Ce_p$ real")

    ax.set_xlabel("Time [min]")
    ax.set_ylabel(r"$Ce_p$")
    ax.set_title("Concentración de propofol en sitio de efecto")
    ax.legend(loc="best", framealpha=1.0)

    save_figure(fig, out_dir, "Ce_prop_bandas", save_pdf)
    return fig


def plot_ce_remi(df, out_dir, save_pdf=True):
    t = df["time_min"]
    ce_prom = 0.5 * (df["Ce_remi_mas"] + df["Ce_remi_menos"])

    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.plot(t, df["Ce_remi_mas"], "r--", label=r"$Ce_r^{+}$")
    ax.plot(t, df["Ce_remi_obs"], "k", label=r"$\overline{Ce_r}$")
    ax.plot(t, df["Ce_remi_menos"], "b--", label=r"$Ce_r^{-}$")
    ax.plot(t, df["Ce_remi"], "k:", label=r"$Ce_r$ real")

    ax.set_xlabel("Time [min]")
    ax.set_ylabel(r"$Ce_r$")
    ax.set_title("Concentración de remifentanilo en sitio de efecto")
    ax.legend(loc="best", framealpha=1.0)

    save_figure(fig, out_dir, "Ce_remi_bandas", save_pdf)
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


def plot_rates_combined(df, out_dir, save_pdf=True):
    t = df["time_min"]

    fig, ax1 = plt.subplots(figsize=(8, 3.2))

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

    save_figure(fig, out_dir, "U_aplicadas_doble_eje", save_pdf)
    return fig


def plot_residuals_prop(df, out_dir, save_pdf=True):
    t = df["time_min"]

    fig, ax = plt.subplots(figsize=(8, 2.8))
    ax.plot(t, df["r_prop_sup"], "r", label=r"$R_p^{+}$")
    ax.plot(t, df["r_prop_inf"], "b", label=r"$R_p^{-}$")
    ax.axhline(0.0, color="k", linewidth=1.0)

    ax.set_xlabel("Time [min]")
    ax.set_ylabel(r"$R_p$")
    ax.set_title("Residuos del detector - Propofol")
    ax.legend(loc="best", framealpha=1.0)

    save_figure(fig, out_dir, "Residuos_propofol", save_pdf)
    return fig


def plot_residuals_remi(df, out_dir, save_pdf=True):
    t = df["time_min"]

    fig, ax = plt.subplots(figsize=(8, 2.8))
    ax.plot(t, df["r_remi_sup"], "r", label=r"$R_r^{+}$")
    ax.plot(t, df["r_remi_inf"], "b", label=r"$R_r^{-}$")
    ax.axhline(0.0, color="k", linewidth=1.0)

    ax.set_xlabel("Time [min]")
    ax.set_ylabel(r"$R_r$")
    ax.set_title("Residuos del detector - Remifentanilo")
    ax.legend(loc="best", framealpha=1.0)

    save_figure(fig, out_dir, "Residuos_remifentanilo", save_pdf)
    return fig


def plot_fault_flags(df, out_dir, save_pdf=True):
    t = df["time_min"]

    fig, ax = plt.subplots(figsize=(8, 3.2))

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
    ax.set_title("Banderas de falla inyectada y detectada")
    ax.legend(loc="best", framealpha=1.0)

    save_figure(fig, out_dir, "Banderas_falla", save_pdf)
    return fig


def run_experiment(config):
    configure_plot_style()

    out_dir = make_output_dir(config)
    save_config(config, out_dir)

    sim_cfg = config["simulation"]
    ctrl_cfg = config["controller"]
    obs_cfg = config["observer"]
    fault_cfg = config["fault"]
    hw_cfg = config["hardware"]
    out_cfg = config["output"]

    stimuli = build_stimuli(config["stimuli"])

    df = run_pid_observer(
        Ts_s=sim_cfg["Ts_s"],
        duracion_min=sim_cfg["duracion_min"],
        paciente=sim_cfg["paciente"],
        stimuli=stimuli,

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

    plot_bis(df, out_dir, save_pdf)
    plot_ce_prop(df, out_dir, save_pdf)
    plot_ce_remi(df, out_dir, save_pdf)
    plot_rates_prop(df, out_dir, save_pdf)
    plot_rates_remi(df, out_dir, save_pdf)
    plot_rates_combined(df, out_dir, save_pdf)
    plot_residuals_prop(df, out_dir, save_pdf)
    plot_residuals_remi(df, out_dir, save_pdf)
    plot_fault_flags(df, out_dir, save_pdf)

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