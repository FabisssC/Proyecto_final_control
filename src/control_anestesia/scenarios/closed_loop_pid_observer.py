import numpy as np
import pandas as pd
import time
from control_anestesia.models.bis_filter import BISFilter
from control_anestesia.controllers.pid import PID
from control_anestesia.simulator_interface.ares_step_interface import AReSStepInterface
from control_anestesia.simulator_interface.ares_interface import AReSConfig
from control_anestesia.observers.observer_model import build_observer_model
from control_anestesia.observers.interval_observer import IntervalObserver
from control_anestesia.models.bis_model import bis_from_ce
from control_anestesia.fault_detection.detector_interval import IntervalFaultDetector
from control_anestesia.fault_detection.fault_scenarios import apply_prop_fault, apply_remi_fault
from control_anestesia.hardware_interface.serial_pump import SerialPumpInterface
from control_anestesia.models.bis_model_ares import bis_from_ce_ares
from control_anestesia.models.bis_inverse import BISInverseEstimator
from control_anestesia.models.bis_inverse_filter import BISInverseFilter
detector = IntervalFaultDetector(epsilon=0.3, enable_time_min=10.0)

def _scalar(value):
    arr = np.asarray(value, dtype=float).flatten()
    return float(arr[-1])


def bis_from_ce_ares(ce_bis, ce_remi, age=40):
    e0 = 93.0
    beta = 1.0

    ec50_prop = 3.08 * np.exp(-0.00635 * (age - 35))
    ec50_remi = 12.7

    ce_bis = max(float(ce_bis), 0.0)
    ce_remi = max(float(ce_remi), 0.0)

    inter_prop = ce_bis / ec50_prop
    inter_remi = ce_remi / ec50_remi

    theta = inter_prop / (inter_prop + inter_remi + np.finfo(float).eps)
    inter = (inter_prop + inter_remi) / (1 - beta * theta + beta * theta**2)

    if inter < 0:
        inter = 0.0

    gamma = 1.89 if ce_bis < ec50_prop else 1.47

    effect = inter**gamma / (1 + inter**gamma)
    bis = e0 - e0 * effect

    return bis


def bis_band_from_ce_ares(Ce_prop_menos, Ce_prop_mas, Ce_remi_menos, Ce_remi_mas, age):
    candidates = [
        bis_from_ce_ares(Ce_prop_menos, Ce_remi_menos, age=age),
        bis_from_ce_ares(Ce_prop_menos, Ce_remi_mas, age=age),
        bis_from_ce_ares(Ce_prop_mas, Ce_remi_menos, age=age),
        bis_from_ce_ares(Ce_prop_mas, Ce_remi_mas, age=age),
    ]

    return min(candidates), max(candidates)


