import multiprocessing
import queue
from time import sleep

import pyautogui
import math
import config as C
from filterapp import ScreenOverlayProcess
from multiprocessing import Queue
from queue import Full
import warnings
from custom_utils import EventListener
from typing import Optional, Tuple

pyautogui.PAUSE = 0

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

            case "standard2":
                return _StandardMode2()

            case _:
                raise Exception(
                    f"The given mode {C.MODE} is not available. Please check config.py to see all available options."
                )


class _StandardMode:
    def __init__(self):
        self.mouse_pressed = EventListener(False, bind=self.mousepressed_onchange)

        self.left_hand_pos = EventListener(None, bind=self.lefthand_onchange)
        self.right_hand_pos = EventListener(None, bind=self.righthand_onchange)

        self.left_hand_detected = EventListener(0, self.lefthanddetected_onchange)
        self.right_hand_detected = EventListener(0, self.righthanddetected_onchange) # -1 means its detected, otherwise amount of detection fails in a row

        self.command_queue = Queue(maxsize=C.COMMAND_QUEUE_MAXSIZE)
        self.overlay = ScreenOverlayProcess(self.command_queue)

        self.overlay.start()

    @staticmethod
    def is_pos_onscreen(pos) -> bool:
        if pos[0] < 0 or pos[1] < 0 or pos[0] > C.MONITOR_RESOLUTION[0] or pos[1] > C.MONITOR_RESOLUTION[1]:
            return False
        return True

    def lefthand_onchange(self, val: Optional[Tuple[int, int]]):
        # hand was moved!
        if val is None:
            # no hand was detected
            self.left_hand_detected.value += 1

        else:
            assert not (None in val)
            # hand was detected somewhere
            self.left_hand_detected.value = -1

            if self.is_pos_onscreen(val):
                # hand was detected and is on screen:
                self.command_queue.put(('highlighter_pos', val))
                pyautogui.moveTo(*val)
            else:
                # hand detected outside screen:
                pass


    def lefthanddetected_onchange(self, val: int):
        # hand was new detected:
        if val == -1:
            self.send_command(('highlighter_visible', True))

        elif val > C.INAROW_HAND_DETECTION_FAILS:
            self.send_command(('highlighter_visible', False))
            pyautogui.mouseUp()

    def righthand_onchange(self, val: Optional[Tuple[int, int]]):
    # right hand was moved:
        if val is None:
            # right hand was undetected:
            self.right_hand_detected.value += 1

        else:
            assert not (None in val)

            self.right_hand_detected.value = -1
            # right hand was detected somewhere

            if self.left_hand_pos.value and self.is_pos_onscreen(self.left_hand_pos.value):
                # check if right hand is within radius and a left hand is also detected
                self.send_command(('second_hand_pos', val))
                if math.dist(val, self.left_hand_pos.value) <= C.HAND_CURSOR_CLICK_DISTANCE and self.is_pos_onscreen(self.left_hand_pos.value):
                    self.mouse_pressed.value = True
                else:
                    self.mouse_pressed.value = False

    def righthanddetected_onchange(self, val: int):
        if val == -1:
            # hand was newly detected:
            pass

        elif val >= C.INAROW_HAND_DETECTION_FAILS:
            self.mouse_pressed.value = False
            self.send_command(('second_hand_pos', self.left_hand_pos.value)) # this means there won't be any line drawn on the overlay

    def mousepressed_onchange(self, val: bool):
        if val:
           pyautogui.mouseDown()
           self.send_command(('highlighter_state', True))
        else:
            pyautogui.mouseUp()
            self.send_command(('highlighter_state', False))


    def send_command(self, command):
        try:
            self.command_queue.put(command)
            return True
        except queue.Full:
            # return False
            assert False  # Only for debugging TODO

    def __del__(self):
        self.command_queue.put(('stop', ))


import config as C
import pyautogui
import math


