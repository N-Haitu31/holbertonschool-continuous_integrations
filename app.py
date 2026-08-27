from flask import Flask
import os

GREETING_NAME = os.environ.get("GREETING_NAME", "stranger")

app = Flask(__name__)

@app.route("/")
def home():
    return f"Hello {GREETING_NAME} from Docker!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
