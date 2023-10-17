import multiprocessing

import pyautogui
import math
import config as C
from filterapp import ScreenOverlayProcess
from multiprocessing import Queue
from queue import Full
import warnings

pyautogui.FAILSAFE = False


# class MouseController:
#     def __init__(self):
#         # Optionally, you can initialize some settings here
#         self.mouse_pressed = False  # Track the state of the mouse button
#
#     def move_to(self, pos: tuple[int, int]):
#         if pos is None:
#             return
#         # what the left hand does
#         pyautogui.moveTo(*pos)
#
#     def check_user_clicked(self, pos: tuple[int, int]):
#         cursor_pos = pyautogui.position()
#         distance = math.dist(pos, cursor_pos)
#
#         if not C.PRESENTATION_MODE:
#             if pos is None:
#                 if self.mouse_pressed:  # Only release the mouse button if it's currently pressed
#                     pyautogui.mouseUp()
#                     self.mouse_pressed = False
#                 return
#
#             # what the right hand does
#             if distance > C.HAND_CURSOR_CLICK_DISTANCE:
#                 if self.mouse_pressed:  # Only release the mouse button if it's currently pressed
#                     pyautogui.mouseUp()
#                     self.mouse_pressed = False
#             else:
#                 if not self.mouse_pressed:  # Only press the mouse button if it's currently not pressed
#                     pyautogui.mouseDown()
#                     self.mouse_pressed = True
#             return
#
#         if C.PRESENTATION_MODE:
#             button_pressed = False
#             if pos is None:
#                 button_pressed = False
#                 return
#
#             # check if user performs click action
#             if distance > C.HAND_CURSOR_CLICK_DISTANCE:
#                 button_pressed = False
#                 return
#
#             else:
#                 # only push a keydown event if there has not already been a keydown event the frame before, to avoid pressing "next" over and over again
#                 if not button_pressed:
#                     if cursor_pos >=< C.MONITOR_RESOLUTION[1] * C.PRESENTATION_ACTION_AREA_HEIGHT: # TODO check if comparison goes right direction, as for now it might either be top or bottom of the screen
#                         # check if hand is far enough on the left side during click:
#                         if cursor_pos[0] <= C.MONITOR_RESOLUTION[0] * C.PRESENTATION_ACTION_AREA_WIDTH:
#                             # TODO previous_slide_clicked ()
#                             return
#
#                         # check if hand is far enough on the right side during click:
#                         if cursor_pos[0] >= C.MONITOR_RESOLUTION[0] - (C.MONITOR_RESOLUTION*C.PRESENTATION_ACTION_AREA_WIDTH):
#                             # TODO next_slide_clicked ()
#                             return
#
#             return
#
#     def previous_slide_clicked(self):
#         pass
#
#     def next_slide_clicked(self):
#         pass
#
#

class Controller:
    def __new__(cls, *args, **kwargs):
        match C.MODE:
            case "standard":
                return _StandardMode()
            case "presentation":
                return _PresentationMode()

            case _:
                raise Exception(
                    f"The given mode {C.MODE} is not available. Please check config.py to see all available options."
                )


