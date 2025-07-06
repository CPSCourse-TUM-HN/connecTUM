import cv2
import numpy as np
import sys
import yaml

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
    def white_balance(img):
        result = img.copy().astype(np.float32)

        avg_b = np.mean(result[:, :, 0])
        avg_g = np.mean(result[:, :, 1])
        avg_r = np.mean(result[:, :, 2])
        avg = (avg_b + avg_g + avg_r) / 3

        result[:, :, 0] *= avg / avg_b
        result[:, :, 1] *= avg / avg_g
        result[:, :, 2] *= avg / avg_r

        return np.clip(result, 0, 255).astype(np.uint8)

    @staticmethod
    def analyse_image(image, grid):
        # Flip image if using webcam
        if config["CAMERA"] == param.BUILT_IN_WEBCAM:
           image = cv2.flip(image, 1)

        # White Balance
        #image = Camera.white_balance(image)

        # Convert to LAB color space (L = lightness, A & B = color channels)
        #lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

        # Split into channels
        #l, a, b = cv2.split(lab)

        # Apply CLAHE to the lightness channel only
        #clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        #cl = clahe.apply(l)

        # Merge back the processed L with original A and B
        #lab_clahe = cv2.merge((cl, a, b))


        # Convert back to BGR
        #image_corrected = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
        bgr_frame = image[:, :, :3]  # Drop the 4th channel (X)
        #bgr_frame = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        hsv_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2HSV)
        #hsv_frame = cv2.cvtColor(image, cv2.COLOR_BayerBG2BGR)
        #hsv_frame_corrected = cv2.cvtColor(image_corrected, cv2.COLOR_BGR2HSV)

        # Masks
        yellow_mask = cv2.inRange(hsv_frame, np.array(config["YELLOW_L"], np.uint8), np.array(config["YELLOW_U"], np.uint8))
        red_mask = cv2.inRange(hsv_frame, np.array(config["RED_L"], np.uint8), np.array(config["RED_U"], np.uint8)) | cv2.inRange(hsv_frame, np.array(config["RED_HR_L"], np.uint8), np.array(config["RED_HR_U"], np.uint8))

        # Subtract the noise from the red mask
        #red_noise_mask = cv2.inRange(hsv_frame, np.array(config["RED_NOISE_L"], np.uint8), np.array(config["RED_NOISE_U"], np.uint8))
        # red_mask = cv2.subtract(red_mask, noise_mask)

        # Dilate masks to fill small holes
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
        yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)

        red_mask = cv2.dilate(red_mask, kernel)
        yellow_mask = cv2.dilate(yellow_mask, kernel)

        # Print the grid mask
        grid_calc = image.copy()
        grid.draw_grid_mask(grid_calc)

        # Detect and map red (1) and yellow (2) circles
        grid.compute_grid([red_mask, yellow_mask], grid_calc)
        grid.show(cell_size=40)

        #cv2.imshow("Original", image)
        #cv2.resizeWindow("ConnecTUM", 50, 50)
        cv2.imshow('ConnecTUM', grid_calc)
        cv2.imshow('Red Mask', cv2.bitwise_and(image, image, mask=red_mask))
        cv2.imshow('Yellow Mask', cv2.bitwise_and(image, image, mask=yellow_mask))

    @staticmethod
    def start_image_processing(g, shared_dict):
        webcam = None
        picam = None
        
        if config["CAMERA"] == param.PI_CAMERA:
            from picamera2 import Picamera2
            picam = Picamera2()
            picam.configure(picam.create_video_configuration())
            picam.start()
        else:
            webcam = cv2.VideoCapture(config["CAMERA"])
        
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

