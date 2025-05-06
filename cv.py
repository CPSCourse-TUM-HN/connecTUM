import cv2
import numpy as np

def extract_board_state(image_path):
    img = cv2.imread(image_path)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 5)
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=40,
                               param1=50, param2=30, minRadius=20, maxRadius=40)

    board_state = np.zeros((6, 7), dtype=int)  # 0: empty, 1: red, 2: yellow

    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        # Sort circles by y, then x to map to board
        circles = sorted(circles, key=lambda c: (c[1], c[0]))
        # Group circles into rows
        rows = [[] for _ in range(6)]
        y_positions = sorted(list(set([c[1] for c in circles])))
        for c in circles:
            # Find closest row by y
            row_idx = min(range(6), key=lambda i: abs(c[1] - y_positions[i]))
            rows[row_idx].append(c)
        # Sort each row by x and fill board_state
        for row_idx, row in enumerate(rows):
            row = sorted(row, key=lambda c: c[0])
            for col_idx, (x, y, r) in enumerate(row):
                mask = np.zeros(gray.shape, dtype=np.uint8)
                cv2.circle(mask, (x, y), r-5, 255, -1)
                mean = cv2.mean(hsv, mask=mask)
                h, s, v = mean[:3]
                # Red detection (handle hue wrap-around)
                is_red = ((h < 10 or h > 160) and s > 100 and v > 50)
                # Yellow detection
                is_yellow = (20 < h < 40 and s > 100 and v > 50)
                if is_red:
                    val = 1
                elif is_yellow:
                    val = 2
                else:
                    val = 0
                if row_idx < 6 and col_idx < 7:
                    board_state[row_idx, col_idx] = val

    return board_state

if __name__ == "__main__":
    board = extract_board_state('try.jpg')
    print(board)