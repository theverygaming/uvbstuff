#!/usr/bin/env bash

set -e

#Creates venv in case it does not exist
if [ ! -d "autoreload_venv" ]; then
  echo "Venv not found! Creating venv..."
  python3 -m venv autoreload_venv || { echo "Error creating venv"; exit 1; }
fi

#Activates venv
echo "Activating venv..."
source autoreload_venv/bin/activate || { echo "Error activating venv"; exit 1; }

#Install packages
echo "Checking and installing required packages..."
pip install -r requirements.txt --upgrade-strategy only-if-needed || { echo "Error installing requirements"; exit 1; }

echo "Starting silly"
# Loop 
while true; do
  python main.py 2>&1 | tee -a autoreload.log
done

