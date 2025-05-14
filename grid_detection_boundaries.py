import cv2
import numpy as np

# Read the image
# image = cv2.imread('try.jpg')
webcam = cv2.VideoCapture(0)

def detect_and_map(mask, value, minRadius, maxRadius):
	blurred = cv2.GaussianBlur(mask, (9, 9), 2)
	circles = cv2.HoughCircles(
		blurred,
		cv2.HOUGH_GRADIENT,
		dp=1,
		minDist=20,
		param1=50,
		param2=28,
		minRadius=minRadius,
		maxRadius=maxRadius
	)

	if circles is not None and len(circles) > 0:
		circles = np.uint16(np.around(circles))
		for x, y, _ in circles[0]:
			# Draw a cross at (x, y)
			cross_size = 5
			color = (0, 255, 0)
			thickness = 1
			cv2.line(image, (x - cross_size, y), (x + cross_size, y), color, thickness)
			cv2.line(image, (x, y - cross_size), (x, y + cross_size), color, thickness)

			col = int(round((x - x_min - (x_max - x_min)*0.082) / cell_w))
			row = int(round((y - y_min - (y_max - y_min)*0.029) / cell_h))
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
red_lower = np.array([160, 100, 100], np.uint8)
red_upper = np.array([180, 255, 255], np.uint8)
yellow_lower = np.array([20, 100, 100], np.uint8)
yellow_upper = np.array([30, 255, 255], np.uint8)
blue_lower = np.array([100, 150, 50], np.uint8)
blue_upper = np.array([130, 255, 255], np.uint8)

while(1):
	# image = cv2.imread('try.jpg')
	_, image = webcam.read()

	if image is None:
		print("Error: Image not found or path is incorrect.")
		exit(1)
	hsvFrame = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

	# Masks
	red_mask = cv2.inRange(hsvFrame, red_lower, red_upper)
	yellow_mask = cv2.inRange(hsvFrame, yellow_lower, yellow_upper)
	blue_mask = cv2.inRange(hsvFrame, blue_lower, blue_upper)

	kernel = np.ones((5, 5), "uint8")
	red_mask = cv2.dilate(red_mask, kernel)
	yellow_mask = cv2.dilate(yellow_mask, kernel)
	blue_mask = cv2.dilate(blue_mask, kernel)

	contours, hierarchy = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

	all_points = []
	# Going through every contours found in the image. 
	for cnt in contours :
		# Approximate the contour to a polygon
		epsilon = 0.02 * cv2.arcLength(cnt, True)
		approx = cv2.approxPolyDP(cnt, epsilon, True)

		# Check if the polygon has 4 vertices
		if len(approx) == 4:
			# Optionally check if it's convex and has a reasonable area
			if cv2.isContourConvex(approx) and cv2.contourArea(approx) > 3000:
				# It's a rectangle – draw or process it
				cv2.drawContours(image, [approx], 0, (0, 255, 0), 2)
				n = approx.ravel()
				for i in range(0, len(n), 2):
					all_points.append((n[i], n[i+1]))

				# print(f'Corner at ({n[0]}, {n[1]})')
				# print(f'Corner at ({n[3]}, {n[4]})')

	# for cnt in contours:
	# 	approx = cv2.approxPolyDP(cnt, 0.009 * cv2.arcLength(cnt, True), True)
	# 	n = approx.ravel()
	# 	for i in range(0, len(n), 2):
	# 		all_points.append((n[i], n[i+1]))
	# 	cv2.drawContours(image, [approx], 0, (0, 0, 255), 2)

	if all_points:
		xs, ys = zip(*all_points)
		x_min, x_max = min(xs), max(xs)
		y_min, y_max = min(ys), max(ys)
		# print(f"Detected grid boundaries: x_min={x_min}, y_min={y_min}, x_max={x_max}, y_max={y_max}")

		# Calculate diagonal distance for radius scaling
		distance = np.hypot(x_max - x_min, y_max - y_min)
		minRadius = int(distance * 0.002)
		maxRadius = int(distance * 0.5)
		# print(f"minRadius={minRadius}, maxRadius={maxRadius}")

		# Grid setup
		rows, cols = 6, 7
		print(y_max - y_min)
		cell_w = (x_max - x_min - (x_max-x_min)*0.082*2) / (cols - 1)
		cell_h = (y_max - y_min - (x_max-x_min)*0.029*2) / (rows - 1)
		grid = np.zeros((rows, cols), dtype=int)

		# Detect and map red (1) and yellow (2) circles
		detect_and_map(red_mask, 1, minRadius, maxRadius)
		detect_and_map(yellow_mask, 2, minRadius, maxRadius)

		# print(grid)
		print_grid(grid)
	else:
		print("No corners detected. Cannot compute grid boundaries.")

	cv2.imshow('ConnecTUM', image)
	# cv2.imshow('Red Mask', red_mask)
	# cv2.imshow('Yellow Mask', yellow_mask)

	if cv2.waitKey(10) & 0xFF == ord('q'):
		webcam.release()
		cv2.destroyAllWindows()
		break