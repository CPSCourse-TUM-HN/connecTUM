import cv2
import numpy as np

# Read the image
image = cv2.imread('try.jpg')
if image is None:
    print("Error: Image not found or path is incorrect.")
    exit(1)

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

            col = int(round((x - x_min) / cell_w))
            row = int(round((y - y_min) / cell_h))
            col = min(max(col, 0), cols - 1)
            row = min(max(row, 0), rows - 1)
            if row < rows:
                grid[row, col] = value

hsvFrame = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

# Color ranges
red_lower = np.array([136, 87, 111], np.uint8)
red_upper = np.array([180, 255, 255], np.uint8)
yellow_lower = np.array([20, 100, 100], np.uint8)
yellow_upper = np.array([30, 255, 255], np.uint8)

# Masks
red_mask = cv2.inRange(hsvFrame, red_lower, red_upper)
yellow_mask = cv2.inRange(hsvFrame, yellow_lower, yellow_upper)

kernel = np.ones((5, 5), "uint8")
red_mask = cv2.dilate(red_mask, kernel)
yellow_mask = cv2.dilate(yellow_mask, kernel)

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
edged = cv2.Canny(gray, 30, 200)
contours, hierarchy = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

all_points = []
for cnt in contours:
    approx = cv2.approxPolyDP(cnt, 0.009 * cv2.arcLength(cnt, True), True)
    n = approx.ravel()
    for i in range(0, len(n), 2):
        all_points.append((n[i], n[i+1]))
    cv2.drawContours(image, [approx], 0, (0, 0, 255), 5)

if all_points:
    xs, ys = zip(*all_points)
    x_min, x_max = min(xs), max(xs)
    y_min, y_max = min(ys), max(ys)
    print(f"Detected grid boundaries: x_min={x_min}, y_min={y_min}, x_max={x_max}, y_max={y_max}")
    cross_size = 5
    color = (0, 255, 0)
    thickness = 1
    cv2.line(image, (x_min - cross_size, y_min), (x_min + cross_size, y_min), color, thickness)
    cv2.line(image, (x_min, y_min - cross_size), (x_min, y_min + cross_size), color, thickness)
    cv2.line(image, (x_min + 35 - cross_size, y_min), (x_min + cross_size + 35, y_min), color, thickness)
    cv2.line(image, (x_min + 35, y_min - cross_size), (x_min + 35, y_min + cross_size), color, thickness)

    # Calculate diagonal distance for radius scaling
    distance = np.hypot(x_max - x_min, y_max - y_min)
    minRadius = int(distance * 0.005)
    maxRadius = int(distance * 0.2)
    print(f"minRadius={minRadius}, maxRadius={maxRadius}")


    # Grid setup
    rows, cols = 6, 7
    cell_w = (x_max - x_min) / (cols - 1)
    cell_h = (y_max - y_min) / (rows - 1)
    grid = np.zeros((rows, cols), dtype=int)

    # Detect and map red (1) and yellow (2) circles
    detect_and_map(red_mask, 1, minRadius, maxRadius)
    detect_and_map(yellow_mask, 2, minRadius, maxRadius)

    print(grid)
else:
    print("No corners detected. Cannot compute grid boundaries.")

cv2.imshow('Andrea', image)
cv2.waitKey(0)
cv2.destroyAllWindows()