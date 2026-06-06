"""
Reproduce el experimento de tres pacientes del artículo Mera et al. 2025.
Cada paciente se simula con sus parámetros PK/PD directos (no demográficos).
El observador usa las mismas tasas PK que la planta.
"""
import json
from pathlib import Path
from control_anestesia.scenarios.closed_loop_pid_observer import run_pid_observer
import pandas as pd
import matplotlib.pyplot as plt

PATIENTS_FILE = Path("configs/patients.json")

def run_patient(patient_key: str):
    patients = json.loads(PATIENTS_FILE.read_text())
    cfg = patients[patient_key]

    print(f"\n=== Corriendo: {cfg['description']} ===")
    ares_id = cfg.get("ares_patient_id") or 0  # ← este cambio
    df = run_pid_observer(
        Ts_s=5,
        duracion_min=70,
        paciente=ares_id,
        fault_enabled=False,
        BIS_ref=50.0,
        ratio=2.0,
        Kp=0.0085, Ki=0.00069, Kd=0.011,
        # Pasar perfil PK directamente cuando esté implementado
        patient_profile=cfg,
    )

    out_path = Path(f"outputs/runs/{patient_key}_results.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"  → Guardado en {out_path}")
    return df

def plot_results(results: dict):
    """
    results: dict con {patient_key: DataFrame}
    """
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    colors = {"patient_A_mera": "blue", "patient_B_mera": "red", "patient_C_mera": "green"}

    for key, df in results.items():
        label = key.replace("patient_", "Paciente ").replace("_mera", "")
        color = colors[key]

        # BIS real vs referencia
        axes[0].plot(df["time_min"], df["BIS"], color=color, label=label)
        axes[0].fill_between(df["time_min"], df["BIS_menos"], df["BIS_mas"],
                             color=color, alpha=0.15)

    axes[0].axhline(50, color="black", linestyle="--", linewidth=1, label="BIS ref=50")
    axes[0].axhline(40, color="gray", linestyle=":", linewidth=0.8)
    axes[0].axhline(60, color="gray", linestyle=":", linewidth=0.8)
    axes[0].set_ylabel("BIS")
    axes[0].set_ylim(20, 100)
    axes[0].legend()
    axes[0].set_title("BIS con banda del observador (zona gris = intervalo estimado)")
    axes[0].grid(True)

    for key, df in results.items():
        label = key.replace("patient_", "Paciente ").replace("_mera", "")
        color = colors[key]
        axes[1].plot(df["time_min"], df["u_prop_cmd"], color=color, label=label)

    axes[1].set_ylabel("u_prop [mg/kg/hr]")
    axes[1].legend()
    axes[1].set_title("Tasa de infusión propofol")
    axes[1].grid(True)

    for key, df in results.items():
        label = key.replace("patient_", "Paciente ").replace("_mera", "")
        color = colors[key]
        axes[2].plot(df["time_min"], df["u_remi_cmd"], color=color, label=label)

    axes[2].set_ylabel("u_remi [µg/kg/hr]")
    axes[2].set_xlabel("Tiempo [min]")
    axes[2].legend()
    axes[2].set_title("Tasa de infusión remifentanilo")
    axes[2].grid(True)

    plt.tight_layout()
    plt.savefig("outputs/runs/three_patients_comparison.pdf", bbox_inches="tight")
    plt.show()
    print("  → Figura guardada en outputs/runs/three_patients_comparison.pdf")

if __name__ == "__main__":
    results = {}
    for key in ["patient_A_mera", "patient_B_mera", "patient_C_mera"]:
        results[key] = run_patient(key)

    plot_results(results)