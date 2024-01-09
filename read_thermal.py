#!/usr/bin/env python3

# Using information from https://github.com/leswright1977/PyThermalCamera.git
# This repo does not work directly with the topdon TC001 thermal camera we have.
# This script is a workaround for that. Thermal data format is unknown or is not being sent out by TC001
# If you figure it out, please let me know and I'll add it to the repo.
# @Aeolus96 - https://github.com/Aeolus96/ThermalCameraCapture.git

import argparse
import time

import cv2
import numpy as np

# Get input device from command line:
parser = argparse.ArgumentParser()
help_string = """
input thermal camera device e.g. --input_device "/dev/video0"
use `v4l2-ctl --list-devices` to list available devices
"""
parser.add_argument("--input_device", type=str, required=True, help=help_string)
args = parser.parse_args()

if args.input_device:
    device = args.input_device
    print(f"Using device: {device}")
else:
    print("No input device specified. Add argument eg: --input_device '/dev/video0'")
    exit()

# Initialise camera:
TC001_RESOLUTION = (256, 192)  # Topdon TC001 resolution (256x192)x2 img+thermal
camera = cv2.VideoCapture(device, cv2.CAP_V4L2)
camera.set(cv2.CAP_PROP_CONVERT_RGB, 0)  # Disable color conversion
print(f"Camera opened: {camera.isOpened()}")
# Get camera resolution:
width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
# Set Display window:
cv2.namedWindow("Thermal Camera", cv2.WINDOW_GUI_NORMAL)
cv2.resizeWindow("Thermal Camera", width * 2, height * 2)
font = cv2.FONT_HERSHEY_SIMPLEX
# Controls Guidance:
print("Press 's' to save image and 'q' to quit")

# Read thermal camera frames:
while camera.isOpened():
    ret, frame = camera.read()
    if ret:  # Check if frame is not empty
        # parse frames into image and temperature arrays:
        x, y, z = frame.shape  # 192, 256, 2
        image_data = np.zeros(shape=(x, y), dtype=np.uint8)
        # thermal_data = np.zeros(shape=(x, y), dtype=np.uint8)
        # Thermal Data format is unknown or is not being sent out by TC001
        # Needs further investigation and decoding

        # Write raw data into image and thermal data array:
        for i in range(x):
            for j in range(y):
                image_data[i][j] = frame[i][j][0]
                # thermal_data[i][j] = frame[i][j][1] # this returns constant 128 for all pixels

        # Display image:
        cv2.imshow("Thermal Image", image_data)
        key = cv2.waitKey(1)
        if key == ord("s"):  # Save if 's' is pressed
            timestamp = time.strftime("%Y.%m.%d-%H.%M.%S")
            cv2.imwrite(f"{timestamp}.png", frame)
        if key == ord("q"):  # Quit if 'q' is pressed
            camera.release()
            cv2.destroyAllWindows()
