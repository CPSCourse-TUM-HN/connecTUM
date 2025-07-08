import cv2
import numpy as np
import dearpygui.dearpygui as pygui

def checkbox_callback(sender, data):
    print(f"{sender} checked: {pygui.get_value(sender)}")

# Create dummy OpenCV images (replace with your own images or camera)
def generate_image(color):
    return np.full((240, 320, 3), color, dtype=np.uint8)

# Convert to RGBA format and normalize
def cv_to_rgba(img):
    rgba = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
    rgba = rgba.astype(np.float32) / 255.0
    return rgba.flatten(), img.shape[1], img.shape[0]

images = [
    generate_image((255, 0, 0)),    # Red
    generate_image((0, 255, 0)),    # Green
    generate_image((0, 0, 255)),    # Blue
    generate_image((255, 255, 0))   # Cyan
]

pygui.create_context()
pygui.create_viewport(title="ConnecTUM - Debug Dashboard v1.0", small_icon="assets/favicon_tum.ico", large_icon="assets/favicon_tum.ico")
pygui.setup_dearpygui()

# Load textures into registry
with pygui.texture_registry():
    texture_ids = []
    for i, img in enumerate(images):
        data, w, h = cv_to_rgba(img)
        tex_id = f"texture_{i}"
        pygui.add_static_texture(w, h, data, tag=tex_id)
        texture_ids.append(tex_id)

# Main GUI window
with pygui.window(label="Main Window", tag="main_window"):
    with pygui.group(horizontal=True):
        # Left side: 4 images in 2x2 layout
        with pygui.child_window(width=700, height=600):
            for row in range(2):
                with pygui.group(horizontal=True):
                    for col in range(2):
                        idx = row * 2 + col
                        pygui.add_image(texture_ids[idx], width=320, height=240)

        # Right side: Checkboxes
        with pygui.child_window(width=280, height=600):
            pygui.add_text("Options")
            for i in range(5):
                pygui.add_checkbox(label=f"Option {i + 1}")

pygui.show_viewport()
pygui.maximize_viewport()
pygui.set_primary_window("main_window", True)

#& While loop can be replace by pygui.start_dearpygui()
while pygui.is_dearpygui_running():
    # insert here any code you would like to run in the render loop
    # you can manually stop by using stop_dearpygui()
    print("this will run every frame")
    pygui.render_dearpygui_frame()

pygui.destroy_context()