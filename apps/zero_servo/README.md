# zero-servo

Interactive CLI for dialing in the zero (center) angle of a servo channel.

## Run

Run directly from source:

```bash
python -m zero_servo.main --channel P0
```

Install the app and run `zero-servo` if you want the CLI script:

```bash
pip install -e apps/zero_servo
zero-servo --channel P0
```

## Commands

- `+` / `-`: nudge by the current step
- `++` / `--`: nudge by 5x the current step
- `set <angle>`: set absolute angle
- `step <angle>`: change step size
- `zero`: set angle to 0
- `show`: show current angle
- `help`: show help
- `quit`: exit and print the final angle
