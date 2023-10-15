import config as C
import win32gui, win32con, win32api
import multiprocessing
from collections import namedtuple
from custom_utils import find_ring_intersection
from time import sleep
import ctypes

class ScreenOverlay(multiprocessing.Process):
    @staticmethod
    def WindowProc(hwnd, msg, wParam, lParam):
        if msg == win32con.WM_CLOSE:
            print("window closed")
            win32gui.PostQuitMessage(0)  # This will exit the message loop
            return 0
        return win32gui.DefWindowProc(hwnd, msg, wParam, lParam)
    def __init__(self, data_queue: multiprocessing.Queue):
        super().__init__()
        self.data_queue = data_queue

        self.highlighter_pos = (200, 200) # TODO: set to None at start
        self.highlighter_state = False  # False for non-clicked, True for clicked
        self.second_hand_pos = False

        self.transparent_color = win32api.RGB(1, 1, 1)  # Example: Magenta as transparent color
        self.hwnd = self.create_window()

    def create_window(self):
        wnd_class = win32gui.WNDCLASS()
        h_inst = wnd_class.hInstance = win32api.GetModuleHandle(None)
        wnd_class.lpszClassName = "LayeredWindowClass"
        wnd_class.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
        wnd_class.lpfnWndProc = self.WindowProc  # Set to custom window procedure
        wnd_class.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        class_atom = win32gui.RegisterClass(wnd_class)

        hwnd = win32gui.CreateWindowEx(
            win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST,
            class_atom,
            "Layered Window",
            win32con.WS_OVERLAPPEDWINDOW | win32con.WS_VISIBLE | win32con.WS_MAXIMIZE,
            0,  # x position
            0,  # y position
            C.MONITOR_RESOLUTION[0], C.MONITOR_RESOLUTION[1],
            0, 0, h_inst, None
        )

        win32gui.SetLayeredWindowAttributes(hwnd, self.transparent_color, 0, win32con.LWA_COLORKEY)


        return hwnd

    def run(self):
        while True:
            # get data
            latest = self.data_queue.get(block=True)

            self.process_command(latest)

    def process_command(self, command: namedtuple):
        ''' command_template = {
            'highlighter_pos', (int, int) || None
            'highlighter_state', bool  # Toggle the State of the inner ring
            'second_hand_pos', (int, int) || None
            'stop', Any
        } '''

        match command[0], command[1]:
            case 'debug_draw', value:
                self.fill_transparent()

                self.draw()

            case 'highlighter_pos', value:
                self.highlighter_pos = value

            case 'highlighter_state', value:
                self.highlighter_state = value

            case 'second_hand_pos', value:
                self.second_hand_pos = value

            case 'stop', _:
                raise SystemExit(f"Thread {multiprocessing.current_process().name} exited due to a stop command.")

            case wrong_command, value:
                raise Exception(f"The used command in thread {multiprocessing.current_process().name} could not be processed \nCommand: '{wrong_command}':{value}")

            case _:
                raise Exception(f"The used command in thread {multiprocessing.current_process().name} has wrong format/type")

        self.draw()

    def fill_transparent(self):
        # Fill the window with magenta color before showing
        hdc = win32gui.GetDC(self.hwnd)
        brush = win32gui.CreateSolidBrush(self.transparent_color)
        win32gui.FillRect(hdc, (0, 0, C.MONITOR_RESOLUTION[0], C.MONITOR_RESOLUTION[1]), brush)
        win32gui.DeleteObject(brush)
        win32gui.ReleaseDC(self.hwnd, hdc)
        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)

    def draw(self):
        self.fill_transparent()
        # draw objects:

        # draw highlighter ring:
        if self.highlighter_pos:
            self.draw_ring(
                pos=self.highlighter_pos,
                radius=C.HAND_CURSOR_CLICK_DISTANCE,
                color=win32api.RGB(*(C.MAIN_ACTIVE_COLOR if self.highlighter_state else C.MAIN_INACTIVE_COLOR)),
                thickness=C.LINE_WIDTH
            )

        # second hand position highlighting
        if self.highlighter_state and self.second_hand_pos:
            assert self.second_hand_pos[0] and self.second_hand_pos[1]  # if the code works this shouldn't be thrown ever ...

            endpos = tuple(int(x) for x in (find_ring_intersection(self.second_hand_pos, self.highlighter_pos, C.HAND_CURSOR_CLICK_DISTANCE)))
            print(endpos)
            self.draw_line(
                start_pos=self.second_hand_pos,
                end_pos=tuple(int(x) for x in (find_ring_intersection(self.second_hand_pos, self.highlighter_pos, C.HAND_CURSOR_CLICK_DISTANCE))),
                color=win32api.RGB(C.SECOND_COLOR),
                thickness=C.LINE_WIDTH
            )

    def draw_ring(self, pos, radius, thickness, color):
        hdc = win32gui.GetDC(self.hwnd)

        brush = win32gui.CreateSolidBrush(color)
        outer_radius = radius + thickness
        inner_radius = radius

        # Draw outer circle
        win32gui.SelectObject(hdc, brush)
        win32gui.Ellipse(hdc, pos[0] - outer_radius, pos[1] - outer_radius, pos[0] + outer_radius,
                         pos[1] + outer_radius)

        # Draw inner circle with transparent color to make it hollow
        brush_transparent = win32gui.CreateSolidBrush(self.transparent_color)
        win32gui.SelectObject(hdc, brush_transparent)
        win32gui.Ellipse(hdc, pos[0] - inner_radius, pos[1] - inner_radius, pos[0] + inner_radius,
                         pos[1] + inner_radius)

        win32gui.DeleteObject(brush)
        win32gui.DeleteObject(brush_transparent)
        win32gui.ReleaseDC(self.hwnd, hdc)

    def draw_line(self, start_pos, end_pos, thickness, color):
        hdc = win32gui.GetDC(self.hwnd)

        brush = win32gui.CreateSolidBrush(color)

        win32gui.SelectObject(hdc, brush)
        win32gui.Polyline(start_pos, end_pos)

        win32gui.DeleteObject(brush)
        win32gui.ReleaseDC(self.hwnd, hdc)


from multiprocessing import Queue

def debug_screen_overlay():
    debug_queue = Queue()
    overlay = ScreenOverlay(debug_queue)

    overlay.process_command(('debug_draw', ((50, 50), 100, 3, win32api.RGB(255, 0, 0))))

    win32gui.PumpMessages()

if __name__ == "__main__":
    debug_screen_overlay()

