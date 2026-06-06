class PID:
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

        self.integral  = 0.0
        self.prev_error = 0.0

    def reset(self):
        self.integral   = 0.0
        self.prev_error = 0.0

    def compute(self, error):
        # Término proporcional
        P = self.Kp * error

        # Término integral (se actualiza ANTES de saturar)
        self.integral += error * self.Ts
        I = self.Ki * self.integral

        # Término derivativo
        D = self.Kd * (error - self.prev_error) / self.Ts
        self.prev_error = error

        u = P + I + D

        # Saturación + anti-windup por clamping
        if self.u_min is not None or self.u_max is not None:
            u_sat = u
            if self.u_max is not None:
                u_sat = min(u_sat, self.u_max)
            if self.u_min is not None:
                u_sat = max(u_sat, self.u_min)

            # Anti-windup: si la salida saturó, congela el integrador
            # en el valor que no habría causado saturación
            if self.anti_windup and u != u_sat:
                # Resta la contribución que causó el overflow
                self.integral -= error * self.Ts

            u = u_sat

        return u