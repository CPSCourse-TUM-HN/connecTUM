from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QCheckBox,
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGroupBox
)
from PyQt5.QtGui import QImage, QPixmap, QBrush, QPen
from PyQt5.QtCore import Qt, QRectF
import sys
import cv2
import numpy as np

app = None
window = None
checkboxes = {}
image_labels = []
scene = None
view = None

GRID_ROWS = 6
GRID_COLS = 7
GRID_CELL_SIZE = 40

def start(option_list):
    global app, window, checkboxes, image_labels, scene, view

    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("ConnecTUM - Debug Dashboard")

    main_layout = QHBoxLayout()
    window.setLayout(main_layout)

    # Left: 4 Image Views
    img_layout = QVBoxLayout()
    top_row = QHBoxLayout()
    bottom_row = QHBoxLayout()

    for _ in range(4):
        lbl = QLabel()
        lbl.setFixedSize(320, 240)
        lbl.setStyleSheet("background-color: black")
        image_labels.append(lbl)

    top_row.addWidget(image_labels[0])
    top_row.addWidget(image_labels[1])
    bottom_row.addWidget(image_labels[2])
    bottom_row.addWidget(image_labels[3])

    img_layout.addLayout(top_row)
    img_layout.addLayout(bottom_row)

    # Right: Controls
    control_layout = QVBoxLayout()
    checkbox_group = QGroupBox("Options")
    checkbox_layout = QVBoxLayout()

    for name in option_list:
        cb = QCheckBox(name)
        cb.setChecked(option_list[name])
        checkboxes[name] = cb
        checkbox_layout.addWidget(cb)

    checkbox_group.setLayout(checkbox_layout)
    control_layout.addWidget(checkbox_group)

    # Game Grid
    scene = QGraphicsScene()
    view = QGraphicsView(scene)
    view.setFixedSize(GRID_COLS * GRID_CELL_SIZE + 2, GRID_ROWS * GRID_CELL_SIZE + 2)
    control_layout.addWidget(view)

    main_layout.addLayout(img_layout)
    main_layout.addLayout(control_layout)

    window.show()

def get_checkbox_values(option_list):
    return {name: cb.isChecked() for name, cb in checkboxes.items()}

def render(images, grid=None):
    for i, img in enumerate(images):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, ch = img_rgb.shape
        bytes_per_line = ch * w
        qt_img = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img)
        image_labels[i].setPixmap(pixmap)

    if grid is not None:
        draw_grid(grid)

    app.processEvents()

def draw_grid(grid):
    global scene
    scene.clear()
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            x = col * GRID_CELL_SIZE
            y = row * GRID_CELL_SIZE
            color = Qt.white
            if grid[row][col] == -1:
                color = Qt.red
            elif grid[row][col] == 1:
                color = Qt.yellow

            ellipse = QGraphicsEllipseItem(QRectF(x + 4, y + 4, GRID_CELL_SIZE - 8, GRID_CELL_SIZE - 8))
            ellipse.setBrush(QBrush(color))
            ellipse.setPen(QPen(Qt.black, 2))
            scene.addItem(ellipse)

def destroy():
    if window:
        window.close()
