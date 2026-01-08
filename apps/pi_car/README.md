# pi-car

Small app that drives a Picarx chassis from a robot socket server.
It also starts a Vilib camera stream in a background thread.

## Run

Run directly from source:

```bash
python -m pi_car.main --host 0.0.0.0 --port 9999
```

Install the app and run `pi-car` if you want the CLI script:

```bash
pip install -e apps/pi_car
pi-car --host 0.0.0.0 --port 9999
```

## Camera stream

The camera thread uses Vilib's web display. On the same WLAN, open the stream in
your browser at:

```
http://<pi-ip>:9000/
```

Some Vilib versions expose the MJPG feed at:

```
http://<pi-ip>:9000/mjpg
```

If neither works, check the Vilib console output for the web port it binds to.

If you do not have `picamera2` available, start the server without the camera:

```bash
pi-car --host 0.0.0.0 --port 9999 --no-camera
```

If `picamera2` is installed system-wide and you need the venv to see it, create
the venv with system site packages:

```bash
python3 -m venv .venv --system-site-packages
```