def run_pid_observer(    
    Ts_s=5,
    duracion_min=60,
    paciente=0,
    stimuli=None,
    fault_enabled=False,
    fault_drug="prop",
    fault_start_min=30.0,
    fault_factor=0.0,
    use_hardware=False,
    hardware_port="COM3",
    observer_measurement_mode="ares_ce",
    ):

    n_steps = int((duracion_min * 60) / Ts_s)
    duracion_s = int(duracion_min * 60)
    h_min = Ts_s / 60

    BIS_ref = 50.0
    ratio = 2.0

    u_prop_min = 0.0
    u_prop_max = 10.0
    u_remi_min = 0.0
    u_remi_max = 20.0

    # Parámetros de prueba de falla
    falla_prop_start_min = 59.0
    falla_prop_factor = 0.9999

    # Detector
    detector_enable_time_min = 10.0
    epsilon = 1

    pid = PID(
        Kp=0.0085,
        Ki=0.00069,
        Kd=0.011,
        #Kp=0.006,
        #Ki=0.00039,
        #Kd=0.012,
        Ts=h_min
    )

    config = AReSConfig(
        patient_id=paciente,
        t_s=Ts_s
    )

    sim = AReSStepInterface(config)
    sim.initialize(duracion_s, stimuli=stimuli)

    demographics = sim.sim.get_patient_demographics()
    age_patient = demographics["age"]
    bis_inverse = BISInverseEstimator()
    bis_inverse_filter = BISInverseFilter(h_min=h_min)

    Ap, Bp, Cp, Dp = build_observer_model(h_min=h_min)

    Ld = 1.6*np.array([
        [0.0,       0.11],
        [0.0,       0.0],
        [0.000045,  0.0],
        [-0.9627,   0.0],
        [0.0,       0.0],
        [0.0,       0.00081],
        [0.012,     0.0],
        [0.0,      -0.9416],
    ], dtype=float)

    #w_lower = np.array([
    #    0.05, 0.05, 0.05, 0.05,
    #    0.05, 0.05, 0.05, 0.05
    #])

    #w_upper = np.array([
    #    0.05, 0.05, 0.05, 0.05,
    #    0.12, 0.12, 0.12, 0.12
    #])
    w_lower=0.0 * np.ones(8)
    w_upper=0.0 * np.ones(8)
    observer = IntervalObserver(
        Ap=Ap,
        Bp=Bp,
        Cp=Cp,
        Ld=Ld,
        x_lower_0=0.006 * np.ones(8),
        x_upper_0=np.array([
            0.014, 0.014, 0.014, 0.014,
            0.018, 0.018, 0.018, 0.018
        ]),
        w_lower=w_lower,
        w_upper=w_upper,
    )

    bis_filter_lower = BISFilter()
    bis_filter_upper = BISFilter()

    # FIX: inicializar y_prev con valores coherentes con el estado inicial
    # del observador (sin fármaco = 0.0) en lugar de dejarlos en cero
    # para evitar que la función inversa arranque con Ce_remi=0 y sobreestime Ce_prop.
    y_upper_prev = np.array([0.6, 0.06])
    y_lower_prev = np.array([0.6, 0.06])

    rows = []

    u_prop_cmd = 0.0
    u_remi_cmd = 0.0


    x1 = 0.0
    x2 = 0.0
    a1 = 1.0579260447065506
    a2 = -0.05912994947958233
    b0 = 0.019777367048692828
    b1 = 0.019777367048692828
    Ce_remi_pred = 0.0
    Ce_remi_pred_prev = 0.0
    u_remi_prev = 0.0
    alpha_correction = 0.1   # mezcla predictor + promedio observador
    warmup_min = 3.0 
    # --- FIN PREDICTOR BACKUP ---

    pump = None

    if use_hardware:
        pump = SerialPumpInterface(port=hardware_port)
        pump.connect()
    try:
        for k in range(n_steps):
            t_start = time.time()
            time_min = (k * Ts_s) / 60

            falla_prop_inyectada = fault_enabled and fault_drug == "prop" and time_min >= fault_start_min
            falla_remi_inyectada = fault_enabled and fault_drug == "remi" and time_min >= fault_start_min

            u_prop_sim = apply_prop_fault(
                u_prop_cmd,
                time_min,
                enabled=falla_prop_inyectada,
                start_min=fault_start_min,
                factor=fault_factor
            )

            u_remi_sim = apply_remi_fault(
                u_remi_cmd,
                time_min,
                enabled=falla_remi_inyectada,
                start_min=fault_start_min,
                factor=fault_factor
            )
            if use_hardware:
                pump.send_rates(u_prop_cmd, u_remi_cmd)

                u_prop_real, u_remi_real = pump.read_rates()

                u_prop_app = u_prop_real if u_prop_real is not None else u_prop_sim
                u_remi_app = u_remi_real if u_remi_real is not None else u_remi_sim
            else:
                u_prop_app = u_prop_sim
                u_remi_app = u_remi_sim

            state = sim.step(u_prop_app, u_remi_app)

            BIS_k = _scalar(state["BIS"])
            Ce_prop_k = _scalar(state["ce_prop"])
            Ce_remi_k = _scalar(state["ce_remi"])
            Ce_bis_k = _scalar(state["ce_bis"])


            a1 = 0.9163624550534433
            a2 = 0.9885824466709823
            b1 = 0.2006109269186557
            b2 = 0.20111136652713787
            g  = 0.6045650345027572
            x1 = a1 * x1 + b1 * u_remi_cmd
            x2 = a2 * x2 + b2 * x1

            Ce_remi_pred = g * x2
            Ce_remi_pred = max(0.0, Ce_remi_pred)
            
            # --- FIN PREDICTOR BACKUP ---

            if observer_measurement_mode == "ares_ce":
                Ce_prop_obs = Ce_prop_k
                Ce_remi_obs = Ce_remi_k
                Ce_remi_prom = max(0.5 * (y_upper_prev[1] + y_lower_prev[1]), 0.0)
                Ce_bis_inv = 0.8*bis_inverse.estimate_ce_prop(BIS_k, Ce_remi_pred)

            elif observer_measurement_mode == "bis_inverse":
                Ce_remi_prom = 0.5 * (y_upper_prev[1] + y_lower_prev[1])
               
                #Ce_remi_prom = alpha_warmup * Ce_remi_prom_obs + (1.0 - alpha_warmup) * Ce_remi_pred*1.3
                BIS_k = np.clip(BIS_k, 20.0, 98.0)

                
                Ce_prop_obs = 0.809 * bis_inverse.estimate_ce_prop(BIS_k,Ce_remi_pred)
                Ce_remi_obs = 1.01*Ce_remi_pred

                # Para logging: estimación con Ce_remi real (solo disponible en simulación)
                #Ce_remi_prom = max(0.5 * (y_upper_prev[1] + y_lower_prev[1]), 0.0)
                #Ce_prop_prom = max(0.5 * (y_upper_prev[0] + y_lower_prev[0]), 0.0)

                #BIS_k = np.clip(BIS_k, 20.0, 98.0)

                #Ce_prop_obs, Ce_remi_obs, Ce_bis_inv, _ = bis_inverse_filter.step(
                #    BIS=BIS_k,
                #    Ce_prop_prom=0.8*bis_inverse.estimate_ce_prop(BIS_k, Ce_remi_pred),
                #    Ce_remi_prom=Ce_remi_pred
                #)
                Ce_bis_inv = 0.805 * bis_inverse.estimate_ce_prop(BIS_k, Ce_remi_k)

            y_medida = np.array([Ce_prop_obs, Ce_remi_obs])

            
            u_observer = np.array([u_prop_cmd, u_remi_cmd])

            # Antes de la falla se usa corrección para mantener el observador calibrado.
            # Después de la falla se desactiva para que el observador no "siga" la planta fallada.
            use_observer_correction = True

            y_lower, y_upper = observer.step(
                u=u_observer,
                y=y_medida,
                use_correction=use_observer_correction
            )

            # FIX: actualizar y_prev DESPUÉS del step del observador para que en el
            # próximo paso k+1, Ce_remi_prom refleje las salidas del paso k.
            y_upper_prev = y_upper.copy()
            y_lower_prev = y_lower.copy()

            Ce_prop_menos = y_lower[0]
            Ce_remi_menos = y_lower[1]
            Ce_prop_mas = y_upper[0]
            Ce_remi_mas = y_upper[1]

            Ce_bis_menos = bis_filter_lower.step(Ce_prop_menos, Ts_s=Ts_s)
            Ce_bis_mas = bis_filter_upper.step(Ce_prop_mas, Ts_s=Ts_s)

            BIS_desde_Ce_real = bis_from_ce(Ce_prop_k, Ce_remi_k)
            BIS_desde_Ce_bis = bis_from_ce_ares(Ce_prop_obs, Ce_remi_obs, age=age_patient)

            BIS_menos, BIS_mas = bis_band_from_ce_ares(
                Ce_prop_menos=Ce_bis_menos,
                Ce_prop_mas=Ce_bis_mas,
                Ce_remi_menos=Ce_remi_menos,
                Ce_remi_mas=Ce_remi_mas,
                age=age_patient
            )

            r_prop, r_remi, fallo_prop, fallo_remi = detector.evaluate(
                time_min=time_min,
                #Ce_prop=Ce_prop_k,
                Ce_prop=Ce_prop_obs,
                Ce_prop_mas=Ce_prop_mas,
                Ce_prop_menos=Ce_prop_menos,
                Ce_remi=Ce_remi_obs,
                Ce_remi_mas=Ce_remi_mas,
                Ce_remi_menos=Ce_remi_menos,
            )

            error = BIS_k - BIS_ref

            u_prop_cmd = pid.compute(error)
            u_prop_cmd = max(min(u_prop_cmd, u_prop_max), u_prop_min)

            u_remi_cmd = ratio * u_prop_cmd
            u_remi_cmd = max(min(u_remi_cmd, u_remi_max), u_remi_min)

            rows.append({
                "time_s": k * Ts_s,
                "time_min": time_min,

                "falla_prop_inyectada": falla_prop_inyectada,
                "falla_remi_inyectada": falla_remi_inyectada,
                "BIS": BIS_k,
                "BIS_ref": BIS_ref,
                "BIS_desde_Ce_real": BIS_desde_Ce_real,
                "BIS_desde_Ce_bis": BIS_desde_Ce_bis,
                "BIS_mas": BIS_mas,
                "BIS_menos": BIS_menos,
                "age_patient": age_patient,
                "error": error,
                "Ce_remi_pred": Ce_remi_pred,  
                "Ce_remi_corr": Ce_remi_obs,   
                "Ce_remi_prom":Ce_remi_prom,

                "Ce_prop": Ce_prop_k,
                "Ce_remi": Ce_remi_k,
                "Ce_bis": Ce_bis_k,
                "Ce_prop_obs": Ce_prop_obs,
                "Ce_remi_obs": Ce_remi_obs,
                "Ce_bis_menos": Ce_bis_menos,
                "Ce_bis_mas": Ce_bis_mas,
                "Ce_bis_inv": Ce_bis_inv,
                "Ce_prop_menos": Ce_prop_menos,
                "Ce_prop_mas": Ce_prop_mas,
                "Ce_remi_menos": Ce_remi_menos,
                "Ce_remi_mas": Ce_remi_mas,

                "r_prop_sup": r_prop[0],
                "r_prop_inf": r_prop[1],
                "r_remi_sup": r_remi[0],
                "r_remi_inf": r_remi[1],

                "fallo_prop": fallo_prop,
                "fallo_remi": fallo_remi,

                "u_prop_app": u_prop_app,
                "u_remi_app": u_remi_app,
                "u_prop_cmd": u_prop_cmd,
                "u_remi_cmd": u_remi_cmd,
            })
            if use_hardware:
                elapsed = time.time() - t_start
                time.sleep(max(0.0, Ts_s - elapsed))
    finally:
        if pump is not None:
            pump.close()
    return pd.DataFrame(rows)