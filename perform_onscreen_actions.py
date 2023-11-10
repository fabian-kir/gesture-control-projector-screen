import math
import multiprocessing
import queue
import warnings
from time import sleep
from typing import Optional
import numpy as np
from overlaytest import FilterApp

import pyautogui

import config as C

pyautogui.PAUSE = 0

pyautogui.FAILSAFE = False


class Controller:
    def __new__(cls, *args, **kwargs):
        match C.MODE:
            case "standard":
                return _StandardMode()

            case _:
                raise Exception(
                    f"The given mode {C.MODE} is not available. Please check config.py to see all available options."
                )

class Mode:
    def __init__(self):
        # Initialize the positions to None, indicating no detection.
        self.left_hand_pos = None
        self.right_hand_pos = None

        self.command_queue = multiprocessing.Queue(maxsize=C.COMMAND_QUEUE_MAXSIZE)


    def update_positions(self, left_hand_pos: Optional[tuple[int, int]], right_hand_pos: Optional[tuple[int, int]]):
        self.left_hand_pos = left_hand_pos
        self.right_hand_pos = right_hand_pos

    @staticmethod
    def normalize_position(pos):
        """Convert the position to a tuple of ints."""
        if pos is None:
            return None
        return (int(pos[0]), int(pos[1]))

    @staticmethod
    def is_pos_onscreen(pos) -> bool:
        if pos[0] < 0 or pos[1] < 0 or pos[0] > C.MONITOR_RESOLUTION[0] or pos[1] > C.MONITOR_RESOLUTION[1]:
            return False
        return True

    def send_command(self, command):
        try:
            self.command_queue.put(command)
            return True
        except queue.Full:
            warnings.warn("Command Queue is full!", UserWarning)
            return False

class _StandardMode(Mode):
    def __init__(self):
        super().__init__()
        # Initialize mouse_pressed to False
        self.mouse_pressed = -1

        self.window = FilterApp()

    def update_positions(self, left_hand_pos: Optional[tuple[int, int]], right_hand_pos: Optional[tuple[int, int]]):
        if left_hand_pos is None:
            return
        left_hand_pos = self.normalize_position(left_hand_pos)

        pyautogui.moveTo(*left_hand_pos)

        if right_hand_pos is None:
            self.window.event_processing()
            return
        right_hand_pos = self.normalize_position(right_hand_pos)


        self.window.pos2 = right_hand_pos

        if math.dist(left_hand_pos, right_hand_pos) <= C.HAND_CURSOR_CLICK_DISTANCE:
            if self.mouse_pressed == -1:
                pyautogui.click()
                print("click")
                self.mouse_pressed += 1
                self.window.active = True

            elif self.mouse_pressed == 30:
                pyautogui.mouseDown()
                print("mousedown")
                self.window.active = True

            else:
                self.mouse_pressed += 1
                self.window.active = False

        elif math.dist(left_hand_pos, right_hand_pos) >= C.HAND_CURSOR_CLICK_DISTANCE:
            self.mouse_pressed = -1
            pyautogui.mouseUp()
            print("mouseup")
            self.window.active = False

        self.window.event_processing()


