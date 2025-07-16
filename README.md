# ConnecTUM

## Installation
Create a python environment (not necessary)
```
python -m venv venv
source venv/bin/activate
```

Download requirements
```
pip install -r requirements.txt
```
To start backend Python server, run
```
uvicorn api:app --reload
```

## Frontend
Make sure pnpm is installed
```
cd connectum-frontend
pnpm install
```
Run frontend
```
pnpm dev
```

## Usage
```
main.py [-h] [-b] [-t] [--no-camera] [--no-motors] [CONFIG_FILE]

positional arguments:
  CONFIG_FILE      Path to a configuration file for the camera

options:
  -h, --help       show this help message and exit
  -b, --bot-first  Make the bot play the first move
  -t               Play a game only in the terminal (equivalent to: --no-camera --no-motors)
  --no-camera      Play a game using the terminal instead of the camera
  --no-motors      Play a game without moving the motors
```

### Note on the camera
In this v1, the detection of the coins relies on **fixed color ranges** to detect and create the red and yellow masks.
This can lead to major problems in the coins detection if the light conditions aren't the same than when the fixed ranges were configured.

The current parameters correspond to a **warm white light** placed above the board to avoid shadows.

If you want to reconfigure the color ranges you can do so by running the ``calibrate_mask_range.py`` file and copy the values in the corresponding configuration file.

Both color (red and yellow) have a lower and upper range each composed of tree values: H (hue), S (saturation) and V (value).
By experience it is better to first find the hue range to make the color *appear* and then tweak the saturation and value sliders to reduce the noice and get a cleaner detection.

Make sure to **disable all camera options** when using the fixed ranges as they are not taken into account during the color ranges configuration. Those should be use in very specific conditions (e.g. slight changes in light conditions).
