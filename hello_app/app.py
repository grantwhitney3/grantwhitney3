from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Hello World</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        display: flex;
        justify-content: center;
        align-items: center;
        min-height: 100vh;
        margin: 0;
        background: #111;
        color: #fff;
      }

      .blink {
        animation: blink 1s step-start infinite;
      }

      @keyframes blink {
        50% {
          opacity: 0;
        }
      }
    </style>
  </head>
  <body>
    <h1 class="blink">Hello World!</h1>
  </body>
</html>
"""


@app.get("/")
def index():
    return render_template_string(HTML)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
