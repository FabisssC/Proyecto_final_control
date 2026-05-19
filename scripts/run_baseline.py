from control_anestesia.models.plant import planta_ares
import numpy as np
import pandas as pd

def escenario_escalon(Ts_s, duracion_min, u_prop_val=2.0, u_remi_val=4.0):
    n = int(duracion_min * 60 / Ts_s)
    u_prop = np.ones(n) * u_prop_val
    u_remi = np.ones(n) * u_remi_val
    return u_prop, u_remi

Ts_s = 5
duracion_min = 60
u_prop, u_remi = escenario_escalon(Ts_s, duracion_min)
result = planta_ares(u_prop=u_prop, u_remi=u_remi, paciente=0, Ts=Ts_s)
df = result.data
df.to_csv("outputs/identificacion_escalon.csv", index=False)
print(df.head())