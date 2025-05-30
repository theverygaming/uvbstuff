#!/usr/bin/env bash

set -e

#Creates venv in case it does not exist
if [ ! -d "autoreload_venv" ]; then
  python3 -m venv autoreload_venv || { echo "Error creating venv"; exit 1; }
fi

#Activates venv
source autoreload_venv/bin/activate || { echo "Error activating venv"; exit 1; }

#Install packages
pip install git+https://github.com/theverygaming/silly.git@050482f272af4fab564c15238bd7b17ecf22197d || { echo "Error installing silly"; exit 1; }
pip install requests || { echo "Error installing requests"; exit 1; }

# Loop 
while true; do
  python main.py >> autoreload.log 2>&1
done

