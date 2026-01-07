# pi-car

Small app that drives a Picarx chassis from a robot socket server.

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
