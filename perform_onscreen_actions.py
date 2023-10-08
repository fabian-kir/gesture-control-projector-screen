import pyautogui
import math
import config as C

pyautogui.FAILSAFE = False

class MouseController:
    def __init__(self):
        # Optionally, you can initialize some settings here
        self.mouse_pressed = False  # Track the state of the mouse button

    def move_to(self, pos: tuple[int, int]):
        if pos is None:
            return
        # what the left hand does
        pyautogui.moveTo(*pos)

    def check_user_clicked(self, pos: tuple[int, int]):
        cursor_pos = pyautogui.position()
        distance = math.dist(pos, cursor_pos)

        if not C.PRESENTATION_MODE:
            if pos is None:
                if self.mouse_pressed:  # Only release the mouse button if it's currently pressed
                    pyautogui.mouseUp()
                    self.mouse_pressed = False
                return

            # what the right hand does
            if distance > C.HAND_CURSOR_CLICK_DISTANCE:
                if self.mouse_pressed:  # Only release the mouse button if it's currently pressed
                    pyautogui.mouseUp()
                    self.mouse_pressed = False
            else:
                if not self.mouse_pressed:  # Only press the mouse button if it's currently not pressed
                    pyautogui.mouseDown()
                    self.mouse_pressed = True
            return

        if C.PRESENTATION_MODE:
            button_pressed = False
            if pos is None:
                button_pressed = False
                return

            # check if user performs click action
            if distance > C.HAND_CURSOR_CLICK_DISTANCE:
                button_pressed = False
                return

            else:
                # only push a keydown event if there has not already been a keydown event the frame before, to avoid pressing "next" over and over again
                if not button_pressed:
                    if cursor_pos >=< C.MONITOR_RESOLUTION[1] * C.PRESENTATION_ACTION_AREA_HEIGHT: # TODO check if comparison goes right direction, as for now it might either be top or bottom of the screen
                        # check if hand is far enough on the left side during click:
                        if cursor_pos[0] <= C.MONITOR_RESOLUTION[0] * C.PRESENTATION_ACTION_AREA_WIDTH:
                            # TODO previous_slide_clicked ()
                            return

                        # check if hand is far enough on the right side during click:
                        if cursor_pos[0] >= C.MONITOR_RESOLUTION[0] - (C.MONITOR_RESOLUTION*C.PRESENTATION_ACTION_AREA_WIDTH):
                            # TODO next_slide_clicked ()
                            return

            return

    def previous_slide_clicked(self):
        pass

    def next_slide_clicked(self):
        pass

# TODO make 2 classes for the control one for presentation mode and one for normal mode ( potentially one base class )

