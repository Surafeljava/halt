# Halt demo (Flask)

Minimal demo to validate rate limiting with a Flask app and a small client.

## Install

```bash
pip install halt-rate
pip install flask
```

(For JavaScript/Node usage, install via npm.)

```bash
npm i halt-rate
```

## Run the Flask app

```bash
python demo/flask_app.py
```

## Run the test client

```bash
python demo/test_rate_limit.py
```

You should see a few `200` responses followed by `429` once the limit is exceeded.
