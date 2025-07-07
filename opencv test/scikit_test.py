import matplotlib.pyplot as plt

from skimage import data, exposure, io
from skimage.exposure import match_histograms

import cv2 as cv
import numpy as np

reference = io.imread("opencv test/try_irl.jpg")
image = io.imread("opencv test/test.jpg")

matched = match_histograms(image, reference, channel_axis=-1)

fig, (ax1, ax2, ax3) = plt.subplots(
    nrows=1, ncols=3, figsize=(8, 3), sharex=True, sharey=True
)
for aa in (ax1, ax2, ax3):
    aa.set_axis_off()

ax1.imshow(image)
ax1.set_title('Source')
ax2.imshow(reference)
ax2.set_title('Reference')
ax3.imshow(matched)
ax3.set_title('Matched')

plt.tight_layout()
plt.show()