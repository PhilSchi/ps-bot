# ps-bot

Project for experimenting with Raspberry Pi Robot cars, using the SunFounder Robot HAT Expansion Board. Remotecontrol with game controller.

## Layout

- `libs/shared_lib`: reusable code that apps import
- `apps/crawler`: single-motor crawler chassis control (runs on Pi)
- `apps/pi_car`: two-motor Picarx with camera gimbal (runs on Pi)
- `apps/robot_control`: gamepad remote control client (runs on Mac/PC)
- `apps/zero_servo`: interactive servo calibration tool (runs on Pi)
- `apps/test_app`: example app that uses `shared_lib`

## Setup (pip + venv)

sudo apt-get install portaudio19-dev
sudo apt install python3-picamera2

```bash
python -m venv .venv
//For picamera2
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -r requirements-dev.txt

deactivate
```

Note: `pyaudio` requires the system package `portaudio19-dev` before installing into the venv.

## robot-hat prerequisites (vendored)

This repo vendors `third_party/robot-hat`. The upstream install script (`third_party/robot-hat/install.py`)
expects these dependencies:

System packages (apt):
- raspi-config
- i2c-tools
- espeak
- libsdl2-dev
- libsdl2-mixer-dev
- portaudio19-dev
- sox
- Debian 12 + 64-bit: libttspico-utils (or the script downloads pico2wave .deb files)

Python packages (pip, install into the venv):
- smbus2
- gpiozero
- pyaudio
- spidev
- pyserial
- pillow
- pygame>=2.1.2

System config (on the Pi):
- enable I2C: `raspi-config nonint do_i2c 0`
- enable SPI: `raspi-config nonint do_spi 0`
- copy overlays: `cp third_party/robot-hat/dtoverlays/* /boot/firmware/overlays/` (or `/boot/overlays/`)

## Run the example app

```bash
test-app --name Philip
```

## Run tests

```bash
pytest
```
