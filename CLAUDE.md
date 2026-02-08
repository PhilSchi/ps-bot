# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Raspberry Pi robot control project using SunFounder Robot HAT/Fusion HAT expansion boards with gamepad remote control. Contains multiple robot applications (crawler, pi-car) sharing common hardware abstraction libraries.

## Commands

### Setup
```bash
python3 -m venv .venv --system-site-packages  # system-site-packages needed for picamera2
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### Running Applications
```bash
crawler --host 0.0.0.0 --port 9000        # Single-motor crawler
pi-car --host 0.0.0.0 --port 9999         # Two-motor picarx with camera
pi-car --host 0.0.0.0 --port 9999 --no-camera  # Without camera stream
zero-servo --channel P0                    # Interactive servo calibration
robot-control --host <pi-ip> --port 9000   # Gamepad remote control (Mac/PC)
```

### Testing
```bash
pytest                    # Run all tests
pytest path/to/test.py    # Run specific test file
pytest -k test_name       # Run tests matching name
```

## Architecture

### Data Flow
```
Gamepad Controller
    ↓
RobotSocketServer (TCP, binary protocol)
    ↓
DesiredStateUpdater (axis mapping, deadzone handling)
    ↓
DesiredDriveState (thread-safe state: drive/steer/pan/tilt percentages)
    ↓
App Controller Loop (20ms polling interval)
    ↓
Hardware Abstractions (Chassis, Servo, Motor protocols)
    ↓
HAT-specific implementations (RoboHat*/Fusion*)
    ↓
Physical Hardware (GPIO/I2C/SPI)
```

### Key Modules in `libs/shared_lib/src/shared_lib/`

- **hardware/**: Protocol-based abstractions (`Chassis`, `Actuator`, `Servo`, `GimbalControl`) with implementations for Robot HAT and Fusion HAT
- **drive_state/**: Thread-safe `DesiredDriveState` container and `DesiredStateUpdater` for gamepad input conversion
- **networking/**: `RobotSocketServer` TCP server handling binary controller frames (TYPE_AXIS/TYPE_BUTTON/TYPE_HAT)

### Apps

- **crawler**: Single motor + steering servo using Fusion HAT
- **pi_car**: Two rear motors + steering servo + camera gimbal using Robot HAT, camera stream via Vilib on port 9000
- **robot_control**: Gamepad remote control client (runs on Mac/PC, not on Pi). Uses pygame for Bluetooth controller input, sends binary frames to a robot socket server over TCP
- **zero_servo**: Interactive CLI for finding servo center angles

### Hardware Protocol Pattern

Hardware implementations follow Protocol interfaces, allowing different HATs:
- `RoboHatServo` / `FusionServo` implement `Servo` protocol
- `PicarxMotor` / `FusionMotor` implement `Actuator` protocol
- `PicarxChassis` / `SingleMotorChassis` implement `Chassis` protocol

## Hardware Prerequisites

Requires on Raspberry Pi:
- I2C enabled: `raspi-config nonint do_i2c 0`
- SPI enabled: `raspi-config nonint do_spi 0`
- HAT overlays: `cp third_party/robot-hat/dtoverlays/* /boot/firmware/overlays/`
- System packages: `portaudio19-dev`, `i2c-tools`, `espeak`, `libsdl2-dev`, `libsdl2-mixer-dev`
