MODE = "standard" # ["standard", "presentation"]
DEBUG = True

MONITOR = 0 # Falls mehrere Monitore an den Computer angeschlossen sind, muss diese Zahl ggf. angepasst werden
CAMERA_INPUT = 1

MONITOR_RESOLUTION = (3840, 2160)

GOOD_MATCH_CALIB_VAL = .45

ND_ARRAY_WIDTH = 8  # 2-8, higher -> better, slower
TRESHOLD = .00001  # .1 - .00001, lower -> better, slower

# NEW_HAND_MOVE_DIVIATION_TRESHOLD = 20# measured in pixels
GESTURE_DETECTION_CONTEXT_LEN = 12
MINIMAL_GESTURE_DETECTION_POINTS = 4
GESTURE_DETECTION_TOLERANCE = 1.83

HAND_CURSOR_CLICK_DISTANCE = 375 #in px

INAROW_HAND_DETECTION_FAILS = 20  # After the hand detection was x times not able to detect a hand, we expect that the hand moved out of the camera area

# Overlay Style:
MAIN_ACTIVE_COLOR = (255, 0, 0)
MAIN_INACTIVE_COLOR = (0, 255, 255)
SECOND_COLOR = (0, 0, 255)
LINE_WIDTH = 20

COMMAND_QUEUE_MAXSIZE = 15

#Presentation Mode:
PRESENTATION_ACTION_AREA_WIDTH = .15 # % amount of the screen at the left and right end (each) where next or previous slide actions are recognized
PRESENTATION_ACTION_AREA_HEIGHT = .2 # % amount of the screen at the top where next or previous slide actions are recognized

PRESENTATION_LINK = "" # link to a public presentation
PRESENTATION_TOOL = None # one of "KEYNOTE";