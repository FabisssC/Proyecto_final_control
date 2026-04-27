import numpy as np
import scipy.signal as signal

from AReS.pharmacodynamics import PharmacodynamicDoH


class BISFilter:
    def __init__(self):
        bis_delay, bis_lti = PharmacodynamicDoH.bis_sensor_dynamics()

        self.bis_delay = signal.StateSpace(*bis_delay)
        self.bis_lti = signal.StateSpace(*bis_lti)

        self.x_lti = np.zeros(self.bis_lti.A.shape[0])
        self.x_delay = np.zeros(self.bis_delay.A.shape[0])

    def step(self, ce_prop_value, Ts_s=5):
        t = np.arange(0, Ts_s, 1)
        u = np.full(t.shape, float(ce_prop_value))

        _, y_lti, x_lti = signal.lsim(
            self.bis_lti,
            u,
            t,
            X0=self.x_lti
        )

        _, y_delay, x_delay = signal.lsim(
            self.bis_delay,
            y_lti,
            t,
            X0=self.x_delay
        )

        self.x_lti = x_lti[-1, :]
        self.x_delay = np.asarray(x_delay[-1]).reshape(-1)

        ce_bis = float(np.asarray(y_delay).flatten()[-1])
        return max(ce_bis, 0.0)