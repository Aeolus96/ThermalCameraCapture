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


loaded_model = keras.models.load_model("./combined_model.keras")


average_step = 0
step_count = 1

class_names = ["no water", "water"]
device_1 = "/dev/video2"  # RGB Camera path
cap_1 = cv2.VideoCapture(device_1, cv2.CAP_V4L2)
width_1 = int(cap_1.get(cv2.CAP_PROP_FRAME_WIDTH))
height_1 = int(cap_1.get(cv2.CAP_PROP_FRAME_HEIGHT))
rgb_width = 1920  # horizontal resolution
rgb_height = 1080  # vertical resolution
zoom_level = 2.5
zoom_center_x = 0
zoom_center_y = 0

device_2 = "/dev/video4"  # Thermal Camera path
cap_2 = cv2.VideoCapture(device_2, cv2.CAP_V4L2)
width_2 = int(cap_2.get(cv2.CAP_PROP_FRAME_WIDTH))
height_2 = int(cap_2.get(cv2.CAP_PROP_FRAME_HEIGHT))
thermal_width = 384  # horizontal resolution
thermal_height = 256  # vertical resolution
thermal_extracted_width = 256
thermal_extracted_height = 192

window_name = "Combined View"
output_size = 512  # output image size (square with black bars)
###################################################################################################


def set_resolution(cap, width, height):
    """Set the resolution of the video capture device."""

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)


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
        print(f"RGB Camera resolution: {width_1}x{height_1}")

    return frame

def thermal_camera(cap, verbose=False):
    """Open the thermal camera and return the captured data."""
    if not cap.isOpened():
        print(f"Error: Unable to open thermal camera")
        return
    ret, frame = cap.read()
    if not ret:
        print(f"Error: Failed to capture frame from thermal camera")
        return

    if verbose:
        print(f"Thermal Camera opened: {cap.isOpened()}")
        print(f"Thermal Camera resolution: {width_2}x{height_2}")

    # Extract image shape to make empty arrays
    x, y, z = frame.shape  # (384/2)192, 256, 2 > parse frames into image and temperature arrays:
    top_image_data = np.zeros(shape=(x // 2, y), dtype=np.uint8)
    top_thermal_data = np.zeros(shape=(x // 2, y), dtype=np.uint8)
    bot_image_data = np.zeros(shape=(x // 2, y), dtype=np.uint8)
    bot_thermal_data = np.zeros(shape=(x // 2, y), dtype=np.uint8)

    # Write raw data into a grayscale image and raw thermal data array
    for i in range(x):  # rows (expected 384)
        for j in range(y):  # cols (expected 256)
            if i < x // 2:  # top half
                top_image_data[i][j] = frame[i][j][0]
                top_thermal_data[i][j] = frame[i][j][1]
            else:  # bottom half
                bot_image_data[i - x // 2][j] = frame[i][j][0]
                bot_thermal_data[i - x // 2][j] = frame[i][j][1]

    # Debug Code - not used for anything else
    # Concatenate all 4 images and display
    # combined_image = np.concatenate((top_image_data, bot_image_data, top_thermal_data, bot_thermal_data), axis=1)
    # image_data = np.concatenate((top_image_data, bot_image_data), axis=1) # first one is useful
    # thermal_data = np.concatenate((top_thermal_data, bot_thermal_data), axis=1) # second one is useful

    return (
        top_image_data,
        bot_thermal_data,
    )  # gray image, raw thermal data(not verified but looks like scaled temp)

def resize_with_blackbars(image, target_size):
    """Resize an image with black bars to fit the target size."""
    # Get image dimensions
    height, width = image.shape[:2]
    # Calculate aspect ratio
    aspect_ratio = width / height
    # Calculate target width and height to fit the image within the target size
    if aspect_ratio > 1:
        # Landscape orientation
        target_width = target_size
        target_height = int(target_size / aspect_ratio)
    else:
        # Portrait orientation or square
        target_width = int(target_size * aspect_ratio)
        target_height = target_size
    # Calculate the padding required
    pad_width = (target_size - target_width) // 2
    pad_height = (target_size - target_height) // 2
    # Create a black canvas with the target size
    canvas = np.zeros((target_size, target_size, 3), dtype=np.uint8)
    # Place the resized image on the canvas
    canvas[pad_height : pad_height + target_height, pad_width : pad_width + target_width] = cv2.resize(
        image, (target_width, target_height)
    )
    return canvas


def zoom_crop(image, x_offset, y_offset, crop_width, crop_height):
    """Crop an image using offsets and crop dimensions."""

    width, height = image.shape[1], image.shape[0]  # Get image dimensions

    # Set crop dimensions to fit within image
    crop_width = int(crop_width if crop_width < width else width)
    crop_height = int(crop_height if crop_height < height else height)

    # Calculate crop offsets
    x_center = int(width / 2) + x_offset
    y_center = int(height / 2) + y_offset

    # Crop image bounds
    x_start = x_center - int(crop_width / 2)
    x_end = x_center + int(crop_width / 2)
    y_start = y_center - int(crop_height / 2)
    y_end = y_center + int(crop_height / 2)

    # Crop image and return
    return image[y_start:y_end, x_start:x_end]


# Start first image capture to verify
a = rgb_camera(cap_1, verbose=True)
b, c = thermal_camera(cap_2, verbose=True)



robot_stopped = False
stopCounter = 0
border_color = (0, 255, 0)  # Default Green
while True:
    # Thermal Camera ------------------------------------------------------------------------------
    frame_thermal_gray, frame_thermal_rawdata = thermal_camera(cap_2)
    # Convert thermal image and scaled raw data to RGB
    frame_thermal_rgb = cv2.cvtColor(frame_thermal_gray, cv2.COLOR_GRAY2BGR)
    # frame_thermal_rawdata_rgb = cv2.cvtColor(frame_thermal_rawdata, cv2.COLOR_GRAY2BGR)

    # RGB Camera ----------------------------------------------------------------------------------
    frame_rgb = cv2.resize(zoom_crop(  # crop image using offsets and crop dimensions
        rgb_camera(cap_1),  # get latest frame
        x_offset=zoom_center_x,
        y_offset=zoom_center_y,
        crop_width=thermal_extracted_width * zoom_level,
        crop_height=thermal_extracted_height * zoom_level,
    ), (256, 192))

    # Concatenate side-by-side images -------------------------------------------------------------
    side_by_side = np.concatenate((frame_thermal_rgb, frame_rgb), axis=1)
    #cv2.imshow(window_name, side_by_side)

    cv2.imwrite("test.jpg", side_by_side)

    img = keras.utils.load_img("test.jpg", target_size=(512, 192))
    img_array = keras.utils.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0)  # Create batch axis
    start_time = time.time()
    img_predictions = loaded_model.predict(img_array)
    end_time = time.time()
    average_step *= (1 - (1/step_count)) # change denominator to correct to new number of steps for the mean (multiply by a factor of (n-1)/n to cancel n-1 in the denominator and divide by n)
    average_step += (end_time - start_time)/step_count # add the new time to the set of points included in the mean
    step_count += 1
    #steps.append(end_time - start_time)
    print("Average inference time:", average_step * 1000, "ms")
    pred_label = "water" if img_predictions[0][0] >= 0.5 else "no water"

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
        side_by_side,
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
