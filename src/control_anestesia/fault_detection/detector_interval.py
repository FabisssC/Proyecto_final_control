import numpy as np


class IntervalFaultDetector:
    def __init__(self, epsilon=0.3, enable_time_min=5.0):
        self.epsilon = epsilon
        self.enable_time_min = enable_time_min

    def evaluate(self, time_min, Ce_prop, Ce_prop_mas, Ce_prop_menos,
                 Ce_remi, Ce_remi_mas, Ce_remi_menos):

        r_prop = np.array([
            Ce_prop_mas - Ce_prop,
            -(Ce_prop - Ce_prop_menos)
        ])

        r_remi = np.array([
            Ce_remi_mas - Ce_remi,
            -(Ce_remi - Ce_remi_menos)
        ])

        enable = time_min > self.enable_time_min

        if enable:
            fallo_prop = (r_prop[0] > self.epsilon) or (r_prop[1] < -self.epsilon)
            fallo_remi = (r_remi[0] > self.epsilon) or (r_remi[1] < -self.epsilon)
        else:
            fallo_prop = False
            fallo_remi = False

        return r_prop, r_remi, fallo_prop, fallo_remi
