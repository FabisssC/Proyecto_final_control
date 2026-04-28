import numpy as np
from control_anestesia.models.bis_model_ares import bis_from_ce_ares


class BISInverseEstimator:
    def __init__(self, age=40, ce_max=20.0):
        self.age = age
        self.ce_max = ce_max
        self.prev = 0.0

    def estimate_ce_prop(self, BIS, Ce_remi):
        BIS = float(BIS)
        Ce_remi = max(float(Ce_remi), 0.0)

        lo = 0.0
        hi = self.ce_max

        f_lo = bis_from_ce_ares(lo, Ce_remi, age=self.age) - BIS
        f_hi = bis_from_ce_ares(hi, Ce_remi, age=self.age) - BIS

        n = 0
        while f_lo * f_hi > 0 and n < 10:
            hi *= 2
            f_hi = bis_from_ce_ares(hi, Ce_remi, age=self.age) - BIS
            n += 1

        if f_lo * f_hi > 0:
            return self.prev

        for _ in range(40):
            mid = 0.5 * (lo + hi)
            f_mid = bis_from_ce_ares(mid, Ce_remi, age=self.age) - BIS

            if f_lo * f_mid <= 0:
                hi = mid
                f_hi = f_mid
            else:
                lo = mid
                f_lo = f_mid

        self.prev = 0.5 * (lo + hi)
        return self.prev