import numpy as np

from control_anestesia.models.bis_inverse import BISInverseEstimator


class BISInverseFilter:
    def __init__(self, h_min, tau_min=100.0):
        self.inverse = BISInverseEstimator()
        self.x_filter = 0.0

        # Filtro discreto equivalente simple:
        # y[k] = a*y[k-1] + (1-a)*u[k]
        self.a = np.exp(-h_min / tau_min)

    def step(self, BIS, Ce_prop_prom, Ce_remi_prom):
        Ce_prop_prom = max(float(Ce_prop_prom), 0.0)
        Ce_remi_prom = max(float(Ce_remi_prom), 0.0)

        Ce_prop_est = self.inverse.estimate_ce_prop(
            BIS=BIS,
            Ce_remi=Ce_remi_prom
        )

        delta = Ce_prop_prom - Ce_prop_est

        self.x_filter = self.a * self.x_filter + (1 - self.a) * delta

        Ce_prop_filtrada = Ce_prop_prom + self.x_filter
        Ce_remi_filtrada = Ce_remi_prom

        return Ce_prop_filtrada, Ce_remi_filtrada, Ce_prop_est, self.x_filter