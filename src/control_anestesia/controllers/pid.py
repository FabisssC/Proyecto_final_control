class PID:
    """
    PID con anti-windup y derivativo sobre la medición.

    Convención de este sistema: error = y - r (BIS - ref).
    Con esta convención, el derivativo sobre medición es:
        D = +Kd * (y_k - y_{k-1}) / Ts

    Cuando BIS cae (y_k < y_{k-1}): D < 0 → frena u → previene overshoot.
    Cuando BIS sube (recuperación): D > 0 → añade u → acelera la corrección.

    Nota: en la convención estándar (error = r - y) el signo sería -Kd*dy/dt.
    Aquí es +Kd*dy/dt porque error = y - r invierte el signo del derivativo.
    """
    def __init__(self, Kp, Ki, Kd, Ts,
                 u_min=None, u_max=None,
                 anti_windup=True):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.Ts = Ts
        self.u_min = u_min
        self.u_max = u_max
        self.anti_windup = anti_windup
        self.integral   = 0.0
        self.prev_error = 0.0
        self.prev_y     = None

    def reset(self):
        self.integral   = 0.0
        self.prev_error = 0.0
        self.prev_y     = None

    def compute(self, error, measurement=None):
        """
        error       : BIS_k - BIS_ref  (siempre requerido)
        measurement : BIS_k  (pasar para derivativo sobre medición, recomendado)
        """
        P = self.Kp * error

        self.integral += error * self.Ts
        I = self.Ki * self.integral

        if measurement is not None:
            if self.prev_y is None:
                self.prev_y = measurement     # primer paso → D = 0, sin kick
            # Signo +Kd porque error = y - r en este sistema
            D = self.Kd * (measurement - self.prev_y) / self.Ts
            self.prev_y = measurement
        else:
            D = self.Kd * (error - self.prev_error) / self.Ts

        self.prev_error = error
        u = P + I + D

        if self.u_min is not None or self.u_max is not None:
            u_sat = u
            if self.u_max is not None: u_sat = min(u_sat, self.u_max)
            if self.u_min is not None: u_sat = max(u_sat, self.u_min)
            if self.anti_windup and u != u_sat:
                self.integral -= error * self.Ts
            u = u_sat

        return u