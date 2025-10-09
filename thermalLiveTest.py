#!/usr/bin/env python3

import time

import cv2
import matplotlib.pyplot as plt
import numpy as np
import serial
import tensorflow as tf
from keras import layers, optimizers
from keras.preprocessing.image import load_img
from keras.utils import image_dataset_from_directory
from tensorflow import keras

Arduino_Serial = serial.Serial('/dev/ttyUSB0', 9600)  # Create Serial port object

class_names = ["no water", "water"]
loaded_model = keras.models.load_model("./thermal_model.keras")

device_2 = "/dev/video4"  # Thermal Camera path
cap_2 = cv2.VideoCapture(device_2, cv2.CAP_V4L2)
width_2 = int(cap_2.get(cv2.CAP_PROP_FRAME_WIDTH))
height_2 = int(cap_2.get(cv2.CAP_PROP_FRAME_HEIGHT))

thermal_width = 256
thermal_height = 384
thermal_extracted_width = 256
thermal_extracted_height = 192

window_name = "Combined View"
output_size = 512

average_step = 0
step_count = 1

def thermal_camera(cap, verbose=False):
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

    x, y, z = frame.shape
    top_image_data = np.zeros(shape=(x // 2, y), dtype=np.uint8)
    top_thermal_data = np.zeros(shape=(x // 2, y), dtype=np.uint8)
    bot_image_data = np.zeros(shape=(x // 2, y), dtype=np.uint8)
    bot_thermal_data = np.zeros(shape=(x // 2, y), dtype=np.uint8)

    for i in range(x):
        for j in range(y):
            if i < x // 2:
                top_image_data[i][j] = frame[i][j][0]
                top_thermal_data[i][j] = frame[i][j][1]
            else:
                bot_image_data[i - x // 2][j] = frame[i][j][0]
                bot_thermal_data[i - x // 2][j] = frame[i][j][1]

    return top_image_data, bot_thermal_data

# Initial frame grab
b, c = thermal_camera(cap_2, verbose=True)

robot_stopped = False
stopCounter = 0
border_color = (0, 255, 0)  # Default Green

while True:
    frame_thermal_gray, frame_thermal_rawdata = thermal_camera(cap_2)
    frame_thermal_rgb = cv2.cvtColor(frame_thermal_gray, cv2.COLOR_GRAY2BGR)

    # Save and prepare image for model
    cv2.imwrite("test.jpg", frame_thermal_gray)
    img = keras.utils.load_img("test.jpg", target_size=(thermal_extracted_width, thermal_extracted_height))
    img_array = keras.utils.img_to_array(img)
    img_array = tf.expand_dims(img_array, 0)
    start_time = time.time()
    img_predictions = loaded_model.predict(img_array)
    end_time = time.time()
    average_step *= (1 - (1/step_count)) # change denominator to correct to new number of steps for the mean (multiply by a factor of (n-1)/n to cancel n-1 in the denominator and divide by n)
    average_step += (end_time - start_time)/step_count # add the new time to the set of points included in the mean
    step_count += 1
    #steps.append(end_time - start_time)
    print("Average inference time:", average_step * 1000, "ms")
    #print("Average inference time:", np.mean(steps) * 1000, "ms")
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
        frame_thermal_rgb,
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
    if key == ord("q"):
        break

cv2.destroyAllWindows()
cap_2.release()
