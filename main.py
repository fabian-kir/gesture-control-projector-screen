import pyautogui

import config as C
import processing
from calibration import Calibration
from cameras import Camera
from screen import ScreenInput
from perform_onscreen_actions import Controller


class Main:
    def __init__(self):
        # self.screen_input = ScreenInput()

        self.cameras = [Camera(), ]

        self.calibration = Calibration(camera_sources=self.cameras)
        self.transformation = self.calibration()

        self.mouse_control = Controller()

        self.fingertip_detector = processing.HandDetector(self.cameras[0].resolution, self.transformation)

    def __call__(self):
        with self.cameras[0] as camera:
            while True:
                img = camera()
                transformed_fingertips = self.fingertip_detector(img)

                self.mouse_control.update_positions(transformed_fingertips[0], transformed_fingertips[1])

if __name__ == "__main__":
    print("main here")
    main = Main()
    main()
