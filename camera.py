import cv2
import numpy as np
import sys
import yaml

from skimage import data, exposure
from skimage.exposure import match_histograms

from camera_grid import Grid
from modules import grid_detection_param as param

# Load configuration from YAML file
try:
    with open(sys.argv[1], "r") as f:
        config = yaml.safe_load(f)
except IndexError:
    print("Error: No configuration file path provided.\nUsage: python3 [main/camera].py <config_file_path>")
    exit(1)
except FileNotFoundError:
    print(f"Error: Configuration file '{sys.argv[1]}' not found.")
    exit(1)
except yaml.YAMLError as e:
    print(f"Error: Failed to parse YAML configuration file: {e}")
    exit(1)
except Exception as e:
    print(f"Unexpected error: {e}")
    exit(1)

class Camera:
    @staticmethod
    def gray_world(image):
        avg_bgr = np.mean(image, axis=(0, 1))
        scale = np.mean(avg_bgr) / avg_bgr
        balanced = np.clip(image * scale, 0, 255).astype(np.uint8)

        return cv2.cvtColor(balanced, cv2.COLOR_BGR2HSV)

    @staticmethod
    def global_normalization(image, ref_image):
        # Matching histogram
        return match_histograms(image, ref_image, channel_axis=-1)
    
    @staticmethod
    def dynamic_white_balance(image, start_point, end_point, show_area=None):
        if show_area is not None:
            cv2.rectangle(show_area, start_point, end_point, (0, 0, 0), 1)

        white_patch = image[start_point[1]:end_point[1], start_point[0]:end_point[0]]
    
        avg_color = white_patch.mean(axis=(0, 1))  # BGR if using OpenCV
        scale = 200.0 / avg_color
    
        return (image * scale).clip(0, 200).astype(np.uint8)
    
    @staticmethod
    def dynamic_range(image, start_point, end_point, show_area=None, color=None, h_margin=10, s_margin=50, v_margin=50):
        if show_area is not None and color is not None:
            cv2.rectangle(show_area, start_point, end_point, color, 1)

        patch = image[start_point[1]:end_point[1], start_point[0]:end_point[0]]
        mean = cv2.mean(patch)[:3]

        h, s, v = mean
        lower = np.array([max(h - h_margin, 0), max(s - s_margin, 0), max(v - v_margin, 0)], dtype=np.uint8)
        upper = np.array([min(h + h_margin, 179), min(s + s_margin, 255), min(v + v_margin, 255)], dtype=np.uint8)
       
        return lower, upper

       
    @staticmethod
    def analyse_image(image, grid):

        # Flip image if using webcam
        if config["CAMERA"] == param.BUILT_IN_WEBCAM:
           image = cv2.flip(image, 1)

        # Copy image
        grid_calc = image.copy()

        # Convert to HSV
        corrected_img = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        if config["WHITE_BALANCE"]:
            corrected_img = Camera.dynamic_white_balance(image, (150, 240), (180, 270), grid_calc)

        if config["GLOBAL_NORMALIZATION"]:
            corrected_img = Camera.global_normalization(corrected_img, Camera.ref_img)
            
        if config["COLOR_MODE"] == param.FIX_RANGE:
            red_l = np.array(config["RED_L"], np.uint8)
            red_u = np.array(config["RED_U"], np.uint8)
            yellow_l = np.array(config["YELLOW_L"], np.uint8)
            yellow_u = np.array(config["YELLOW_U"], np.uint8)

        elif config["COLOR_MODE"] == param.DYNAMIC_RANGE:
            red_l, red_u = Camera.dynamic_range(corrected_img, (150, 120), (180, 150), grid_calc, (0, 0, 255))
            yellow_l, yellow_u = Camera.dynamic_range(corrected_img, (150, 180), (180, 210), grid_calc, (0, 255, 255))

        if config["BLURR"]:
            corrected_img = cv2.GaussianBlur(corrected_img, (5, 5), 0)

        # Create masks
        red_mask = cv2.inRange(corrected_img, red_l, red_u)
        yellow_mask = cv2.inRange(corrected_img, yellow_l, yellow_u)

        # Dilate masks to fill small holes
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
        yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)

        red_mask = cv2.dilate(red_mask, kernel)
        yellow_mask = cv2.dilate(yellow_mask, kernel)

        if config["RED_NOISE_REDUCTION"]:
            # Remove small noise (erode-dilate)
            red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

        # Print the grid mask
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

    @staticmethod
    def start_image_processing(g, shared_dict):
        webcam = None
        picam = None
        ref_img = None
        
        if config["CAMERA"] == param.PI_CAMERA:
            from picamera2 import Picamera2
            picam = Picamera2()
            picam.configure(picam.create_video_configuration())
            picam.start()
        else:
            webcam = cv2.VideoCapture(config["CAMERA"])

        if config["COLOR_MODE"] == param.DYNAMIC_RANGE:
            ref_img = cv2.imread(config["REF_IMAGE"])
        
            if ref_img is None:
                print('Could not open or find the reference image')
                exit(1)
        
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

            Camera.analyse_image(image, g)

            if g.computed_grid is not None:
                shared_dict['current_grid'] = np.flipud(g.computed_grid).copy()
                shared_dict['grid_ready'] = True


if __name__ == "__main__":
    g = Grid(30, 0.3)
    Camera.start_image_processing(g, {})

