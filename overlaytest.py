from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame as pyg
from time import sleep
from multiprocessing import Process, Queue
import tkinter as tk
from ctypes import windll
import win32api
import win32con
import win32gui

import config as C
import pyautogui

SetWindowPos = windll.user32.SetWindowPos


class FilterApp:
    '''def __init__(self):
        self.active = False
        self.pos2 = (0, 0)

        self.screen = pyg.display.set_mode(C.MONITOR_RESOLUTION, pyg.FULLSCREEN)
        self.TRANSPARENCY_COLOR = (1, 1, 1)

        hwnd = pyg.display.get_wm_info()["window"]
        win32gui.SetWindowLong(
            hwnd,
            win32con.GWL_EXSTYLE,
            win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST
        )
        win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*self.TRANSPARENCY_COLOR), 0, win32con.LWA_COLORKEY)
        self.screen.fill((0, 0, 255))
        self.screen.fill(self.TRANSPARENCY_COLOR)
    '''

    def __init__(self):
        self.active = False
        self.pos2 = (0, 0)

        # Transparency
        # Set up pygame display in a windowed mode with the desired resolution
        self.screen = pyg.display.set_mode(C.MONITOR_RESOLUTION, pyg.NOFRAME)
        self.TRANSPARENCY_COLOR = (1, 1, 1)

        # Retrieve the window handle created by pygame
        hwnd = pyg.display.get_wm_info()["window"]

        # Set window to be topmost, layered, and transparent
        extended_style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, win32gui.GetWindowLong(
            hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)

        # Set layered window attributes for transparency
        win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(*self.TRANSPARENCY_COLOR), 0, win32con.LWA_COLORKEY)

        # Fill screen with a solid color, then apply transparency color
        self.screen.fill((0, 0, 255))
        self.screen.fill(self.TRANSPARENCY_COLOR)


        # Always on Top
        win32gui.SetWindowPos(hwnd, -1, 1, 1, 0, 0, 1)
        #                                     x  y              - window pos

    def set_topmost(self):
        NOSIZE = 1
        NOMOVE = 2
        TOPMOST = -1

        hwnd = pyg.display.get_wm_info()['window']
        SetWindowPos(hwnd, TOPMOST, 0, 0, 0, 0, NOMOVE | NOSIZE)

    def draw(self):
        self.screen.fill(
            self.TRANSPARENCY_COLOR
        )

        pos1 = pyautogui.position()

        pyg.draw.circle(
            surface=self.screen,
            color=C.MAIN_ACTIVE_COLOR if self.active else C.MAIN_INACTIVE_COLOR,
            center=pos1,
            radius=C.HAND_CURSOR_CLICK_DISTANCE,
        )

        pyg.draw.line(
            surface=self.screen,
            color=C.SECOND_COLOR,
            width=C.LINE_WIDTH,
            start_pos=self.pos2,
            end_pos=pos1
        )

        pyg.draw.circle(
            surface=self.screen,
            color=self.TRANSPARENCY_COLOR,
            center=pos1,
            radius=C.HAND_CURSOR_CLICK_DISTANCE - C.LINE_WIDTH
        )

        pyg.display.update()
        self.set_topmost()

    def event_processing(self):
        self.draw()

        for event in pyg.event.get():
            if event.type == pyg.QUIT:
                exit()

