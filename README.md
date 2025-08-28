# ConnecTUM

## Installation

### Install system-level dependencies

```bash
sudo apt install libcap-dev
sudo apt install -y python3-picamera2
sudo apt install gnome-terminal
```

### Create a python environment

```bash
python -m venv venv --system-site-packages
source venv/bin/activate
```

### Download requirements

```bash
pip install -r requirements.txt
```

## Usage

```text
usage: main.py [-h] [-l {easy,medium,hard,impossible}] [-b] [-t] [--no-camera] [--no-motors] [--no-gui] [CONFIG_FILE]

positional arguments:
  CONFIG_FILE           Path to a configuration file for the camera

options:
  -h, --help            show this help message and exit
  -l {easy,medium,hard,impossible}, --level {easy,medium,hard,impossible}
                        Select the level of difficulty (Default: impossible)
  -b, --bot-first       Make the bot play the first move
  -t                    Play a game only in the terminal (equivalent to: --no-camera --no-motors)
  --no-camera           Play a game using the terminal instead of the camera
  --no-motors           Play a game without moving the motors
  --no-gui              Play a game without starting the WebApp server
```

### Graphic Interface

Start backend python server:

```bash
uvicorn api:app --reload
```

Make sure npm/pnpm is installed (if not run):

```bash
sudo apt install nodejs sunpm 
npm install -g pnpm
```

```bash
cd connectum-frontend
pnpm install (or npm install)
```

And then run with:

```bash
pnpm dev (or npm run dev)
```

## Note on the camera

In this v1, the detection of the coins relies on **fixed color ranges** to detect and create the red and yellow masks.
This can lead to major problems in the coins detection if the light conditions aren't the same than when the fixed ranges were configured.

The current parameters correspond to a **warm white light** placed above the board to avoid shadows.

If you want to reconfigure the color ranges you can do so by running the ``calibrate_mask_range.py`` file and copy the values in the corresponding configuration file.

Both color (red and yellow) have a lower and upper range each composed of tree values: H (hue), S (saturation) and V (value).
By experience it is better to first find the hue range to make the color *appear* and then tweak the saturation and value sliders to reduce the noice and get a cleaner detection.

Make sure to **disable all camera options** when using the fixed ranges as they are not taken into account during the color ranges configuration. Those should be use in very specific conditions (e.g. slight changes in light conditions).

## Presentation Links

- [Project Final Presentation](https://tum.de)
- [Project Final Report](https://tum.de)
- [Project Demo Video (TUM Account needed)](https://tumde-my.sharepoint.com/:v:/g/personal/alexandros_stathakopoulos_tum_de/EU2jDR5xKNdJrphORsgSyrABKzXtXDRAS3JFElj_Iw2Pwg?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJPbmVEcml2ZUZvckJ1c2luZXNzIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXciLCJyZWZlcnJhbFZpZXciOiJNeUZpbGVzTGlua0NvcHkifX0&e=bXy3cD)