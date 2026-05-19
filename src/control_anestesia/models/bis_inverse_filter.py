import numpy as np
from control_anestesia.models.bis_inverse import BISInverseEstimator


class BISInverseFilter:
    def __init__(self, h_min, tau_min=None):
        self.inverse = BISInverseEstimator()
        self.x_filter = 0.0

        # tau = 100 segundos convertido a minutos (h_min está en minutos)
        if tau_min is None:
            tau_min = 100.0 / 60.0

        # y[k] = a*y[k-1] + (1-a)*u[k]
        self.a = np.exp(-h_min / tau_min)

    def step(self, BIS, Ce_prop_prom, Ce_remi_prom):
        Ce_prop_prom = max(float(Ce_prop_prom), 0.0)
        Ce_remi_prom = max(float(Ce_remi_prom), 0.0)

        Ce_prop_est = self.inverse.estimate_ce_prop(
            BIS=BIS,
            Ce_remi=Ce_remi_prom
        )

        # FIX: filtrar el error entre prom y estimada, sumar a la ESTIMADA
        # (no al prom como estaba antes) — replica exactamente Simulink:
        # y_filt = Ce_prop_est + LPF(Ce_prop_prom - Ce_prop_est)
        delta = Ce_prop_prom - Ce_prop_est
        self.x_filter = self.a * self.x_filter + (1 - self.a) * delta

        Ce_prop_filtrada = Ce_prop_est + self.x_filter
        Ce_remi_filtrada = Ce_remi_prom

        return Ce_prop_filtrada, Ce_remi_filtrada, Ce_prop_est, self.x_filter