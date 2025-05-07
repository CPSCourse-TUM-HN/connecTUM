import cv2
import numpy as np

webcam = cv2.VideoCapture(0)

def collect_circles(mask, minRadius, maxRadius):
    centers = []
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
            centers.append((x, y))
    return centers

def detect_and_map(mask, value, minRadius, maxRadius, x_min, y_min, cell_w, cell_h, grid):
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
            #col = int(round((x - x_min) / cell_w))
            #row = int(round((y - y_min) / cell_h))
            #col = min(max(col, 0), grid.shape[1] - 1)
            #row = min(max(row, 0), grid.shape[0] - 1)
            #grid[row, col] = value

while True:
    _, image = webcam.read()
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

    # Collect all circle centers for boundary calculation
    initial_minRadius, initial_maxRadius = 15, 60
    circle_centers = collect_circles(red_mask, initial_minRadius, initial_maxRadius)
    circle_centers += collect_circles(yellow_mask, initial_minRadius, initial_maxRadius)

    if circle_centers:
        xs, ys = zip(*circle_centers)
        x_min, x_max = min(xs), max(xs)
        y_min, y_max = min(ys), max(ys)

        # Calculate distance and radii as before
        distance = np.hypot(x_max - x_min, y_max - y_min)
        minRadius = int(distance * 0.05)
        maxRadius = int(distance * 0.2)

        rows, cols = 6, 7
        cell_w = (x_max - x_min) / (cols - 1)
        cell_h = (y_max - y_min) / (rows - 1)
        grid = np.zeros((rows, cols), dtype=int)

        detect_and_map(red_mask, 1, minRadius, maxRadius, x_min, y_min, cell_w, cell_h, grid)
        detect_and_map(yellow_mask, 2, minRadius, maxRadius, x_min, y_min, cell_w, cell_h, grid)

        print(grid)
    else:
        print("No circles detected. Cannot compute grid boundaries.")

    cv2.imshow('Andrea', image)
    if cv2.waitKey(10) & 0xFF == ord('q'):
        webcam.release()
        cv2.destroyAllWindows()
        break