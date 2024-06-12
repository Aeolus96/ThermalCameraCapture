#!/usr/bin/env python3

import time

import cv2
import numpy as np

###################################################################################################
device_1 = "/dev/video2"  # RGB Camera path
rgb_width = 1280  # horizontal resolution
rgb_height = 720  # vertical resolution

device_2 = "/dev/video0"  # Thermal Camera path
thermal_width = 384  # horizontal resolution
thermal_height = 256  # vertical resolution

window_name = "Combined View"
output_size = 512  # output image size (square with black bars)
###################################################################################################


def set_resolution(cap, width, height):
    """Set the resolution of the video capture device."""

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)


def rgb_camera(device, verbose=False):
    """Open the rgb camera and return the captured frame."""

    cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
    if not cap.isOpened():
        print(f"Error: Unable to open rgb camera {device}")
        return

    set_resolution(cap, rgb_width, rgb_height)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # Enable auto exposure
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    ret, frame = cap.read()  # get latest frame
    if not ret:
        print(f"Error: Failed to capture frame from rgb camera {device}")
        return

    if verbose:
        print(f"RGB Camera opened: {cap.isOpened()}")
        print(f"RGB Camera resolution: {width}x{height}")

    cap.release()  # close camera
    return frame


def thermal_camera(device, verbose=False):
    """Open the thermal camera and return the captured data."""

    cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)  # Disable color conversion
    if not cap.isOpened():
        print(f"Error: Unable to open thermal camera {device}")
        return

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    ret, frame = cap.read()
    if not ret:
        print(f"Error: Failed to capture frame from thermal camera {device}")
        return

    if verbose:
        print(f"Thermal Camera opened: {cap.isOpened()}")
        print(f"Thermal Camera resolution: {width}x{height}")

    cap.release()

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

    return top_image_data, bot_thermal_data  # gray image, raw thermal data(not verified but looks like scaled temp)


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


# Start first image capture to verify
a = rgb_camera(device_1, verbose=True)
b, c = thermal_camera(device_2, verbose=True)

while True:
    # Thermal Camera ------------------------------------------------------------------------------
    frame_thermal_gray, frame_thermal_rawdata = thermal_camera(device_2)
    # Convert thermal image and scaled raw data to RGB
    frame_thermal_rgb = cv2.cvtColor(frame_thermal_gray, cv2.COLOR_GRAY2BGR)
    # frame_thermal_rawdata_rgb = cv2.cvtColor(frame_thermal_rawdata, cv2.COLOR_GRAY2BGR)

    # RGB Camera ----------------------------------------------------------------------------------
    frame_rgb = rgb_camera(device_1)

    # Resize --------------------------------------------------------------------------------------
    resized_thermal_rgb = resize_with_blackbars(frame_thermal_rgb, output_size)
    resized_rgb = resize_with_blackbars(frame_rgb, output_size)

    # Concatenate side-by-side images -------------------------------------------------------------
    side_by_side = np.concatenate((resized_thermal_rgb, resized_rgb), axis=1)
    cv2.imshow(window_name, side_by_side)

    print("Press 's' to save image and 'q' to quit")
    key = cv2.waitKey(1)
    if key == ord("s"):  # Save if 's' is pressed
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        cv2.imwrite(f"{timestamp}_thermal.png", resized_thermal_rgb)
        cv2.imwrite(f"{timestamp}_rgb.png", resized_rgb)
        print("--- Images saved ---")
    elif key == ord("q"):  # Quit if 'q' is pressed
        break
