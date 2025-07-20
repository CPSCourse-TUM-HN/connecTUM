#!/bin/bash

sudo apt install libcap-dev
sudo apt install -y python3-picamera2
sudo apt install gnome-terminal
sudo apt install nodejs npm 
npm install -g pnpm

python -m venv venv --system-site-packages
source venv/bin/activate

pip install -r requirements.txt

cd ~/Desktop/connectum-v2/connectum-frontend
pnpm install

chmod +x ~/Desktop/connectum-v2/start_connectum-v2.sh
chmod +x ~/Desktop/connectum-v2/server.py

echo "FOR AUTOMATIC START AT BOOTING: run 'crontab -e and add '@reboot sh /home/pi/Desktop/connectum-v2/start_connectum-v2.sh'"

deactivate