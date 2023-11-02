from cv2 import VideoCapture
import cv2

import config as C

class Camera:
    def __init__(self):
        with self as camera:
            _ = camera.__call__()

        assert not (_ is None)
        self.width = _.shape[1]
        self.height = _.shape[0]
        self.resolution = (self.width, self.height)

    def __call__(self):
        ret, frame = self.cap.read()
        return frame


    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None

    def __enter__(self):
        self.cap = VideoCapture(C.CAMERA_INPUT)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()

    def __del__(self):
        self.release()