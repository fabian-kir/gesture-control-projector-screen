import win32gui
import win32con
import win32api

import config as C

class LayeredWindow:
    def __init__(self):
        self.transparent_color = win32api.RGB(1, 1, 1)  # Example: Magenta as transparent color
        self.hwnd = self.create_window()

    def create_window(self):
        wnd_class = win32gui.WNDCLASS()
        h_inst = wnd_class.hInstance = win32api.GetModuleHandle(None)
        wnd_class.lpszClassName = "LayeredWindowClass"
        wnd_class.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
        wnd_class.lpfnWndProc = WindowProc  # Set to custom window procedure
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

        return hwnd

    def draw_ring(self, pos, radius, thickness, color):
        self.fill_transparent()

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

    def show(self):
        # Fill the window with magenta color before showing
        hdc = win32gui.GetDC(self.hwnd)
        brush = win32gui.CreateSolidBrush(self.transparent_color)
        win32gui.FillRect(hdc, (0, 0, 300, 300), brush)
        win32gui.DeleteObject(brush)
        win32gui.ReleaseDC(self.hwnd, hdc)
        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)

    def update(self):
        win32gui.SetLayeredWindowAttributes(self.hwnd, self.transparent_color, 0, win32con.LWA_COLORKEY)

    def erase(self):
        pass  # Implement as needed.

    def fill_transparent(self):
        hdc = win32gui.GetDC(self.hwnd)
        brush = win32gui.CreateSolidBrush(self.transparent_color)
        win32gui.FillRect(hdc, (
        0, 0, win32api.GetSystemMetrics(win32con.SM_CXSCREEN), win32api.GetSystemMetrics(win32con.SM_CYSCREEN)), brush)
        win32gui.DeleteObject(brush)
        win32gui.ReleaseDC(self.hwnd, hdc)


def WindowProc(hwnd, msg, wParam, lParam):
    if msg == win32con.WM_CLOSE:
        print("window closed")
        win32gui.PostQuitMessage(0)  # This will exit the message loop
        return 0
    return win32gui.DefWindowProc(hwnd, msg, wParam, lParam)


# Running the window in its main loop
if __name__ == "__main__":
    window = LayeredWindow()
    window.show()
    window.update()

    # Draw a ring at (400, 300) with radius 100, thickness 20, and color red
    window.draw_ring((400, 300), 100, 20, win32api.RGB(255, 0, 0))

    win32gui.PumpMessages()
