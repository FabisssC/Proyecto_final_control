import numpy as np
import pandas as pd

from control_anestesia.controllers.pid import PID
from control_anestesia.simulator_interface.ares_step_interface import AReSStepInterface
from control_anestesia.simulator_interface.ares_interface import AReSConfig


def run_pid_ratio(Ts_s=5, duracion_min=60, paciente=0):
    t_sim = int((duracion_min * 60) / Ts_s)
    h_min = Ts_s / 60

    BIS_ref = 50.0
    ratio = 2.0

    u_prop_min = 0.0
    u_prop_max = 10.0

    u_remi_min = 0.0
    u_remi_max = 20.0

    pid = PID(
        Kp=0.009,
        Ki=0.000055,
        Kd=0.005,
        Ts=h_min
    )

    config = AReSConfig(
        patient_id=paciente,
        t_s=Ts_s
    )

    sim = AReSStepInterface(config)
    sim.initialize(t_sim)

    time = []
    BIS = []
    Ce_prop = []
    Ce_remi = []
    u_prop_hist = []
    u_remi_hist = []
    error_hist = []

    u_prop_k = 0.0
    u_remi_k = 0.0

    for k in range(t_sim):
        state = sim.step(u_prop_k, u_remi_k)

        BIS_k = state["BIS"]
        Ce_prop_k = state["ce_prop"]
        Ce_remi_k = state["ce_remi"]

        error = BIS_k - BIS_ref

        u_prop_k = pid.compute(error)
        u_prop_k = max(min(u_prop_k, u_prop_max), u_prop_min)

        u_remi_k = ratio * u_prop_k
        u_remi_k = max(min(u_remi_k, u_remi_max), u_remi_min)

        time.append(k * Ts_s)
        BIS.append(BIS_k)
        Ce_prop.append(Ce_prop_k)
        Ce_remi.append(Ce_remi_k)
        u_prop_hist.append(u_prop_k)
        u_remi_hist.append(u_remi_k)
        error_hist.append(error)

    df = pd.DataFrame({
        "time_s": np.array(time),
        "time_min": np.array(time) / 60,
        "BIS": np.array(BIS),
        "BIS_ref": BIS_ref,
        "error": np.array(error_hist),
        "Ce_prop": np.array(Ce_prop),
        "Ce_remi": np.array(Ce_remi),
        "u_prop": np.array(u_prop_hist),
        "u_remi": np.array(u_remi_hist),
    })

    return df