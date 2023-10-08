import cv2
import mss
import numpy as np

import config as C


class ScreenInput:
    def __init__(self):
        self.monitor_number = C.MONITOR +1

    def __call__(self):
        with mss.mss() as sct:
            return cv2.cvtColor(np.flip(np.array(sct.grab(sct.monitors[self.monitor_number]))[:, :, :3], 2), cv2.COLOR_BGR2RGB)
