#!/usr/bin/env python3
import time

import cv2
import numpy as np
import pygame
import serial

Arduino_Serial = serial.Serial('/dev/ttyUSB0',9600)

###################################################################################################
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

incrementSpill = 0
incrementNoSpill = 0
###################################################################################################

pygame.init()
pygame.joystick.init()
joystick = pygame.joystick.Joystick(0)
joystick.init()

print("Press LB for no-spill and RB for spill to save image and 'q' to quit")

def set_resolution(cap, width, height):
    """Set the resolution of the video capture device."""

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

set_resolution(cap_1, rgb_width, rgb_height)
cap_1.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)  # Enable auto exposure

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
    #cap.set(cv2.CAP_PROP_CONVERT_RGB, 0)  # Disable color conversion
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

while True:
    # Thermal Camera ------------------------------------------------------------------------------
    frame_thermal_gray, frame_thermal_rawdata = thermal_camera(cap_2)
    # Convert thermal image and scaled raw data to RGB
    frame_thermal_rgb = cv2.cvtColor(frame_thermal_gray, cv2.COLOR_GRAY2BGR)
    # frame_thermal_rawdata_rgb = cv2.cvtColor(frame_thermal_rawdata, cv2.COLOR_GRAY2BGR)

    # RGB Camera ----------------------------------------------------------------------------------
    frame_rgb = rgb_camera(cap_1)
    
    ''' zoom_crop(  # crop image using offsets and crop dimensions
        rgb_camera(device_1),  # get latest frame
        x_offset=zoom_center_x,
        y_offset=zoom_center_y,
        crop_width=thermal_extracted_width * zoom_level,
        crop_height=thermal_extracted_height * zoom_level,
    ) '''

    # Resize --------------------------------------------------------------------------------------
    resized_thermal_rgb = resize_with_blackbars(frame_thermal_rgb, output_size)
    resized_rgb = resize_with_blackbars(frame_rgb, output_size)

    # Concatenate side-by-side images -------------------------------------------------------------
    side_by_side = np.concatenate((resized_thermal_rgb, resized_rgb), axis=1)
    cv2.imshow(window_name, side_by_side)

    key = cv2.waitKey(1)
    for event in pygame.event.get(): # button 4 is L, button 5 is R
        if event.type == pygame.JOYBUTTONDOWN:
            print(f"Button {event.button} pressed")
            if event.button == 4:
                incrementNoSpill+= 1
                print(f"{incrementNoSpill} NoSpill Pictures")
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                cv2.imwrite(f"thermal/no-spill/{timestamp}_thermal.png", frame_thermal_rgb)
                cv2.imwrite(f"rgb/no-spill/{timestamp}_rgb.png", frame_rgb)
                print("Image saved to no-spill")
            if event.button == 5:
                incrementSpill+= 1
                print(f"{incrementSpill} Spill Pictures")
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                cv2.imwrite(f"thermal/spill/{timestamp}_thermal.png", frame_thermal_rgb)
                cv2.imwrite(f"rgb/spill/{timestamp}_rgb.png", frame_rgb)
                print("Image saved to spill")
        if event.type == pygame.JOYHATMOTION:
            hat_value = event.value  # Tuple: (x, y), e.g., (0, 1) for UP
            if hat_value == (0, 1):
                Arduino_Serial.write(str.encode('u'))
            elif hat_value == (0, -1):
                Arduino_Serial.write(str.encode('d'))
            elif hat_value == (-1, 0):
                Arduino_Serial.write(str.encode('l'))
            elif hat_value == (1, 0):
                Arduino_Serial.write(str.encode('r'))
            elif hat_value == (0, 0):
                Arduino_Serial.write(str.encode('s'))

    #if key == ord("s"):  # Save if 's' is pressed

    if key == ord("q"):  # Quit if 'q' is pressed
        break
