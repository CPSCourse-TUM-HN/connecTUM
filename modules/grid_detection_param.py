import numpy as np

# Camera
BUILT_IN_WEBCAM = 0
EXTERNAL_WEBCAM = 1
DEFAULT_CAMERA = BUILT_IN_WEBCAM

# Board Dimension
BOARD_WIDTH = 189
BOARD_HEIGHT = 139
CIRCLE_RADIUS = 8.75
PADDING_TOP = 7
PADDING_SIDE = 7.75
DESCALE_FACTOR = 1

ROWS = 6
COLUMNS = 7

# Color Ranges
RED_L = np.array([0, 110, 110], np.uint8)
RED_U = np.array([5, 255, 255], np.uint8)

RED_HR_L = np.array([160, 110, 110], np.uint8)
RED_HR_U = np.array([180, 255, 255], np.uint8)

YELLOW_L = np.array([25, 90, 90], np.uint8)
YELLOW_U = np.array([40, 200, 200], np.uint8)

BLUE_L = np.array([100, 150, 50], np.uint8)
BLUE_U = np.array([130, 255, 255], np.uint8)

# Noise red range
RED_NOISE_L = np.array([0, 15, 0], np.uint8)    # low saturation, low value
RED_NOISE_U = np.array([10, 255, 170], np.uint8)  # not bright reds
