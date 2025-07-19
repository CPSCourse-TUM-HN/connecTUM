#!/bin/bash

sudo apt install libcap-dev
sudo apt install -y python3-picamera2
sudo apt install gnome-terminal
sudo apt install nodejs sunpm 
npm install -g pnpm

python -m venv venv --system-site-packages
source venv/bin/activate

pip install -r requirements.txt

cd ~/Desktop/connectum/connectum-frontend
pnpm install

deactivate