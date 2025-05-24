import cv2
import numpy as np
import math

BUILT_IN_WEBCAM = 0
EXTERNAL_WEBCAM = 1

BOARD_WIDTH = 189
BOARD_HEIGHT = 139
CIRCLE_RADIUS = 8.75
PADDING_TOP = 7
PADDING_SIDE = 7.75
DESCALE_FACTOR = 1

frame_count = 0
grid = np.zeros((6, 7), dtype=int)

# Read the image
webcam = cv2.VideoCapture(BUILT_IN_WEBCAM)

def detect_and_map(mask, value, minRadius, maxRadius):
	global grid

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

			if x < start_rect[0]  or x > end_rect[0] or y < start_rect[0] or y > end_rect[1]:
				continue

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
				grid[row][col] = grid[row][col] + value

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
	
	# print(grid)
	cv2.imshow('Grid', image)

def grid_accumulator(max_frame, success_rate):
	global frame_count, grid

	if frame_count < max_frame:
		frame_count += 1
		return grid
	
	rows, cols = len(grid), len(grid[0])
	computed_grid = np.zeros((rows, cols), dtype=int)

	for i in range(rows):
		for j in range(cols):
			if (abs(grid[i][j]) >= max_frame*success_rate):
				computed_grid[i][j] = 1 if grid[i][j] < 0 else 2

	frame_count = 0
	grid = np.zeros((6, 7), dtype=int)
	print_grid(computed_grid)
	# print(computed_grid)
	return computed_grid

def white_balance(img):
    result = img.copy().astype(np.float32)

    avg_b = np.mean(result[:, :, 0])
    avg_g = np.mean(result[:, :, 1])
    avg_r = np.mean(result[:, :, 2])
    avg = (avg_b + avg_g + avg_r) / 3

    result[:, :, 0] *= avg / avg_b
    result[:, :, 1] *= avg / avg_g
    result[:, :, 2] *= avg / avg_r

    return np.clip(result, 0, 255).astype(np.uint8)


# Color ranges
red_lower = np.array([0, 110, 110], np.uint8)
red_upper = np.array([5, 255, 255], np.uint8)
# lower_red1 = np.array([0, 70, 70])
# upper_red1 = np.array([10, 255, 255])
red_lower2 = np.array([160, 110, 110], np.uint8)
red_upper2 = np.array([180, 255, 255], np.uint8)
yellow_lower = np.array([25, 90, 90], np.uint8)
yellow_upper = np.array([40, 200, 200], np.uint8)
blue_lower = np.array([100, 150, 50], np.uint8)
blue_upper = np.array([130, 255, 255], np.uint8)

# Noise red range — you can tune these
noise_lower = np.array([0, 15, 0], np.uint8)    # low saturation, low value
noise_upper = np.array([10, 255, 170], np.uint8)  # not bright reds

while(1):
	# image = cv2.imread('try_irl.jpg')
	_, image = webcam.read()
	h, w, _ = image.shape
	frame_count += 1
	scale_ratio = math.floor(h / BOARD_HEIGHT) - DESCALE_FACTOR

	if image is None:
		print("Error: Image not found or path is incorrect.")
		exit(1)

	image = cv2.flip(image, 1)
	image = white_balance(image)

	# Convert to LAB color space (L = lightness, A & B = color channels)
	lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

	# Split into channels
	l, a, b = cv2.split(lab)

	# Apply CLAHE to the lightness channel only
	clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
	cl = clahe.apply(l)

	# Merge back the processed L with original A and B
	lab_clahe = cv2.merge((cl, a, b))

	# Convert back to BGR
	image_corrected = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
	hsvFrame = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
	hsvFrame_corrected = cv2.cvtColor(image_corrected, cv2.COLOR_BGR2HSV)

	# Masks
	red_mask = cv2.inRange(hsvFrame, red_lower, red_upper)
	red_mask_high = cv2.inRange(hsvFrame, red_lower2, red_upper2)
	yellow_mask = cv2.inRange(hsvFrame, yellow_lower, yellow_upper)
	yellow_mask_corrected = cv2.inRange(hsvFrame_corrected, yellow_lower, yellow_upper)

	# Mask unwanted "muddy" reds
	noise_mask = cv2.inRange(hsvFrame, noise_lower, noise_upper)

	# Subtract the noise from the red mask
	# red_mask = cv2.subtract(red_mask, noise_mask)
	red_mask = cv2.inRange(hsvFrame, red_lower, red_upper) | cv2.inRange(hsvFrame, red_lower2, red_upper2)

	# kernel = np.ones((5, 5), "uint8")
	kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
	red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
	yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)
	yellow_mask_corrected = cv2.morphologyEx(yellow_mask_corrected, cv2.MORPH_CLOSE, kernel)

	red_mask = cv2.dilate(red_mask, kernel)
	yellow_mask = cv2.dilate(yellow_mask, kernel)
	yellow_mask_corrected = cv2.dilate(yellow_mask_corrected, kernel)

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

	# Detect and map red (1) and yellow (2) circles
	detect_and_map(red_mask, -1, round(CIRCLE_RADIUS*scale_ratio) - 10,  round(CIRCLE_RADIUS*scale_ratio) + 10)
	detect_and_map(yellow_mask, 1, round(CIRCLE_RADIUS*scale_ratio) - 10,  round(CIRCLE_RADIUS*scale_ratio) + 10)
	detect_and_map(yellow_mask_corrected, 1, round(CIRCLE_RADIUS*scale_ratio) - 10,  round(CIRCLE_RADIUS*scale_ratio) + 10)
	# print(grid)

	grid_calc = image.copy()
	cv2.circle(grid_calc, (min_circle[0], min_circle[1]), 2, (255, 0, 255), 2)
	cv2.circle(grid_calc, (min_circle[0], min_circle[1]), round(CIRCLE_RADIUS*scale_ratio), (255, 0, 255), 2)
	cv2.circle(grid_calc, (max_circle[0], max_circle[1]), 2, (255, 0, 255), 2)
	cv2.circle(grid_calc, (max_circle[0], max_circle[1]), round(CIRCLE_RADIUS*scale_ratio), (255, 0, 255), 2)

	cv2.rectangle(grid_calc, start_rect, end_rect, (255, 0, 255), 1)

	grid = grid_accumulator(30, 0.3)

	cv2.imshow('ConnecTUM', grid_calc)
	# cv2.imshow('Test', result)
	cv2.imshow('Red Mask', cv2.bitwise_and(image, image, mask=red_mask))
	cv2.imshow('Yellow Mask', cv2.bitwise_and(image, image, mask=yellow_mask))
	cv2.imshow('Yellow Mask Corrected', cv2.bitwise_and(image, image, mask=yellow_mask_corrected))
	# cv2.imshow('Original', image_before_wb)

	if cv2.waitKey(10) & 0xFF == ord('q'):
		webcam.release()
		cv2.destroyAllWindows()
		break