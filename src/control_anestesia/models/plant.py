from dataclasses import dataclass
import numpy as np
import pandas as pd

from control_anestesia.simulator_interface.ares_interface import AReSInterface, AReSConfig


@dataclass
class PlantResult:
    time_s: np.ndarray
    data: pd.DataFrame
    raw_state: dict
    raw_inputs: dict


def planta_ares(u_prop, u_remi, paciente=0, Ts=5) -> PlantResult:
    u_prop = np.asarray(u_prop, dtype=float).flatten()
    u_remi = np.asarray(u_remi, dtype=float).flatten()

    if u_prop.shape != u_remi.shape:
        raise ValueError("u_prop y u_remi deben tener la misma forma.")

    t_sim = len(u_prop)

    config = AReSConfig(
        patient_id=paciente,
        t_s=Ts
    )

    sim = AReSInterface(config)
    sim.initialize(t_sim=t_sim)

    state, inputs = sim.run(
        u_prop=u_prop,
        u_remi=u_remi
    )

    n = len(state["BIS"])
    time_s = np.arange(n) * Ts

    df = pd.DataFrame({
        "time_s": time_s,
        "BIS": np.asarray(state["BIS"][:n], dtype=float),
        "Ce_prop": np.asarray(state["ce_prop"][:n], dtype=float),
        "Ce_remi": np.asarray(state["ce_remi"][:n], dtype=float),
        "Cp_prop": np.asarray(state["cp_prop"][:n], dtype=float),
        "Cp_remi": np.asarray(state["cp_remi"][:n], dtype=float),
        "u_prop": np.asarray(inputs["u_prop"][:n], dtype=float),
        "u_remi": np.asarray(inputs["u_remi"][:n], dtype=float),
    })

    for key in ["MAP", "CO", "HR", "SV", "TPR", "ce_del", "ce_wav", "ce_bis"]:
        if key in state:
            values = state[key]
            if values is not None and len(values) >= n:
                df[key] = np.asarray(values[:n], dtype=float)

    return PlantResult(
        time_s=time_s,
        data=df,
        raw_state=state,
        raw_inputs=inputs,
    )