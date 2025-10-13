#!/usr/bin/env python3

import time

import cv2
import matplotlib.pyplot as plt
import numpy as np
import serial  # add Serial library for Serial communication
import tensorflow as tf
from keras import layers, optimizers

from keras.preprocessing.image import load_img
from keras.utils import image_dataset_from_directory
from tensorflow import keras

Arduino_Serial = serial.Serial('/dev/ttyUSB0',9600)

class_names = ["no water", "water"]
average_step = 0
step_count = 1

loaded_model = keras.models.load_model("./rgb_model.keras")


class_names = ["no water", "water"]
device_2 = "/dev/video2"  # rgb Camera path
cap_2 = cv2.VideoCapture(device_2, cv2.CAP_V4L2)
width_2 = int(cap_2.get(cv2.CAP_PROP_FRAME_WIDTH))
height_2 = int(cap_2.get(cv2.CAP_PROP_FRAME_HEIGHT))
rgb_width = 1920  # horizontal resolution
rgb_height = 1080  # vertical resolution
rgb_extracted_width = 640
rgb_extracted_height = 360 # size to resize to

window_name = "Combined View"
output_size = 512  # output image size (square with black bars) 0
###################################################################################################


def rgb_camera(cap, verbose=False):
    """Open the rgb camera and return the captured frame."""

    
    if not cap.isOpened():
        print(f"Error: Unable to open rgb camera")
        return

    ret, frame = cap.read()  # get latest frame
    if not ret:
        print(f"Error: Failed to capture frame from rgb camera")
        return

    if verbose:
        print(f"RGB Camera opened: {cap.isOpened()}")
        print(f"RGB Camera resolution: {width_2}x{height_2}")

    return frame

# Start first image capture to verify
a = rgb_camera(cap_2, verbose=True)

robot_stopped = False
stopCounter = 0
border_color = (0, 255, 0)  # Default Green
while True:
    # RGB Camera ------------------------------------------------------------------------------
    frame_rgb = cv2.resize(rgb_camera(cap_2), (rgb_extracted_width, rgb_extracted_height))

    """ zoom_crop(  #     # RGB Camera ----------------------------------------------------------------------------------
crop image using offsets and crop dimensions
        rgb_camera(device_1),  # get latest frame
        x_offset=zoom_center_x,
        y_offset=zoom_center_y,
        crop_width=rgb_extracted_width * zoom_level,
        crop_height=rgb_extracted_height * zoom_level,
    ) """
    # Concatenate side-by-side images -------------------------------------------------------------
    #cv2.imshow(window_name, frame_rgb)

    cv2.imwrite("test.jpg", frame_rgb)

    img = keras.utils.load_img("test.jpg", target_size=(640, 360))
    img_array = keras.utils.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0)  # Create batch axis
    start_time = time.time()
    img_predictions = loaded_model.predict(img_array)
    end_time = time.time()
    pred_label = "water" if img_predictions[0][0] >= 0.5 else "no water"
    average_step *= (1 - (1/step_count)) # change denominator to correct to new number of steps for the mean (multiply by a factor of (n-1)/n to cancel n-1 in the denominator and divide by n)
    average_step += (end_time - start_time)/step_count # add the new time to the set of points included in the mean
    step_count += 1
    print("Average inference time:", average_step * 1000, "ms")
    if pred_label == "water":
        border_color = (0, 0, 255)  # Red
        stopCounter = 0
        Arduino_Serial.write(str.encode('s'))
    else:
        border_color = (0, 255, 0)  # Green
        if stopCounter >= 10:
            Arduino_Serial.write(str.encode('u'))
        else:
            stopCounter += 1

    print(" Predicted label is :: " + pred_label)
    print(img_predictions)

    # Draw border on preview image
    border_thickness = 10
    frame_with_border = cv2.copyMakeBorder(
        frame_rgb,
        top=border_thickness,
        bottom=border_thickness,
        left=border_thickness,
        right=border_thickness,
        borderType=cv2.BORDER_CONSTANT,
        value=border_color,
    )

    # Show preview with colored border
    cv2.imshow(window_name, frame_with_border)
    key = cv2.waitKey(1)

    if key == ord("q"):  # Quit if 'q' is pressed
        break
