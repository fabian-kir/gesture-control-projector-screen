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
        if pos is None:
            if self.mouse_pressed:  # Only release the mouse button if it's currently pressed
                pyautogui.mouseUp()
                self.mouse_pressed = False
            return

        # what the right hand does
        cursor_pos = pyautogui.position()
        distance = math.dist(pos, cursor_pos)
        if distance > C.HAND_CURSOR_CLICK_DISTANCE:
            if self.mouse_pressed:  # Only release the mouse button if it's currently pressed
                pyautogui.mouseUp()
                self.mouse_pressed = False
        else:
            if not self.mouse_pressed:  # Only press the mouse button if it's currently not pressed
                pyautogui.mouseDown()
                self.mouse_pressed = True
