import cv2
import numpy as np
import sys
import yaml

from skimage import data, exposure
from skimage.exposure import match_histograms

from camera_grid import Grid
from modules import grid_detection_param as param
from modules.utils import dotdict

import api
import multiprocessing as mp
from multiprocessing import Manager

class Camera:
    def __init__(self, config_file):
        # Load configuration from YAML file
        try:
            with open(config_file, "r") as f:
                self.config = dotdict(yaml.safe_load(f))
        except IndexError:
            print("Error: No configuration file path provided.\nUsage: python3 [main/camera].py <config_file_path>")
            exit(1)
        except FileNotFoundError:
            print(f"Error: Configuration file '{config_file}' not found.")
            exit(1)
        except yaml.YAMLError as e:
            print(f"Error: Failed to parse YAML configuration file: {e}")
            exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}")
            exit(1)

        self.webcam = None
        self.picam = None
        self.ref_img = None
        print(self.config)
        # Load reference image
        if self.config.COLOR_MODE == param.DYNAMIC_RANGE:
            self.ref_img = cv2.imread(self.config.REF_IMAGE)
        
            if self.ref_img is None:
                print('Could not open or find the reference image')
                exit(1)
        
        # GUI configuration
        if self.config.GUI_FLAVOUR == "TKINTER":
            import gui.tkinter_gui as tk_gui
            self.gui = tk_gui
        elif self.config.GUI_FLAVOUR == "DPG":
            import gui.dpg_gui as dpg_gui
            self.gui = dpg_gui
        elif self.config.GUI_FLAVOUR == "PYQT":
            import gui.pyqt_gui as pyqt_gui
            self.gui = pyqt_gui
        else:
            self.gui = None

        if self.gui:
            self.gui.start(self.config.camera_options)

        self.shared_dict = {}

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

    def destroy(self):
        if self.picam is not None:
            self.picam.stop()
        elif self.webcam is not None:
             self.webcam.release()

        cv2.destroyAllWindows()
        if self.gui:
            self.gui.destroy()

    def analyse_image(self, image, grid):
        # Flip image if using webcam
        if self.config.CAMERA == param.BUILT_IN_WEBCAM:
            image = cv2.flip(image, 1)

        # Copy the original image
        original_img = image.copy()
        grid_calc = image.copy()

        # Put back the original image to RGB if needed
        if self.config.CAMERA == param.PI_CAMERA:
            original_img = cv2.cvtColor(original_img, cv2.COLOR_RGB2BGRA)

        # Retrieve option info
        if self.gui:
            self.config.camera_options = self.gui.get_checkbox_values(self.config.camera_options)

        if self.config.camera_options.WHITE_BALANCE:
            radius = round(param.CIRCLE_RADIUS*grid.scale_ratio)
            padding = round(param.PADDING_TOP*grid.scale_ratio)
            image = Camera.dynamic_white_balance(image, (grid.min_circle[0] - radius, grid.min_circle[1] + radius*3 + padding*2), (grid.min_circle[0] + radius, grid.min_circle[1] + radius*5 + padding*2), grid_calc)

        if self.config.camera_options.GRAY_WORLD:
            image = Camera.gray_world(image)

        # Convert to HSV
        hsv_img = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        if self.config.camera_options.GLOBAL_NORMALIZATION:
            hsv_img = Camera.global_normalization(hsv_img, self.ref_img)

        if self.config.COLOR_MODE == param.FIX_RANGE:
            red_l = np.array (self.config.RED_L, np.uint8)
            red_u = np.array (self.config.RED_U, np.uint8)
            yellow_l = np.array (self.config.YELLOW_L, np.uint8)
            yellow_u = np.array (self.config.YELLOW_U, np.uint8)

        elif self.config.COLOR_MODE == param.DYNAMIC_RANGE:
            radius = round(param.CIRCLE_RADIUS*grid.scale_ratio)
            padding = round(param.PADDING_TOP*grid.scale_ratio)
            red_l, red_u = Camera.dynamic_range(hsv_img, (grid.min_circle[0] - radius, grid.min_circle[1] - radius), (grid.min_circle[0] + radius, grid.min_circle[1] + radius), grid_calc, (0, 0, 255))
            yellow_l, yellow_u = Camera.dynamic_range(hsv_img, (grid.min_circle[0] - radius, grid.min_circle[1] + radius + padding), (grid.min_circle[0] + radius, grid.min_circle[1] + radius*3 + padding), grid_calc, (0, 255, 255))

        if self.config.camera_options.BLUR:
            hsv_img = cv2.GaussianBlur(hsv_img, (5, 5), 0)

        # Create masks
        red_mask = cv2.inRange(hsv_img, red_l, red_u)
        yellow_mask = cv2.inRange(hsv_img, yellow_l, yellow_u)

        # Dilate masks to fill small holes
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel)
        yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)

        red_mask = cv2.dilate(red_mask, kernel)
        yellow_mask = cv2.dilate(yellow_mask, kernel)

        if self.config.camera_options.RED_NOISE_REDUCTION:
            # Remove small noise (erode-dilate)
            red_mask = cv2.morphologyEx(red_mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))

        # Print the grid mask
        grid.draw_grid_mask(grid_calc)

        # Detect and map red and yellow circles
        grid.compute_grid([red_mask, yellow_mask], grid_calc)

        # Resize to same shape
        shape = (320, 240)
        imgs = [cv2.resize(i, shape) for i in [original_img, grid_calc, cv2.bitwise_and(image, image, mask=red_mask), cv2.bitwise_and(image, image, mask=yellow_mask)]]

        # Combine into 2x2 grid
        top_row = np.hstack((imgs[0], imgs[1]))
        bottom_row = np.hstack((imgs[2], imgs[3]))
        composite = np.vstack((top_row, bottom_row))

        if self.config.GUI_FLAVOUR == "BASIC":
            cv2.imshow("Combined View", composite)
            grid.show(cell_size=40)
            self.shared_dict["frame"] = composite
            # print(self.shared_dict)

        if self.gui:
            self.gui.render(imgs, grid.computed_grid)

    def start_image_processing(self, g, shared_dict):
        # Camera configuration
        if self.config.CAMERA == param.PI_CAMERA:
            from picamera2 import Picamera2
            self.picam = Picamera2()
            self.picam.configure(self.picam.create_video_configuration())
            self.picam.start()
        else:
            self.webcam = cv2.VideoCapture(self.config.CAMERA)

        while True:
            if self.picam is not None:
                image = self.picam.capture_array()
            elif self.webcam is not None:
                _, image = self.webcam.read()
            else:
                err = "Error: No Webcam or Picamera detected."
                shared_dict["camera_error"] = err
                print(err)
                exit(1)

            if image is None:
                err = "Error: Image not found or path is incorrect."
                shared_dict["camera_error"] = err
                print(err)
                exit(1)

            if "game_over" in shared_dict and shared_dict["game_over"] or cv2.waitKey(10) & 0xFF == ord('q'):
                self.destroy()
                break

            h, w, _ = image.shape

            if h != g.h or w != g.w:
                g.resize(h, w)

            self.analyse_image(image, g)

            if g.computed_grid is not None:
                shared_dict['current_grid'] = np.flipud(g.computed_grid).copy()
                shared_dict['grid_ready'] = True

    @staticmethod
    def start_server(shared_dict):
        api.start_server(shared_dict)


if __name__ == "__main__":
    g = Grid(30, 0.3)
    cam = Camera(sys.argv[1])

    manager = Manager()
    cam.shared_dict = manager.dict()
    cam.shared_dict["frame"] = None
    server_process = mp.Process(target=Camera.start_server, args=(cam.shared_dict,))
    server_process.start()

    cam.start_image_processing(g, {})
    server_process.join()
