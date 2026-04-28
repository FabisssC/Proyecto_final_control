import time
import serial


class SerialPumpInterface:
    def __init__(self, port="COM3", baudrate=115200, timeout=0.2):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.ser = None
        self.u_prop_f = 0.0
        self.u_remi_f = 0.0
        self.alpha = 0.35

    def connect(self):
        self.ser = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout
        )
        time.sleep(2)

    def close(self):
        if self.ser is not None and self.ser.is_open:
            self.stop()
            self.ser.close()

    def stop(self):
        if self.ser is not None and self.ser.is_open:
            self.ser.write(b"0\n")

    def send_rates(self, u_prop_cmd, u_remi_cmd):
        sp_j = u_prop_cmd / 0.48951

        sp_p = u_remi_cmd / 0.0308
        sp_p = sp_p * (156.3 - 35) / 217.27 + 35

        if sp_p != sp_p or sp_p == float("inf") or sp_p == float("-inf"):
            sp_p = 35

        self.ser.write(f"sj{sp_j:.3f}\n".encode())
        time.sleep(0.001)
        self.ser.write(f"sp{sp_p:.3f}\n".encode())

    def read_rates(self):
        u_prop_real = None
        u_remi_real = None

        while self.ser.in_waiting > 0:
            line = self.ser.readline().decode(errors="ignore").strip()
            parts = line.split(",")

            if len(parts) == 2:
                try:
                    u_prop_real = max(0.0, float(parts[0]))

                    rpm_peris = float(parts[1])
                    u_remi_real = (rpm_peris - 35) * 227.27 / (156.3 - 35)
                    u_remi_real = max(0.0, u_remi_real * 0.0308)
                    self.u_prop_f = self.alpha * u_prop_real + (1 - self.alpha) * self.u_prop_f
                    self.u_remi_f = self.alpha * u_remi_real + (1 - self.alpha) * self.u_remi_f

                    u_prop_real = self.u_prop_f
                    u_remi_real = self.u_remi_f
                except ValueError:
                    pass

        return u_prop_real, u_remi_real
