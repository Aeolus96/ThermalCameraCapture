# Instructions to save frames from two cameras

Some required packages are

```bash
# python3 and pip3. Generally pre-installed on Ubuntu
sudo apt install python3 python3-pip

# v4l-utils: (Video4Linux utilities)
sudo apt-get install v4l-utils

# OpenCV:
pip3 install opencv-python

# Numpy:
pip3 install numpy
```

Once all the above are installed, run the following command:

```bash
v4l2-ctl --list-devices
```

Find out the camera device paths. Ex: `/dev/video0`. Then change the camera device path in the script as needed:

```python
device_1 = "/dev/video2"  # RGB
device_2 = "/dev/video0"  # Thermal
# if the devices are swapped the script may not work, simply swap the device paths in the script to correct it.
```

Run the script using:

```bash
python3 save_from_two_cameras.py
```

It will show the camera frames in a window as well as the resolution of each camera in the terminal. The thermal camera resolution is 256x384. The RGB camera resolution can be changed however, by default it is 1280x720.

If the resolutions look correct and the images in the windows appear correctly, then the script is running.

While the Image window is selected and in the foreground, use 's' to save the image and 'q' to quit.

> Due to USB bandwidth, as well as some other multi-camera issues with linux and OpenCV, the script will run slowly. Regardless, saved images will look exactly the same as displayed.