class _StandardMode:
    def __init__(self):
        self.mouse_pressed = False

        self.left_hand_pos = (-1, -1)
        self.right_hand_pos = (-1, -1)
        self.is_hand_detected = {"left": False, "right": False}
        self.is_hand_on_screen = {"left": False, "right": False}

        self.command_queue = Queue(maxsize=C.COMMAND_QUEUE_MAXSIZE)
        self.overlay = ScreenOverlayProcess(self.command_queue)

        self.overlay.start()

    @staticmethod
    def is_pos_onscreen(pos):
        if pos[0] < 0 or pos[1] < 0 or pos[0] > C.MONITOR_RESOLUTION[0] or pos[1] > C.MONITOR_RESOLUTION[1]:
            return False
        return True

    def update_left_hand(self, pos):
        if pos is None:
            self.is_hand_detected["left"] = False
            # Note: we don't uncheck is_hand_on_screen as it may be that the hand is still on screen whilst there was a frame where the detection didn't work
            # - might however lead to problems due to the hand fully disappearing from the camera image
            return

        assert not (None in pos)

        if not self.is_pos_onscreen(pos):
            self.is_hand_detected["left"] = True
            self.is_hand_on_screen["left"] = False
            self.left_hand_pos = tuple(int(a) for a in pos)
            self.update()
            return

        self.left_hand_pos = tuple(int(a) for a in pos)
        self.is_hand_detected["left"] = self.is_hand_on_screen["left"] = True
        self.update()

    def update_right_hand(self, pos):
        if pos is None:
            self.is_hand_detected["right"] = False
            # Note: we don't uncheck is_hand_on_screen as it may be that the hand is still on screen whilst there was a frame where the detection didn't work
            # - might however lead to problems due to the hand fully disappearing from the camera image
            return

        assert not (None in pos)

        if not self.is_pos_onscreen(pos):
            self.is_hand_detected["right"] = True
            self.is_hand_on_screen["right"] = False
            self.right_hand_pos = tuple(int(a) for a in pos)
            self.update()
            return

        self.right_hand_pos = tuple(int(a) for a in pos)
        self.is_hand_detected["right"] = self.is_hand_on_screen["right"] = True
        self.update()

    def feed_overlay(self, commands=()):
        sending = [
            ('debug_draw', None),
            ('highlighter_pos', self.left_hand_pos),
            ('highlighter_state', self.mouse_pressed),
            ('second_hand_pos', self.right_hand_pos)
        ]

        if len(commands):
            sending += commands

        try:
            for command in sending:
                # self.command_queue.put(command, block=False)
                pass
        except Full:
            warnings.warn("WARNING: The command Queue has run out of capacity.", UserWarning)

    def update(self):
        self.feed_overlay()

        # left hand:
        if self.is_hand_on_screen["left"]:
            # Move cursor to hand pos:
            pyautogui.moveTo(*self.left_hand_pos)

        # right hand:
        cursor_pos = pyautogui.position()

        if self.is_hand_detected["right"]:
            distance = math.dist(self.right_hand_pos, cursor_pos)
        else:
            return

        if self.is_hand_on_screen:
            # no right hand detected or not onscreen:
            pyautogui.mouseUp()
            self.mouse_pressed = False
            return

        if distance > C.HAND_CURSOR_CLICK_DISTANCE:
            if self.mouse_pressed:  # Only release the mouse button if it's currently pressed
                pyautogui.mouseUp()
                self.mouse_pressed = False
        else:
            if not self.mouse_pressed:  # Only press the mouse button if it's currently not pressed
                pyautogui.mouseDown()
                self.mouse_pressed = True

        # Maybe update onscreen hand position - should be merged into this class at least

    def __del__(self):
        self.command_queue.put(('stop', ))

class _PresentationMode(_StandardMode):
    def __init__(self):
        super().__init__()

        self.next_button_pressed = False
        self.previous_button_pressed = False

    def update(self):
        if False in (
                list(self.is_hand_on_screen.values()) + list(self.is_hand_detected.values())):  # both hands must be detected and onscreen for anything to happen
            distance = math.dist(self.left_hand_pos, self.right_hand_pos)
            if distance < C.HAND_CURSOR_CLICK_DISTANCE:
                # Hands make a click - now check if they click on nextslide, previousslide or none of both

                if 0 < self.left_hand_pos[0] < C.MONITOR_RESOLUTION[0] * C.PRESENTATION_ACTION_AREA_WIDTH and \
                        0 < self.left_hand_pos[1] < C.MONITOR_RESOLUTION[1] * C.PRESENTATION_ACTION_AREA_HEIGHT:
                    self.previous_slide()

                elif C.MONITOR_RESOLUTION[0] * (1 - C.PRESENTATION_ACTION_AREA_WIDTH) < self.left_hand_pos < \
                        C.MONITOR_RESOLUTION[0] and \
                        0 < self.left_hand_pos[1] < C.MONITOR_RESOLUTION[1] * C.PRESENTATION_ACTION_AREA_HEIGHT:
                    self.next_slide()

    def previous_slide(self):
        pass  # TODO

    def next_slide(self):
        pass  # TODO

# TODO make 2 classes for the control one for presentation mode and one for normal mode ( potentially one base class )
