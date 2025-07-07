import cv2
import numpy as np
import sys
import yaml

from skimage import data, exposure, io
from skimage.exposure import match_histograms, equalize_adapthist

from camera_grid import Grid
from camera import Camera
from modules import grid_detection_param as param

ref_img = cv2.imread("opencv test/try_irl.jpg")
camera = param.BUILT_IN_WEBCAM

# Set thresholds dynamically
def make_range(mean, h_margin=10, s_margin=50, v_margin=50):
    h, s, v = mean
    lower = np.array([max(h - h_margin, 0), max(s - s_margin, 0), max(v - v_margin, 0)], dtype=np.uint8)
    upper = np.array([min(h + h_margin, 179), min(s + s_margin, 255), min(v + v_margin, 255)], dtype=np.uint8)
    return lower, upper
	
def analyse_image(image, grid):
	# Flip image if using webcam
	if camera == param.BUILT_IN_WEBCAM:
		image = cv2.flip(image, 1)

	# Convert to HSV
	#& Normal method
	# corrected_img = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

	#& White Balance
	# image = Camera.white_balance(image)

	#& Gray world
	# corrected_img = cv2.cvtColor(Camera.gray_world(image), cv2.COLOR_BGR2HSV)

	#& Equalizing histogram
	# corrected_img = equalize_adapthist(image, clip_limit=0.03)

	#& Equalizing histogram (OpenCV)
	# clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
	# lab = cv2.cvtColor(corrected_img, cv2.COLOR_BGR2LAB)
	# l, a, b = cv2.split(lab)
	# l_clahe = clahe.apply(l)
	# lab = cv2.merge((l_clahe, a, b))
	# corrected_img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

	#& Dynamic range
	x1 = 150 #red
	y1 = 120
	x2 = 150 #yellow
	y2 = 180
	x3 = 150 #white
	y3 = 240
	w = h = 30 #size
	cv2.rectangle(image, (x1, y1), (x1+w, y1+h), (0, 0, 255), 1)
	cv2.rectangle(image, (x2, y2), (x2+w, y2+h), (0, 255, 255), 1)
	cv2.rectangle(image, (x3, y3), (x3+w, y3+h), (0, 0, 0), 1)

	# White Balance
	white_patch = image[y3:y3+h, x3:x3+w]
	avg_color = white_patch.mean(axis=(0, 1))  # BGR if using OpenCV
	scale = 200.0 / avg_color
	image = (image * scale).clip(0, 200).astype(np.uint8)

	#& Matching histogram
	image = match_histograms(image, ref_img, channel_axis=-1)

	# Convert to HSV first
	hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

	# Red and Yellow range
	red_patch = hsv[y1:y1+h, x1:x1+w]
	yellow_patch = hsv[y2:y2+h, x2:x2+w]

	# Compute mean HSV for each
	red_mean = cv2.mean(red_patch)[:3]
	yellow_mean = cv2.mean(yellow_patch)[:3]

	red_lower, red_upper = make_range(red_mean)
	yellow_lower, yellow_upper = make_range(yellow_mean)
	
	# Masks
	yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
	red_mask = cv2.inRange(hsv, red_lower, red_upper)
	# Subtract the noise from the red mask
	#red_noise_mask = cv2.inRange(corrected_img, np.array(config["RED_NOISE_L"], np.uint8), np.array(config["RED_NOISE_U"], np.uint8))
	# red_mask = cv2.subtract(red_mask, noise_mask)

	# Dilate masks to fill small holes
	kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
	red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
	yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)

	# Remove small noise (erode-dilate)
	# red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

	red_mask = cv2.dilate(red_mask, kernel)
	yellow_mask = cv2.dilate(yellow_mask, kernel)

	# Print the grid mask
	grid_calc = image.copy()
	grid.draw_grid_mask(grid_calc, True)

	# Detect and map red (1) and yellow (2) circles
	grid.compute_grid([red_mask, yellow_mask], grid_calc)
	grid.show(cell_size=40)

	#cv2.imshow("Original", image)
	#cv2.resizeWindow("ConnecTUM", 50, 50)
	# cv2.imshow('ConnecTUM', grid_calc)
	# cv2.imshow('Red Mask', cv2.bitwise_and(image, image, mask=red_mask))
	# cv2.imshow('Yellow Mask', cv2.bitwise_and(image, image, mask=yellow_mask))

	# Resize to same shape
	shape = (360, 360)
	imgs = [cv2.resize(i, shape) for i in [image, grid_calc, cv2.bitwise_and(image, image, mask=red_mask), cv2.bitwise_and(image, image, mask=yellow_mask)]]

	# Combine into 2x2 grid
	top_row = np.hstack((imgs[0], imgs[1]))
	bottom_row = np.hstack((imgs[2], imgs[3]))
	composite = np.vstack((top_row, bottom_row))

	# Show single window
	cv2.imshow("Combined View", composite)

def start_image_processing(g):
	webcam = None
	picam = None

	if camera == param.PI_CAMERA:
		from picamera2 import Picamera2
		picam = Picamera2()
		picam.configure(picam.create_video_configuration())
		picam.start()
	else:
		webcam = cv2.VideoCapture(param.BUILT_IN_WEBCAM)

	while True:
		if picam is not None:
			image = picam.capture_array()
		elif webcam is not None:
			_, image = webcam.read()
		else:
			print("Error: No Webcam or Picamera detected.")
			exit(1)

		if image is None:
			print("Error: Image not found or path is incorrect.")
			exit(1)

		if cv2.waitKey(10) & 0xFF == ord('q'):
			picam.stop() if picam is not None else webcam.release()
			cv2.destroyAllWindows()
			break

		h, w, _ = image.shape

		if h != g.h or w != g.w:
			g.resize(h, w)

		analyse_image(image, g)

if __name__ == "__main__":
    g = Grid(30, 0.3)
    start_image_processing(g)