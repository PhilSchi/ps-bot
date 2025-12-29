# ps-bot

This repo is organized as a small monorepo with a shared library and multiple apps.

## Layout

- `libs/shared_lib`: reusable code that apps import
- `apps/test_app`: example app that uses `shared_lib`

## Setup (pip + venv)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Run the example app

```bash
test-app --name Philip
```

## Run tests

```bash
pytest
```
