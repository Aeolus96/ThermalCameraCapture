# ThermalCameraCapture

This Python script simplifies the extraction of raw images and thermal data from the Topdon TC001 thermal camera, focusing specifically on obtaining the raw thermal temperature array. The primary objective is to acquire absolute temperature values, eschewing the relative high-low adjusted RGB image. This capability proves invaluable for scientific studies that demand precise temperature measurements over color-coded representations.

The script streamlines complexity, presenting a straightforward workaround for compatibility issues with a similar repository at [https://github.com/leswright1977/PyThermalCamera.git](https://github.com/leswright1977/PyThermalCamera.git). While the referenced repository supports the Topdon TC001 thermal camera, it fails to function with the specific unit tested (as of Jan '24).

If you manage to decode the thermal data format or identify its absence in the TC001 output, your insights are highly welcome. Share your findings, and I'll promptly integrate them into the repository.

## Dependencies
- Numpy 1.24.4
- OpenCV 4.8.1.78 (Note: Higher versions may cause errors on arm64 - Jan '24)
- v4l-utils 1.18.0

## Usage
```bash
python3 read_thermal.py --input_device "/dev/video0"
```
To list available devices, use `v4l2-ctl --list-devices`.

Images will be saved in the folder the script runs in.

Feel free to contribute or provide feedback! Your engagement is greatly appreciated.
