import config as C
import win32gui, win32con, win32api
import multiprocessing
from collections import namedtuple
from custom_utils import find_ring_intersection

class ScreenOverlay(multiprocessing.Process):
    def __init__(self, data_queue: multiprocessing.Queue):
        super().__init__()
        self.data_queue = data_queue

        self.create_window()

        self.highlighter_pos = None
        self.highlighter_state = False # False for non-clicked, True for clicked
        self.second_hand_pos = False

    def create_window(self):  # init methode
        # Create a layered window that covers the entire screen
        self.hwnd = win32gui.CreateWindowEx(
            win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST | win32con.WS_EX_TRANSPARENT,
            "Static",
            None,
            win32con.WS_POPUP | win32con.WS_VISIBLE,
            0, 0, win32api.GetSystemMetrics(win32con.SM_CXSCREEN),
            win32api.GetSystemMetrics(win32con.SM_CYSCREEN),
            None,
            None,
            None,
            None
        )
        # Set the layered window attributes to be transparent
        win32gui.SetLayeredWindowAttributes(self.hwnd, win32api.RGB(0, 0, 0), 0, win32con.LWA_COLORKEY)
        # Get the device context of the window
        self.hdc = win32gui.GetDC(self.hwnd)

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

    def draw(self):
        self.erase()

        # draw objects:

        # draw highlighter ring:
        self.draw_ring(
            pos=self.highlighter_pos,
            radius=C.HAND_CURSOR_CLICK_DISTANCE,
            color=(C.MAIN_ACTIVE_COLOR if self.highlighter_state else C.MAIN_INACTIVE_COLOR),
            thickness=C.LINE_WIDTH
        )

        # second hand position highlighting
        if not self.highlighter_state:
            endpos = tuple(int(x) for x in (find_ring_intersection(self.second_hand_pos, self.highlighter_pos, C.HAND_CURSOR_CLICK_DISTANCE)))
            print(endpos)
            self.draw_line(
                start_pos=self.second_hand_pos,
                end_pos=tuple(int(x) for x in (find_ring_intersection(self.second_hand_pos, self.highlighter_pos, C.HAND_CURSOR_CLICK_DISTANCE))),
                color=C.SECOND_COLOR,
                thickness=C.LINE_WIDTH
            )

        self.update()

    def draw_ring(self, pos, radius, color=(255, 0, 0), thickness=1):
        x, y = pos

        """Draw a ring with a specified center, radius, color, and thickness."""
        pen = win32gui.CreatePen(win32con.PS_SOLID, thickness, win32api.RGB(*color))
        win32gui.SelectObject(self.hdc, pen)
        win32gui.Ellipse(self.hdc, x - radius, y - radius, x + radius, y + radius)
        win32gui.Ellipse(self.hdc, x - radius + thickness, y - radius + thickness, x + radius - thickness, y + radius - thickness)

    def draw_circle(self, x, y, radius, color=(255, 0, 0)):
        """Draw a filled circle with a specified center, radius, and color."""
        brush = win32gui.CreateSolidBrush(win32api.RGB(*color))
        win32gui.SelectObject(self.hdc, brush)
        win32gui.Ellipse(self.hdc, x - radius, y - radius, x + radius, y + radius)

    def draw_rect(self, left, top, right, bottom, color=(255, 0, 0)):
        """Draw a rectangle with specified coordinates and color."""
        brush = win32gui.CreateSolidBrush(win32api.RGB(*color))
        win32gui.SelectObject(self.hdc, brush)
        win32gui.Rectangle(self.hdc, left, top, right, bottom)

    def draw_pixel(self, x, y, color=(255, 0, 0)):
        """Draw a pixel with a specified location and color."""
        win32gui.SetPixel(self.hdc, x, y, win32api.RGB(*color))

    def draw_line(self, start_pos, end_pos, color=(255, 0, 0), thickness=1):
        x1, y1 = start_pos
        x2, y2 = end_pos
        """Draw a line between two points with a specified color and thickness."""
        pen = win32gui.CreatePen(win32con.PS_SOLID, thickness, win32api.RGB(*color))
        win32gui.SelectObject(self.hdc, pen)
        win32gui.MoveToEx(self.hdc, x1, y1, None)
        win32gui.LineTo(self.hdc, x2, y2)

    def erase(self):
        """Erase all drawn objects on the DC without updating the window."""
        transparent_brush = win32gui.CreateSolidBrush(win32api.RGB(0, 0, 0))
        win32gui.FillRect(self.hdc, (
        0, 0, win32api.GetSystemMetrics(win32con.SM_CXSCREEN), win32api.GetSystemMetrics(win32con.SM_CYSCREEN)),
                          transparent_brush)

    def update(self):
        """Update the window to reflect the changes made on the DC."""
        win32gui.UpdateLayeredWindow(self.hwnd, None, None, None, self.hdc, None, 0, None, win32con.ULW_ALPHA)


from multiprocessing import Queue


def debug_screen_overlay():
    # Initialize
    data_queue = Queue()
    overlay = ScreenOverlay(data_queue)

    # Test create_window
    overlay.create_window()
    assert overlay.hwnd is not None, "Window handle should not be None after creation."
    assert overlay.hdc is not None, "Device context should not be None after window creation."
    print("create_window passed!")

    # Test process_command for highlighter_pos
    data_queue.put(('highlighter_pos', (10, 20)))
    overlay.process_command(data_queue.get())
    assert overlay.highlighter_pos == (10, 20), "Highlighter position should be set to (10, 20)."
    print("process_command for highlighter_pos passed!")

    # Test process_command for highlighter_state
    data_queue.put(('highlighter_state', True))
    overlay.process_command(data_queue.get())
    assert overlay.highlighter_state == True, "Highlighter state should be set to True."
    print("process_command for highlighter_state passed!")

    # Test process_command for second_hand_pos
    data_queue.put(('second_hand_pos', (30, 40)))
    overlay.process_command(data_queue.get())
    assert overlay.second_hand_pos == (30, 40), "Second hand position should be set to (30, 40)."
    print("process_command for second_hand_pos passed!")

    # Test process_command for invalid command
    try:
        data_queue.put(('invalid_command', None))
        overlay.process_command(data_queue.get())
    except Exception as e:
        print(f"Caught expected exception for invalid command: {e}")

    # Cleanup
    win32gui.DeleteObject(overlay.hdc)
    win32gui.DestroyWindow(overlay.hwnd)
    print("Cleanup done!")


if __name__ == "__main__":
    debug_screen_overlay()

