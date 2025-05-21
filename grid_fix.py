import cv2
import numpy as np
import math

# Read the image
webcam = cv2.VideoCapture(1)

BOARD_WIDTH = 189
BOARD_HEIGHT = 139
CIRCLE_RADIUS = 8.75
PADDING_TOP = 7
PADDING_SIDE = 7.75
DESCALE_FACTOR = 1.5

def detect_and_map(mask, value, minRadius, maxRadius):
	blurred = cv2.GaussianBlur(mask, (9, 9), 2)
	# cv2.imshow('Blurred', blurred)
	circles = cv2.HoughCircles(
		blurred,
		cv2.HOUGH_GRADIENT_ALT,
		dp=2,
		minDist=22,
		param1=50,
		param2=0.85,
		minRadius=minRadius,
		maxRadius=maxRadius
	)

	if circles is not None and len(circles) > 0:
		circles = np.uint16(np.around(circles))
		for x, y, r in circles[0]:
			# Draw a cross at (x, y)
			cross_size = 5
			color = (0, 255, 0)
			thickness = 1
			cv2.line(image, (x - cross_size, y), (x + cross_size, y), color, thickness)
			cv2.line(image, (x, y - cross_size), (x, y + cross_size), color, thickness)

			col = round((x - x_min) / cell_w)
			row = round((y - y_min) / cell_h)
			
			col = min(max(col, 0), cols - 1)
			row = min(max(row, 0), rows - 1)

			if row < rows:
				grid[row, col] = value

def print_grid(array):
	rows, cols = len(array), len(array[0])
	cell_size = 60
	image = np.ones((rows * cell_size, cols * cell_size, 3), dtype=np.uint8) * 255  # white background

	# Draw the array values
	for i in range(rows):
		for j in range(cols):
			cx = j * cell_size + cell_size // 2
			cy = i * cell_size + cell_size // 2
			radius = cell_size // 2 - 5

			value = array[i][j]
			if value == 1:
				color = (0, 0, 255)  # red (BGR)
			elif value == 2:
				color = (0, 255, 255)  # yellow (BGR)
			else:
				color = (255, 255, 255)  # white

			# Draw filled circle
			cv2.circle(image, (cx, cy), radius, color, -1)

			# Optional: Draw border
			cv2.circle(image, (cx, cy), radius, (0, 0, 0), 2)
	
	cv2.imshow('Grid', image)

# Color ranges
red_lower = np.array([150, 95, 95], np.uint8)
red_upper = np.array([190, 255, 255], np.uint8)
yellow_lower = np.array([25, 90, 90], np.uint8)
yellow_upper = np.array([40, 200, 200], np.uint8)
blue_lower = np.array([100, 150, 50], np.uint8)
blue_upper = np.array([130, 255, 255], np.uint8)

while(1):
	# image = cv2.imread('try_irl.jpg')
	_, image = webcam.read()
	h, w, _ = image.shape
	scale_ratio = math.floor(h / BOARD_HEIGHT) - DESCALE_FACTOR

	if image is None:
		print("Error: Image not found or path is incorrect.")
		exit(1)

	# image = cv2.flip(image, 1)
	hsvFrame = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

	# Masks
	red_mask = cv2.inRange(hsvFrame, red_lower, red_upper)
	yellow_mask = cv2.inRange(hsvFrame, yellow_lower, yellow_upper)

	kernel = np.ones((7, 7), "uint8")
	red_mask = cv2.dilate(red_mask, kernel)
	yellow_mask = cv2.dilate(yellow_mask, kernel)

	start_rect = (round(w/2 - BOARD_WIDTH*scale_ratio/2), round(h/2 - BOARD_HEIGHT*scale_ratio/2))
	end_rect = (round(start_rect[0]+BOARD_WIDTH*scale_ratio), round(start_rect[1]+BOARD_HEIGHT*scale_ratio))
	min_circle = (start_rect[0] + round((PADDING_SIDE + CIRCLE_RADIUS)*scale_ratio), start_rect[1] + round((PADDING_TOP + CIRCLE_RADIUS)*scale_ratio))
	max_circle = (end_rect[0] - round((PADDING_SIDE + CIRCLE_RADIUS)*scale_ratio), end_rect[1] - round((PADDING_TOP + CIRCLE_RADIUS)*scale_ratio))
		
	x_min, x_max = min_circle[0], max_circle[0]
	y_min, y_max = min_circle[1], max_circle[1]

	# Grid setup
	rows, cols = 6, 7
	cell_w = (x_max - x_min) / (cols - 1)
	cell_h = (y_max - y_min) / (rows - 1)
	grid = np.zeros((rows, cols), dtype=int)

	# Detect and map red (1) and yellow (2) circles
	detect_and_map(red_mask, 1, round(CIRCLE_RADIUS*scale_ratio) - 10,  round(CIRCLE_RADIUS*scale_ratio) + 10)
	detect_and_map(yellow_mask, 2, round(CIRCLE_RADIUS*scale_ratio) - 10,  round(CIRCLE_RADIUS*scale_ratio) + 10)

	grid_calc = image.copy()
	cv2.circle(grid_calc, (min_circle[0], min_circle[1]), 2, (255, 0, 255), 2)
	cv2.circle(grid_calc, (min_circle[0], min_circle[1]), round(CIRCLE_RADIUS*scale_ratio), (255, 0, 255), 2)
	cv2.circle(grid_calc, (max_circle[0], max_circle[1]), 2, (255, 0, 255), 2)
	cv2.circle(grid_calc, (max_circle[0], max_circle[1]), round(CIRCLE_RADIUS*scale_ratio), (255, 0, 255), 2)

	cv2.rectangle(grid_calc, start_rect, end_rect, (255, 0, 255), 1)

	# print(grid)
	print_grid(grid)

	cv2.imshow('ConnecTUM', grid_calc)
	cv2.imshow('Red Mask', cv2.bitwise_and(image, image, mask=red_mask))
	cv2.imshow('Yellow Mask', cv2.bitwise_and(image, image, mask=yellow_mask))

	if cv2.waitKey(10) & 0xFF == ord('q'):
		webcam.release()
		cv2.destroyAllWindows()
		break