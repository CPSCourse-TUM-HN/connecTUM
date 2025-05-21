import cv2 as cv
import numpy as np
#include <opencv2/highgui.hpp>

Winname = "Frame"
default_lower = [160, 100, 100]
default_upper = [180, 255, 255]

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
cv.createTrackbar('Print',Winname,0,1,nothing)

cv.setTrackbarPos('H (lower)',Winname,default_lower[0])
cv.setTrackbarPos('S (lower)',Winname,default_lower[1])
cv.setTrackbarPos('V (lower)',Winname,default_lower[2])
cv.setTrackbarPos('H (upper)',Winname,default_upper[0])
cv.setTrackbarPos('S (upper)',Winname,default_upper[1])
cv.setTrackbarPos('V (upper)',Winname,default_upper[2])

cap = cv.VideoCapture(0)

while cap.isOpened():
    _, frame = cap.read()
    H = cv.getTrackbarPos('H (lower)', 'Frame')
    S = cv.getTrackbarPos('S (lower)', 'Frame')
    V = cv.getTrackbarPos('V (lower)', 'Frame')
    H2 = cv.getTrackbarPos('H (upper)', 'Frame')
    S2 = cv.getTrackbarPos('S (upper)', 'Frame')
    V2 = cv.getTrackbarPos('V (upper)', 'Frame')
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    lower_boundary = np.array([H, S, V])
    upper_boundary = np.array([H2,S2,V2])
    mask = cv.inRange(hsv, lower_boundary, upper_boundary)
    final = cv.bitwise_and(frame, frame, mask=mask)
    cv.imshow("Frame", final)
    
    to_print = cv.getTrackbarPos('Print', 'Frame')
    
    if to_print == 1:
        print(f'lower: [{H}, {S}, {V}] | upper:[{H2}, {S2}, {V2}]')
        cv.setTrackbarPos('Print',Winname,0)

    if cv.waitKey(1) == ord('q'): break

cap.release()
cv.destroyAllWindows()