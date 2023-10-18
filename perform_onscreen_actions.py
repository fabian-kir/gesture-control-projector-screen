import multiprocessing

import pyautogui
import math
import config as C
from filterapp import ScreenOverlayProcess
from multiprocessing import Queue
from queue import Full
import warnings
from custom_utils import EventListener

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
        self.mouse_pressed = EventListener(False, bind=None) # TODO!!!

        self._left_hand_pos = EventListener(None, bind=self.lefthand_onchange)
        self._right_hand_pos = EventListener(None, bind=self.righthand_onchange)

        self.left_hand_detected = EventListener(0, self.lefthanddetected_onchange)
        self.right_hand_detected = EventListener(0, self.righthanddetected_onchange) # -1 means its detected, otherwise amount of detection fails in a row

        self.command_queue = Queue(maxsize=C.COMMAND_QUEUE_MAXSIZE)
        self.overlay = ScreenOverlayProcess(self.command_queue)

        self.overlay.start()

    @staticmethod
    def is_pos_onscreen(pos):
        if pos[0] < 0 or pos[1] < 0 or pos[0] > C.MONITOR_RESOLUTION[0] or pos[1] > C.MONITOR_RESOLUTION[1]:
            return False
        return True

    @property
    def left_hand_pos(self):
        return self._left_hand_pos

    @left_hand_pos.setter
    def left_hand_pos(self, pos):
        if not (pos is None):
            assert not (None in pos)

        pos = tuple(int(val) for val in pos)
        self.left_hand_pos.value = pos

    @property
    def right_hand_pos(self):
        return self._right_hand_pos

    @right_hand_pos.setter
    def right_hand_pos(self, pos):
        if not (pos is None):
            assert not (None in pos)

        pos = tuple(int(val) for val in pos)
        self.left_hand_pos.value = pos

    @property
    def hand_detection_failed_count(self):
        return self.hand_detection_failed_count

    @hand_detection_failed_count.setter
    def hand_detection_failed_count(self, value):
        if value >= C.INAROW_HAND_DETECTION_FAILS:


    def lefthand_onchange(self, val):
        # hand was moved!

        if val is None:
            # no hand was detected
            self.left_hand_detected.value += 1

        else:
            # hand was detected somewhere
            self.left_hand_detected.value = -1

            if self.is_pos_onscreen(val):
                # hand was detected and is on screen:
                self.command_queue.put(('highlighter_pos', val))
                pyautogui.moveTo(*val)
            else:
                # hand detected outside screen:
                pass


    def lefthanddetected_onchange(self, val):
        # hand was new detected:
        if val == -1:
            self.send_command(('highlighter_visible', True))

        elif val > C.INAROW_HAND_DETECTION_FAILS:
            self.send_command(('highlighter_visible', False))
            pyautogui.mouseUp()

    def righthand_onchange(self, val):
    # right hand was moved:
        if val is None:
            # right hand was undetected:
            self.right_hand_detected += 1

        else:
            # right hand was detected somewhere

            # check if right hand is within radius
            self.send_command(('second_hand_pos', val))
            if math.dist(val, self.left_hand_pos.value) <= C.HAND_CURSOR_CLICK_DISTANCE and self.is_pos_onscreen(self.left_hand_pos.value):
                self.mouse_pressed = True
            else:
                self.mouse_pressed = False

    def righthanddetected_onchange(self, val):
        # functionality for if val >= C.INAROW...


    def send_command(self, command):
    def feed_overlay(self, commands=()): # outdated, from now on send_command will do that
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


def __init__(self):
    self.events = SomeModule()
    self.latest_pos = None

    self.events.add_listener(
        var = self.latest_pos,
        callback=self.on_pos_change
    )
def on_pos_change(self, value):
    print(f"new value for self.latest_pos is {value}")