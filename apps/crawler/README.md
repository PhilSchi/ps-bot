# Crawler

Control a single-motor crawler chassis via the robot socket server.

## Usage

```bash
crawler --host 0.0.0.0 --port 9999
crawler --host 0.0.0.0 --port 9999 --no-camera  # Without camera stream
```

## Camera Stream

The camera stream is served via Vilib on port 9000. Access from another device:

```
http://<raspberry-pi-ip>:9000/mjpg
```

Or with VLC:

```bash
vlc http://<raspberry-pi-ip>:9000/mjpg
```
