import cv2
import numpy as np
import math

from modules import grid_detection_param as param

class Grid:
    def __init__(self, max_frame, sucess_rate):
        self.frame_count = 0
        self.grid = np.zeros((6, 7), dtype=int)
        self.computed_grid = np.zeros((6, 7), dtype=int)

        self.max_frame = max_frame
        self.sucess_rate = sucess_rate

        self.h = None
        self.w = None
        
        self.scale_ratio = None
        self.start_rect = None
        self.end_rect = None
        self.min_circle = None
        self.max_circle = None

    def resize(self, new_h, new_w):
        # Get image size and ratio for the board mask
        self.scale_ratio = math.floor(new_h / param.BOARD_HEIGHT) - param.DESCALE_FACTOR

        self.start_rect = (round(new_w / 2 - param.BOARD_WIDTH * self.scale_ratio / 2),
                           round(new_h / 2 - param.BOARD_HEIGHT * self.scale_ratio / 2))
        self.end_rect = (round(self.start_rect[0] + param.BOARD_WIDTH * self.scale_ratio),
                         round(self.start_rect[1] + param.BOARD_HEIGHT * self.scale_ratio))

        self.min_circle = (self.start_rect[0] + round((param.PADDING_SIDE + param.CIRCLE_RADIUS) * self.scale_ratio),
                           self.start_rect[1] + round((param.PADDING_TOP + param.CIRCLE_RADIUS) * self.scale_ratio))
        self.max_circle = (self.end_rect[0] - round((param.PADDING_SIDE + param.CIRCLE_RADIUS) * self.scale_ratio),
                           self.end_rect[1] - round((param.PADDING_TOP + param.CIRCLE_RADIUS) * self.scale_ratio))

        self.cell_w = (self.max_circle[0] - self.min_circle[0]) / (param.COLUMNS - 1)
        self.cell_h = (self.max_circle[1] - self.min_circle[1]) / (param.ROWS - 1)

    def compute_grid(self, mask_array, img):
        if len(mask_array) != 2:
            return
        
        # Detect and map red (-1) and yellow (1) circles
        self.detect_and_map(mask_array[0], -1, img)
        self.detect_and_map(mask_array[1], 1, img)

        self.grid_accumulator()

    # Smooth out grid result over max_frame
    # To be counted, a coin should appear at least max_frame*success_rate times
    def grid_accumulator(self):
        if self.frame_count < self.max_frame:
            self.frame_count += 1
            return

        self.computed_grid = np.zeros((param.ROWS, param.COLUMNS), dtype=int)

        for i in range(param.ROWS):
            for j in range(param.COLUMNS):
                if abs(self.grid[i][j]) >= self.max_frame * self.sucess_rate:
                    self.computed_grid[i][j] = 1 if self.grid[i][j] < 0 else 2

        self.frame_count = 0
        self.grid = np.zeros((6, 7), dtype=int)

    # Detect coins and map them to a grid position
    def detect_and_map(self, mask, value, img):
        blurred = cv2.GaussianBlur(mask, (9, 9), 2)
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT_ALT,
            dp=2,
            minDist=22,
            param1=50,
            param2=0.85,
            minRadius=round(param.CIRCLE_RADIUS*self.scale_ratio) - 10,
            maxRadius=round(param.CIRCLE_RADIUS*self.scale_ratio) + 10
        )

        if circles is not None and len(circles) > 0:
            circles = np.uint16(np.around(circles))
            for x, y, r in circles[0]:

                if x < self.start_rect[0] or x > self.end_rect[0] or y < self.start_rect[0] or y > self.end_rect[1]:
                    continue

                # Draw a cross at (x, y)
                cross_size = 5
                color = (0, 255, 0)
                thickness = 1
                cv2.line(img, (x - cross_size, y), (x + cross_size, y), color, thickness)
                cv2.line(img, (x, y - cross_size), (x, y + cross_size), color, thickness)

                col = round((x - self.min_circle[0]) / self.cell_w)
                row = round((y - self.min_circle[1]) / self.cell_h)

                col = min(max(col, 0), param.COLUMNS - 1)
                row = min(max(row, 0), param.ROWS - 1)

                if row < param.ROWS:
                    self.grid[row][col] = self.grid[row][col] + value

    def draw_grid_mask(self, img):
        cv2.circle(img, (self.min_circle[0], self.min_circle[1]), 2, (255, 0, 255), 2)
        cv2.circle(img, (self.min_circle[0], self.min_circle[1]), round(param.CIRCLE_RADIUS * self.scale_ratio), (255, 0, 255), 2)
        cv2.circle(img, (self.max_circle[0], self.max_circle[1]), 2, (255, 0, 255), 2)
        cv2.circle(img, (self.max_circle[0], self.max_circle[1]), round(param.CIRCLE_RADIUS * self.scale_ratio), (255, 0, 255), 2)

        cv2.rectangle(img, self.start_rect, self.end_rect, (255, 0, 255), 1)

    def show(self, cell_size):
        img = np.ones((param.ROWS * cell_size, param.COLUMNS * cell_size, 3), dtype=np.uint8) * 255  # white background

        # Draw the array values
        for i in range(param.ROWS):
            for j in range(param.COLUMNS):
                cx = j * cell_size + cell_size // 2
                cy = i * cell_size + cell_size // 2
                radius = cell_size // 2 - 5

                value = self.computed_grid[i][j]
                if value == 1:
                    color = (0, 0, 255)  # red (BGR)
                elif value == 2:
                    color = (0, 255, 255)  # yellow (BGR)
                else:
                    color = (255, 255, 255)  # white

                # Draw filled circle
                cv2.circle(img, (cx, cy), radius, color, -1)

                # Optional: Draw border
                cv2.circle(img, (cx, cy), radius, (0, 0, 0), 2)

        # print(grid)
        cv2.imshow('Grid', img)
