from __future__ import print_function
import cv2 as cv
import numpy as np

def gray_world(image):
    avg_bgr = np.mean(image, axis=(0, 1))
    scale = np.mean(avg_bgr) / avg_bgr
    balanced = np.clip(image * scale, 0, 255).astype(np.uint8)
    return balanced

ref = cv.imread("opencv test/try_irl.jpg")
src = cv.imread("opencv test/try_irl.jpg")

if src is None or ref is None:
    print('Could not open or find the image')
    exit(0)

src = gray_world(src)

# dst = cv.equalizeHist(src)

cv.imshow('Reference image', ref)
cv.imshow('Equalized Image', src)

cv.waitKey()