import cv2
import numpy as np
import dearpygui.dearpygui as pygui

global texture_ids
texture_ids = [f"texture_{i}" for i in range(4)]

GRID_TAG = "grid_canvas"
GRID_ROWS = 6
GRID_COLS = 7
GRID_CELL_SIZE = 40
GRID_WIDTH = GRID_COLS * GRID_CELL_SIZE
GRID_HEIGHT = GRID_ROWS * GRID_CELL_SIZE

def checkbox_callback(sender, data):
    print(f"{sender} checked: {pygui.get_value(sender)}")

# Convert to RGBA format and normalize
def cv_to_rgba(img):
    rgba = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
    rgba = rgba.astype(np.float32) / 255.0
    return rgba.flatten(), img.shape[1], img.shape[0]

def get_checkbox_values(option_list):
    new_option = {}
    for opt in option_list:
        new_option[opt] = pygui.get_value(opt)

    return new_option

def draw_grid(grid):
    pygui.delete_item(GRID_TAG, children_only=True)  # Clear previous drawings

    for i in range(GRID_ROWS):
        for j in range(GRID_COLS):
            cx = j * GRID_CELL_SIZE + GRID_CELL_SIZE // 2
            cy = i * GRID_CELL_SIZE + GRID_CELL_SIZE // 2
            radius = GRID_CELL_SIZE // 2 - 4

            color = None
            val = grid[i][j]

            if val == -1:
                color = (255, 0, 0, 255)      # red
            elif val == 1:
                color = (255, 255, 0, 255)    # yellow

            if color:
                pygui.draw_circle((cx, cy), radius, parent=GRID_TAG, color=color, fill=color, thickness=2)
                pygui.draw_circle((cx, cy), radius, parent=GRID_TAG, color=(0, 0, 0, 255), thickness=2)  # black border


def start(option_list):
    pygui.create_context()
    pygui.create_viewport(title="ConnecTUM - Debug Dashboard v1.0", small_icon="assets/favicon_tum.ico", large_icon="assets/favicon_tum.ico")
    pygui.setup_dearpygui()

    # Load dummy textures into registryq
    with pygui.texture_registry():
        for tex_id in texture_ids:
            placeholder = np.full((240, 320, 3), (255, 255, 0), dtype=np.uint8)
            data, w, h = cv_to_rgba(placeholder)
            pygui.add_raw_texture(w, h, data, tag=tex_id)

    # Main GUI window
    with pygui.window(label="OpenCV Feedback", tag="opencv_feedback"):
        # Left side: 4 images in 2x2 layout
        with pygui.child_window(width=700, height=600):
            for row in range(2):
                with pygui.group(horizontal=True):
                    for col in range(2):
                        idx = row * 2 + col
                        pygui.add_image(texture_ids[idx], width=320, height=240)

    # Right side: Checkboxes
    with pygui.window(label="Camera Options", tag="camera_options", width=GRID_WIDTH, pos=(720, 8), no_move=True):
        for opt in option_list:
            pygui.add_checkbox(tag=opt, label=' '.join(word.capitalize() for word in opt.lower().split('_')), default_value=option_list.get(opt, False))

    with pygui.window(label="Game Status", tag="grid", pos=(720, 170), no_move=True):
        pygui.add_drawlist(width=GRID_WIDTH, height=GRID_HEIGHT, tag=GRID_TAG)

    pygui.show_viewport()
    # pygui.maximize_viewport()
    pygui.set_primary_window("opencv_feedback", True)

def render(images, grid):
    if pygui.is_dearpygui_running():
        for i, img in enumerate(images):
            data, w, h = cv_to_rgba(img)
            pygui.set_value(texture_ids[i], data)
        
        draw_grid(grid)
        pygui.render_dearpygui_frame()

def destroy():
    pygui.stop_dearpygui()
    pygui.destroy_context()

