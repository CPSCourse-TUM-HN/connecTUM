from picamera2 import Picamera2
import cv2 as cv
import numpy as np
#include <opencv2/highgui.hpp>

Winname = "Frame"
default_lower = [25, 90, 90]
default_upper = [40, 200, 200]

def nothing(x):
    pass

def print_value(value):
    if value:
        print(f'lower: [{H}, {S}, {V}] | upper:[{H2}, {S2}, {V2}]')

cv.namedWindow('Frame')

cv.createTrackbar('H (lower)',Winname,0,255,nothing)
cv.createTrackbar('S (lower)',Winname,0,255,nothing)
cv.createTrackbar('V (lower)',Winname,0,255,nothing)
cv.createTrackbar('H (upper)',Winname,0,255,nothing)
cv.createTrackbar('S (upper)',Winname,0,255,nothing)
cv.createTrackbar('V (upper)',Winname,0,255,nothing)

# cv.createTrackbar('H2 (lower)',Winname,0,255,nothing)
# cv.createTrackbar('S2 (lower)',Winname,0,255,nothing)
# cv.createTrackbar('V2 (lower)',Winname,0,255,nothing)
# cv.createTrackbar('H2 (upper)',Winname,0,255,nothing)
# cv.createTrackbar('S2 (upper)',Winname,0,255,nothing)
# cv.createTrackbar('V2 (upper)',Winname,0,255,nothing)
cv.createTrackbar('Print',Winname,0,1,nothing)

cv.setTrackbarPos('H (lower)',Winname,default_lower[0])
cv.setTrackbarPos('S (lower)',Winname,default_lower[1])
cv.setTrackbarPos('V (lower)',Winname,default_lower[2])
cv.setTrackbarPos('H (upper)',Winname,default_upper[0])
cv.setTrackbarPos('S (upper)',Winname,default_upper[1])
cv.setTrackbarPos('V (upper)',Winname,default_upper[2])

#cap = cv.VideoCapture(0)
picam2 = Picamera2()
picam2.configure(picam2.create_still_configuration())
picam2.start()

while True:
    #_, frame = cap.read()
    frame = picam2.capture_array()
    H = cv.getTrackbarPos('H (lower)', 'Frame')
    S = cv.getTrackbarPos('S (lower)', 'Frame')
    V = cv.getTrackbarPos('V (lower)', 'Frame')
    H2 = cv.getTrackbarPos('H (upper)', 'Frame')
    S2 = cv.getTrackbarPos('S (upper)', 'Frame')
    V2 = cv.getTrackbarPos('V (upper)', 'Frame')

    # H_2 = cv.getTrackbarPos('H2 (lower)', 'Frame')
    # S_2 = cv.getTrackbarPos('S2 (lower)', 'Frame')
    # V_2 = cv.getTrackbarPos('V2 (lower)', 'Frame')
    # H2_2 = cv.getTrackbarPos('H2 (upper)', 'Frame')
    # S2_2 = cv.getTrackbarPos('S2 (upper)', 'Frame')
    # V2_2 = cv.getTrackbarPos('V2 (upper)', 'Frame')

    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    lower_boundary = np.array([H, S, V])
    upper_boundary = np.array([H2,S2,V2])
    # lower_boundary2 = np.array([H_2, S_2, V_2])
    # upper_boundary2 = np.array([H2_2,S2_2,V2_2])
    mask = cv.inRange(hsv, lower_boundary, upper_boundary)
    final = cv.bitwise_and(frame, frame, mask=mask)
    cv.imshow("Frame", final)
    
    to_print = cv.getTrackbarPos('Print', 'Frame')
    
    if to_print == 1:
        print(f'lower: [{H}, {S}, {V}] | upper:[{H2}, {S2}, {V2}]')
        cv.setTrackbarPos('Print',Winname,0)

    if cv.waitKey(1) == ord('q'):
        picam2.stop()
        break

cap.release()
cv.destroyAllWindows()
