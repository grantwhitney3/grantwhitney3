# Hello World Flask App

Minimal Flask demo that serves a blinking "Hello World!" page.

## Run locally

```bash
cd hello_app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask --app app run --host 0.0.0.0 --port 5000
```

Open:

```text
http://127.0.0.1:5000/
```
