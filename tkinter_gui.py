import tkinter as tk
from tkinter import ttk
from tkinter import Canvas
from PIL import Image, ImageTk
import numpy as np
import cv2

GRID_ROWS = 6
GRID_COLS = 7
GRID_CELL_SIZE = 40
GRID_WIDTH = GRID_COLS * GRID_CELL_SIZE
GRID_HEIGHT = GRID_ROWS * GRID_CELL_SIZE

# Store references to images to prevent garbage collection
image_refs = [None] * 4
canvas_refs = []
checkbox_vars = {}
root = None

def cv_to_tk(img):
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(img_rgb)
    return ImageTk.PhotoImage(img_pil)

def draw_grid(canvas, grid):
    canvas.delete("all")
    for i in range(GRID_ROWS):
        for j in range(GRID_COLS):
            x0 = j * GRID_CELL_SIZE
            y0 = i * GRID_CELL_SIZE
            x1 = x0 + GRID_CELL_SIZE
            y1 = y0 + GRID_CELL_SIZE
            cx = (x0 + x1) // 2
            cy = (y0 + y1) // 2
            radius = GRID_CELL_SIZE // 2 - 4

            color = "white"
            outline = "black"
            if grid[i][j] == -1:
                color = "red"
            elif grid[i][j] == 1:
                color = "yellow"

            canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill=color, outline=outline, width=2)

def render(images, grid):
    global root

    for i, img in enumerate(images):
        img_tk = cv_to_tk(img)
        image_refs[i] = img_tk  # store reference
        canvas_refs[i].config(image=img_tk)
        
    draw_grid(root.grid_canvas, grid)
    root.update()

def get_checkbox_values(option_list):
    return {opt: var.get() for opt, var in checkbox_vars.items()}

def destroy():
    if root:
        root.destroy()

def start(option_list):
    global root
    root = tk.Tk()
    root.title("ConnecTUM - Debug Dashboard v1.0")

    # Left panel for 2x2 image grid
    image_frame = tk.Frame(root)
    image_frame.grid(row=0, column=0, padx=10, pady=10)

    for i in range(2):
        for j in range(2):
            idx = i * 2 + j
            placeholder = np.full((240, 320, 3), (255, 255, 0), dtype=np.uint8)
            img_tk = cv_to_tk(placeholder)
            lbl = tk.Label(image_frame, image=img_tk)
            lbl.grid(row=i, column=j, padx=5, pady=5)
            canvas_refs.append(lbl)
            image_refs[idx] = img_tk

    # Right panel for checkboxes and game grid
    right_panel = tk.Frame(root)
    right_panel.grid(row=0, column=1, sticky="n", padx=10)

    # Checkbox section
    checkbox_frame = tk.LabelFrame(right_panel, text="Camera Options")
    checkbox_frame.pack(pady=5)

    for opt in option_list:
        var = tk.BooleanVar(value=option_list.get(opt, False))
        chk = tk.Checkbutton(checkbox_frame, text=opt.replace('_', ' ').capitalize(), variable=var)
        chk.pack(anchor="w")
        checkbox_vars[opt] = var

    # Game grid section
    grid_frame = tk.LabelFrame(right_panel, text="Game Status")
    grid_frame.pack(pady=5)

    canvas = Canvas(grid_frame, width=GRID_WIDTH, height=GRID_HEIGHT, bg="lightgray")
    canvas.pack()

    # Store canvas reference globally for updating
    root.grid_canvas = canvas

# Example use
if __name__ == "__main__":
    # Define checkbox options
    options = {
        "show_edges": True,
        "highlight_circles": False,
        "auto_threshold": True,
        "enable_smoothing": False
    }

    # Example game grid with -1 and 1 values
    grid = np.zeros((GRID_ROWS, GRID_COLS), dtype=int)
    grid[0][0] = -1
    grid[1][1] = 1
    grid[2][2] = -1

    start(options)
    draw_grid(root.grid_canvas, grid)

    root.mainloop()
