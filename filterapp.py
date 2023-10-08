import config as C
import tkinter as tk
import pyautogui
import math
import pygame as pyg
import win32gui, win32con, win32api
import threading


class TransparentWindow:
    def __init__(self):
        self.screen = pyg.display.set_mode(C.MONITOR_RESOLUTION, pyg.FULLSCREEN)
        self.aux_surface = pyg.Surface(C.MONITOR_RESOLUTION, flags=pyg.SRCALPHA)
        self.TRANSPARENCY_COLOR = (1, 1, 1)
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.YELLOW = (0, 255, 255)
        self.BLUE = (0, 0, 255)

        hwnd = pyg.display.get_wm_info()["window"]

        # Get the current extended style of the window
        ex_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)

        # Add WS_EX_LAYERED, WS_EX_TOPMOST, and WS_EX_TRANSPARENT to the window's extended style
        ex_style |= win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST | win32con.WS_EX_TRANSPARENT

        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, ex_style)
        win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*self.TRANSPARENCY_COLOR), 0, win32con.LWA_COLORKEY)

        self.screen.fill((0, 0, 255))
        self.screen.fill(self.TRANSPARENCY_COLOR)

        self.click_aux_surf = pyg.Surface(C.MONITOR_RESOLUTION, flags=pyg.SRCALPHA)
        self.hand_position = (0, 0)

        # Start a thread to periodically set the window to the topmost layer
        threading.Thread(target=self.keep_window_on_top, args=(hwnd,)).start()

    def keep_window_on_top(self, hwnd):
        while True:
            win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0,
                                  win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
            pyg.time.wait(100)  # Wait for 100 milliseconds before setting again

    def draw_highlighter(self):
        cursor_pos = pyautogui.position()

        # No hand was detected
        if self.hand_position is None:
            self.screen.fill(self.TRANSPARENCY_COLOR)
            pyg.display.update()
            return

        # left hand was detected but to far away
        if math.dist(self.hand_position, cursor_pos) > C.HAND_CURSOR_CLICK_DISTANCE:
            pyg.draw.circle(self.aux_surface, self.YELLOW, pyautogui.position(), C.HAND_CURSOR_CLICK_DISTANCE, 10)
        # left hand was detected close enough for a click
        else:
            pyg.draw.circle(self.aux_surface, self.RED, pyautogui.position(), C.HAND_CURSOR_CLICK_DISTANCE, 10)

        self.screen.blit(self.aux_surface, (0, 0))


        pyg.display.update()
        self.screen.fill(self.TRANSPARENCY_COLOR)
        self.aux_surface.fill((0, 0, 0, 0))  # Clear auxiliary surface with transparency


    def update_hand_position(self, hand_pos):
        if hand_pos is None:
            self.hand_position = None

        self.hand_position = hand_pos
        r = math.dist(hand_pos, pyautogui.position())

        pyg.draw.circle(self.aux_surface, self.BLUE, pyautogui.position(), r, 10)