class _StandardMode2:
    def __init__(self):
        # Initialize the positions to None, indicating no detection.
        self.left_hand_pos = None
        self.right_hand_pos = None

        # Initialize mouse_pressed to False
        self.mouse_pressed = False

        # Initialize counters for consecutive detection failures.
        self.left_hand_fail_counter = 0
        self.right_hand_fail_counter = 0

        self.command_queue = multiprocessing.Queue(maxsize=C.COMMAND_QUEUE_MAXSIZE)
        self.overlay = ScreenOverlayProcess(self.command_queue)
        self.overlay.start()

    @staticmethod
    def normalize_position(pos):
        """Convert the position to a tuple of ints."""
        if pos is None:
            return None
        return (int(pos[0]), int(pos[1]))

    def update_positions(self, left_hand_pos: Optional[tuple[int, int]], right_hand_pos: Optional[tuple[int, int]]):
        """
        Update the positions of the left and right hands.
        Increment or reset detection failure counters accordingly.

        Args:
        - left_hand_pos (tuple or None): New position for the left hand or None if not detected.
        - right_hand_pos (tuple or None): New position for the right hand or None if not detected.
        """

        # Normalize positions
        left_hand_pos = self.normalize_position(left_hand_pos)
        right_hand_pos = self.normalize_position(right_hand_pos)

        # Update left hand position and move the cursor
        if left_hand_pos is not None and self.is_pos_onscreen(left_hand_pos):
            pyautogui.moveTo(left_hand_pos[0], left_hand_pos[1])
            # Send the highlighter position to the overlay process
            self.send_command(('highlighter_pos', left_hand_pos))
        else:
            # If left hand is not detected, set highlighter position to None
            self.send_command(('highlighter_pos', None))

        # Handle detection failures for left hand
        if left_hand_pos is None:
            self.left_hand_fail_counter += 1
        else:
            self.left_hand_fail_counter = 0
            self.left_hand_pos = left_hand_pos

        # Handle detection failures for right hand
        if right_hand_pos is None:
            self.right_hand_fail_counter += 1
        else:
            self.right_hand_fail_counter = 0
            self.right_hand_pos = right_hand_pos

            # Send the position of the right hand to the overlay process
            self.send_command(('second_hand_pos', right_hand_pos))

        # Check if a hand is considered undetected based on the threshold
        if self.left_hand_fail_counter >= C.INAROW_HAND_DETECTION_FAILS:
            self.left_hand_pos = None

        if self.right_hand_fail_counter >= C.INAROW_HAND_DETECTION_FAILS:
            self.right_hand_pos = None
            pyautogui.mouseUp()
            # If right hand is not detected, set second hand position to None
            self.send_command(('second_hand_pos', None))

        # State handling for right hand
        if self.left_hand_pos is not None and self.right_hand_pos is not None:
            distance = math.dist(self.left_hand_pos, self.right_hand_pos)
            if distance <= C.HAND_CURSOR_CLICK_DISTANCE:
                if not self.mouse_pressed:
                    pyautogui.mouseDown()
                    sleep(.1)
                    self.mouse_pressed = True
                # Toggle the state of the highlighter when hands are close
                self.send_command(('highlighter_state', True))
            else:
                if self.mouse_pressed:
                    pyautogui.mouseUp()
                    self.mouse_pressed = False
                # Toggle the state of the highlighter when hands are apart
                self.send_command(('highlighter_state', False))

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
            assert False
            # return False TODO


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



import unittest
import config as C
import pyautogui

from unittest.mock import patch

from unittest.mock import patch


