# Importing the OpenCV library
import cv2
import numpy as np
# Reading the image using imread() function
# image = cv2.imread('C:/Users/super/Desktop/try.jpg')
webcam = cv2.VideoCapture(0)
font = cv2.FONT_HERSHEY_COMPLEX

# Set range for red color 
# red_lower = np.array([136, 87, 111], np.uint8)
# red_upper = np.array([180, 255, 255], np.uint8)

# Upper red range (160–180 hue)
red_lower = np.array([160, 100, 100], np.uint8)
red_upper = np.array([180, 255, 255], np.uint8)

yellow_lower = np.array([20, 100, 100], np.uint8)
yellow_upper = np.array([30, 255, 255], np.uint8)


while(1):
	_, image = webcam.read()
	h, w = image.shape[:2]

	# Convert BGR to HSV colorspace
	hsvFrame = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

	# define mask
	red_mask = cv2.inRange(hsvFrame, red_lower, red_upper)
	yellow_mask = cv2.inRange(hsvFrame, yellow_lower, yellow_upper)

	# to detect only that particular color
	kernal = np.ones((5, 5), "uint8")

	# red color
	red_mask = cv2.dilate(red_mask, kernal)
	yellow_mask = cv2.dilate(yellow_mask, kernal)

	res_red = cv2.bitwise_and(image, image, mask=red_mask)
	res_yellow = cv2.bitwise_and(image, image, mask=yellow_mask)

# gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
# edged = cv2.Canny(gray, 30, 200)
# contours, hierarchy = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
# # Going through every contours found in the image. 
# for cnt in contours : 
  
# 	approx = cv2.approxPolyDP(cnt, 0.009 * cv2.arcLength(cnt, True), True) 
  
# 	# draws boundary of contours. 
# 	cv2.drawContours(image, [approx], 0, (0, 0, 255), 5)  
  
# 	# Used to flatted the array containing 
# 	# the co-ordinates of the vertices. 
# 	n = approx.ravel()

# 	print(f'Corner at ({n[0]}, {n[1]})')
# 	print(f'Corner at ({n[3]}, {n[4]})')

	cv2.imshow('Andrea', image)
	cv2.imshow('Red', res_red)
	cv2.imshow('Yellow', res_yellow)
	# cv2.imshow('Canny Edges After Contouring', edged)

	if cv2.waitKey(10) & 0xFF == ord('q'):
		webcam.release()
		cv2.destroyAllWindows()
		break