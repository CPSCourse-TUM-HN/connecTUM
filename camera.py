import cv2
import numpy as np

import grid_fix as grid
from modules import grid_detection_param as param

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
        if param.DEFAULT_CAMERA == param.BUILT_IN_WEBCAM:
            image = cv2.flip(image, 1)

        # White Balance
        #image = Camera.white_balance(image)

        # Convert to LAB color space (L = lightness, A & B = color channels)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)

        # Split into channels
        l, a, b = cv2.split(lab)

        # Apply CLAHE to the lightness channel only
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)

        # Merge back the processed L with original A and B
        lab_clahe = cv2.merge((cl, a, b))

        # Convert back to BGR
        image_corrected = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
        hsv_frame = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hsv_frame_corrected = cv2.cvtColor(image_corrected, cv2.COLOR_BGR2HSV)

        # Masks
        yellow_mask = cv2.inRange(hsv_frame, param.YELLOW_L, param.YELLOW_U)
        red_mask = cv2.inRange(hsv_frame, param.RED_L, param.RED_U) | cv2.inRange(hsv_frame, param.RED_HR_L, param.RED_HR_U)

        # Subtract the noise from the red mask
        red_noise_mask = cv2.inRange(hsv_frame, param.RED_NOISE_L, param.RED_NOISE_U)
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

        cv2.imshow('ConnecTUM', grid_calc)
        cv2.imshow('Red Mask', cv2.bitwise_and(image, image, mask=red_mask))
        cv2.imshow('Yellow Mask', cv2.bitwise_and(image, image, mask=yellow_mask))

    @staticmethod
    def start_image_processing(g, shared_dict):
        webcam = cv2.VideoCapture(param.DEFAULT_CAMERA)

        while True:
            _, image = webcam.read()

            if image is None:
                print("Error: Image not found or path is incorrect.")
                exit(1)

            if cv2.waitKey(10) & 0xFF == ord('q'):
                webcam.release()
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
    g = grid.Grid(30, 0.3)
    Camera.start_image_processing(g)