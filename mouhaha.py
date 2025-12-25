from flask import Flask, render_template
from dotenv import load_dotenv
import os

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('mouhaha.html')


if __name__ == '__main__':
    load_dotenv()
    host = os.getenv("FLASK_HOST")
    port = int(os.getenv("FLASK_PORT_MOUHAHA"))
    print(f"Starting mouhaha on {host}:{port}")
    app.run(host=host, port=port,
            ssl_context=("certificates/loutreserver.crt", "certificates/loutreserver.key"))
