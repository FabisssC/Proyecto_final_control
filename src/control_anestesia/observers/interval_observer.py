import numpy as np


class IntervalObserver:
    def __init__(self, Ap, Bp, Cp, Ld, x_lower_0, x_upper_0, w_lower, w_upper):
        self.Ap = np.asarray(Ap, dtype=float)
        self.Bp = np.asarray(Bp, dtype=float)
        self.Cp = np.asarray(Cp, dtype=float)
        self.Ld = np.asarray(Ld, dtype=float)

        self.x_lower = np.asarray(x_lower_0, dtype=float).reshape(-1, 1)
        self.x_upper = np.asarray(x_upper_0, dtype=float).reshape(-1, 1)

        self.w_lower = np.asarray(w_lower, dtype=float).reshape(-1, 1)
        self.w_upper = np.asarray(w_upper, dtype=float).reshape(-1, 1)

    def step(self, u, y=None, use_correction=True):
        u = np.asarray(u, dtype=float).reshape(2, 1)

        y_upper = self.Cp @ self.x_upper
        y_lower = self.Cp @ self.x_lower

        if use_correction and y is not None:
            y = np.asarray(y, dtype=float).reshape(2, 1)

            # Convención: y_estimada - y
            innovation_upper = y_upper - y
            innovation_lower = y_lower - y
        else:
            innovation_upper = np.zeros((2, 1))
            innovation_lower = np.zeros((2, 1))

        x_upper_next = (
            self.Ap @ self.x_upper
            + self.Bp @ u
            + self.w_upper
            + self.Ld @ innovation_upper
        )

        x_lower_next = (
            self.Ap @ self.x_lower
            + self.Bp @ u
            - self.w_lower
            + self.Ld @ innovation_lower
        )

        self.x_upper = x_upper_next
        self.x_lower = x_lower_next

        y_upper_new = self.Cp @ self.x_upper
        y_lower_new = self.Cp @ self.x_lower

        return y_lower_new.flatten(), y_upper_new.flatten()