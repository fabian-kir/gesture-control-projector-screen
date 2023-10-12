import pyautogui  # I do not know why, but however, this line seems to be REALLY important ?!?!?!

import config as C
import processing
from calibration import Calibration
from cameras import IriunCameraInput
from filterapp import TransparentWindow
from screen import ScreenInput
from perform_onscreen_actions import Controller


class Main:
    def __init__(self):
        # self.screen_input = ScreenInput()

        self.cameras = [IriunCameraInput(), ]

        self.calibration = Calibration(camera_sources=self.cameras)
        self.transformation = self.calibration()

        self.mouse_control = Controller()

        self.fingertip_detector = processing.HandDetector(self.cameras[0].resolution, self.transformation)

        self.transparent_window = TransparentWindow()


    def __call__(self):
        with self.cameras[0] as camera:
            while True:
                img = camera()
                transformed_fingertips = self.fingertip_detector(img)

                self.mouse_control.update_left_hand(transformed_fingertips[0])
                self.mouse_control.update_right_hand(transformed_fingertips[1])

                self.transparent_window.update_hand_position(transformed_fingertips[1])

                self.transparent_window.draw_highlighter()

main = Main()
main()