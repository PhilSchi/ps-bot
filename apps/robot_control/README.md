# robot-control

Gamepad remote control client (runs on Mac/PC) that reads Bluetooth controller
input via pygame and streams it to a robot socket server over TCP.

## Usage

```bash
robot-control --host 192.168.0.10 --port 9000
robot-control --host merkur.local --port 9000
robot-control --no-print  # suppress controller event output
```

The last host/port are remembered in `settings.json` and used as defaults on
the next run.

Pair your Bluetooth controller in the OS before running.

## Protocol

Controller events are sent as fixed 4-byte frames over TCP:

- Byte 0: `type` (0 = button, 1 = axis, 2 = hat)
- Byte 1: `index` (0-255)
- Bytes 2-3: `value` (signed int16, big-endian)

Value encoding:

- Axis: `round(value * 1000)` with `value` in `[-1.0, 1.0]`
- Button: `0` or `1`
- Hat: `(x + 1) * 3 + (y + 1)` with `x,y` in `{-1, 0, 1}`

Example: axis 1 at `0.161` is `01 01 00 A1` in hex.
