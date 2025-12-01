from flask import Flask, render_template, request, redirect, url_for, make_response
import jwt
import uuid
from datetime import datetime, timezone, timedelta
from functools import wraps
import uuid
from argon2 import PasswordHasher
from pprint import pp

ph = PasswordHasher()
dummy_hash = ph.hash('this is a dummy')
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'changethis'
app.config['JWT_LIFETIME'] = 3600

users = []
user_email_index = {}
user_uid_index = {}


def add_user(email, name, password, role):
    if user_email_index.get(email) is not None: return -1
    uid = str(uuid.uuid4())
    for _ in range(10):
        if user_uid_index.get(uid) is None: break
    else:
        return -2
    hashed_password = ph.hash(password)
    users.append({
        'uid': uid,
        'email': email,
        'name': name,
        'password': hashed_password,
        'role': role,
    })
    user_email_index[email] = len(users) - 1
    user_uid_index[uid] = len(users) - 1
    return 1


assert add_user('luc@mail.com', 'luc', '1uC', 'user') == 1
assert add_user('eli@mail.com', 'eli', '3L1', 'admin') == 1
assert add_user('val@gmail.com', 'val', 'jwt', 'admin') == 1


@app.route('/login', methods=['GET', 'POST'])
def login():
    print(f"/login")
    print(f"REQUEST METHOD {request.method=}")
    if request.method == 'POST':
        print(f"DEMANNNNNNDE DE LOGINNNNNN {request.form=}")
        email = request.form['email']
        password = request.form['password']
        user = user_email_index.get(email)

        phash = users[user]['password'] if user else dummy_hash
        preal = password if user else 'something else'

        try:
            ph.verify(phash, preal)
        except:
            print('Not good pass')
            return render_template('login.html', error='Invalid email or password'), 401

        if user is None:  # si mdp de test correspond au mdp user inexistant ...
            return render_template('login.html', error='Invalid email or password'), 401

        token = jwt.encode({
            'uid': users[user]['uid'],
            'exp': datetime.now(timezone.utc) + timedelta(seconds=app.config['JWT_LIFETIME'])},
            app.config['JWT_SECRET_KEY'], algorithm="HS256")

        redirection = redirect(url_for('dashboard'))
        response = make_response(redirection)

        response.set_cookie('jwt_token', token)
        params = {
            'key': 'jwt_token',
            'value': token,
            'max_age': None,
            'expires': None,
            'path': "/",
            'domain': None,
            'secure': False,
            'httponly': False,
            'samesite': None,
            'partitioned': False,
        }

        """"
        # Cookie sécurisé
        response.set_cookie(
            "access_token",
            token,
            httponly=True,  # JS ne peut pas lire le cookie → protège XSS
            secure=True,  # HTTPS obligatoire
            samesite="Strict",  # empêche CSRF entre sites
            max_age=3600  # expire dans 1h
        )
        """

        return response
    else:  # GET
        return render_template('login.html')


def get_user_from_jwt():
    token = request.cookies.get('jwt_token')
    if not token:
        return None
    try:
        data = jwt.decode(
            token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
    except:
        return None
    current_user = user_uid_index.get(data['uid'])
    if current_user is None:
        return None
        # return jsonify({'message': 'Token is invalid!'}), 401
    return users[current_user]


def token_load(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_user_from_jwt()
        return f(user, *args, **kwargs)

    return wrapper


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_user_from_jwt()
        if token is None:
            return render_template('index.html', message='Veuillez vous connecter !'), 401
        return f(token, *args, **kwargs)

    return decorated


@app.route('/')
@token_load
def home(user):
    return render_template('index.html', user=user)


@app.route('/dashboard')
@token_load
def dashboard(user):
    return render_template('index.html', user=user)


@app.route('/logout')
@token_required
def logout(user):
    redirection = redirect('/')
    response = make_response(redirection)

    # Supprimer le cookie
    response.delete_cookie('jwt_token')
    return response


if __name__ == '__main__':
    app.run()