class TestHandStateHandlerTransitions(unittest.TestCase):

    def setUp(self):
        self.handler = Controller()

    @patch('pyautogui.mouseDown')
    @patch('pyautogui.mouseUp')
    @patch('pyautogui.moveTo')
    def test_LH_detected_move_cursor(self, mock_moveTo, mock_mouseUp, mock_mouseDown):
        self.handler.update_positions((500, 500), None)
        mock_moveTo.assert_called_with(500, 500)

    @patch('pyautogui.mouseDown')
    @patch('pyautogui.mouseUp')
    def test_close_to_far_with_click(self, mock_mouseUp, mock_mouseDown):
        self.handler.update_positions((500, 500), (520, 520))
        mock_mouseDown.assert_called_once()

        self.handler.update_positions((500, 500), (800, 800))
        mock_mouseUp.assert_called_once()

    @patch('pyautogui.mouseDown')
    @patch('pyautogui.mouseUp')
    def test_far_to_close_with_click(self, mock_mouseUp, mock_mouseDown):
        self.handler.update_positions((500, 500), (800, 800))
        mock_mouseDown.assert_not_called()

        self.handler.update_positions((500, 500), (520, 520))
        mock_mouseDown.assert_called_once()

    @patch('pyautogui.mouseDown')
    @patch('pyautogui.mouseUp')
    def test_RH_detected_to_undetected_with_click(self, mock_mouseUp, mock_mouseDown):
        self.handler.update_positions((500, 500), (520, 520))
        mock_mouseDown.assert_called_once()

        for _ in range(C.INAROW_HAND_DETECTION_FAILS):
            self.handler.update_positions((500, 500), None)
        mock_mouseUp.assert_called_once()

    @patch('pyautogui.mouseDown')
    @patch('pyautogui.mouseUp')
    def test_RH_undetected_to_detected_close_with_click(self, mock_mouseUp, mock_mouseDown):
        for _ in range(C.INAROW_HAND_DETECTION_FAILS):
            self.handler.update_positions((500, 500), None)
        mock_mouseDown.assert_not_called()

        self.handler.update_positions((500, 500), (520, 520))
        mock_mouseDown.assert_called_once()

    @patch('pyautogui.mouseDown')
    @patch('pyautogui.mouseUp')
    def test_LH_undetected_RH_detected(self, mock_mouseUp, mock_mouseDown):
        self.handler.update_positions(None, (600, 600))
        mock_mouseDown.assert_not_called()
        mock_mouseUp.assert_not_called()

    @patch('pyautogui.mouseDown')
    @patch('pyautogui.mouseUp')
    def test_both_hands_undetected_with_click(self, mock_mouseUp, mock_mouseDown):
        self.handler.update_positions((500, 500), (520, 520))
        mock_mouseDown.assert_called_once()

        for _ in range(C.INAROW_HAND_DETECTION_FAILS):
            self.handler.update_positions(None, None)
        mock_mouseUp.assert_called_once()

    @patch('pyautogui.mouseDown')
    @patch('pyautogui.mouseUp')
    def test_RH_detected_to_far_with_click(self, mock_mouseUp, mock_mouseDown):
        self.handler.update_positions((500, 500), (520, 520))
        mock_mouseDown.assert_called_once()

        self.handler.update_positions((500, 500), (800, 800))
        mock_mouseUp.assert_called_once()

    def test_left_hand_movement(self):
        # Simulate left hand moving to a position on screen
        self.handler.update_positions((500, 500), None)
        command = self.handler.command_queue.get()
        self.assertEqual(command, ('highlighter_pos', (500, 500)))

    def test_right_hand_near_left(self):
        # Simulate right hand being near the left hand
        self.handler.update_positions((500, 500), (520, 520))
        command = self.handler.command_queue.get()  # This fetches the left hand command
        self.assertEqual(command, ('highlighter_pos', (500, 500)))

        command = self.handler.command_queue.get()  # This fetches the right hand command
        self.assertEqual(command, ('second_hand_pos', (520, 520)))

        command = self.handler.command_queue.get()  # This fetches the highlighter state command
        self.assertEqual(command, ('highlighter_state', True))

    def test_right_hand_far_from_left(self):
        # Simulate right hand being far from the left hand
        self.handler.update_positions((500, 500), (800, 800))
        command = self.handler.command_queue.get()  # This fetches the left hand command
        self.assertEqual(command, ('highlighter_pos', (500, 500)))

        command = self.handler.command_queue.get()  # This fetches the right hand command
        self.assertEqual(command, ('second_hand_pos', (800, 800)))

        command = self.handler.command_queue.get()  # This fetches the highlighter state command
        self.assertEqual(command, ('highlighter_state', False))

    def test_no_hands_detected(self):
        # Simulate no hands being detected
        self.handler.update_positions(None, None)
        command = self.handler.command_queue.get()
        self.assertEqual(command, ('highlighter_pos', None))

        command = self.handler.command_queue.get()
        self.assertEqual(command, ('second_hand_pos', None))

    # ... Add any additional transition tests as needed ...


if __name__ == '__main__':
    unittest.main()
