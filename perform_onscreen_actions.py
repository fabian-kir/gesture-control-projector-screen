import math
import multiprocessing
import queue
import warnings
from time import sleep
from typing import Optional

import pyautogui

from filterapp import ScreenOverlayProcess

pyautogui.PAUSE = 0

pyautogui.FAILSAFE = False


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
        self.mouse_pressed = False

        # Initialize counters for consecutive detection failures.
        self.left_hand_fail_counter = 0
        self.right_hand_fail_counter = 0

        self.overlay = ScreenOverlayProcess(self.command_queue)
        self.overlay.start()

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

        # Check if there's a change in left hand position
        if left_hand_pos != self.left_hand_pos:
            # Send the highlighter position to the overlay process
            self.send_command(('highlighter_pos', left_hand_pos))

            self.left_hand_pos = left_hand_pos
            # Update left hand position and move the cursor
            if left_hand_pos is not None and self.is_pos_onscreen(left_hand_pos):
                pyautogui.moveTo(left_hand_pos[0], left_hand_pos[1])

        # Check if there's a change in right hand position
        if right_hand_pos != self.right_hand_pos:
            # Send the position of the right hand to the overlay process
            self.send_command(('second_hand_pos', right_hand_pos))

            self.right_hand_pos = right_hand_pos
            # Handle detection failures for right hand
            if right_hand_pos is None:
                self.right_hand_fail_counter += 1
            else:
                self.right_hand_fail_counter = 0

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
                    print("mousedown")
                    sleep(.05)
                    self.mouse_pressed = True
                    # Toggle the state of the highlighter when hands are close
                    self.send_command(('highlighter_state', True))  # only send on state change
            else:
                if self.mouse_pressed:
                    print("mouseup")
                    pyautogui.mouseUp()
                    self.mouse_pressed = False

                    # Toggle the state of the highlighter when hands are apart
                    self.send_command(('highlighter_state', False))


import unittest
import config as C
import pyautogui

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
