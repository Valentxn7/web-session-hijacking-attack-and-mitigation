from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
import jwt
import uuid
from datetime import datetime, timezone, timedelta
from functools import wraps
import uuid
from argon2 import PasswordHasher
from pprint import pp

ph = PasswordHasher()
dummy_hash=ph.hash('this is a dummy')
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'changethis'
app.config['JWT_LIFETIME'] = 3600

users = []
user_email_index={}
user_uid_index={}


def add_user(email,name,password,role):
    if user_email_index.get(email) is not None: return -1
    uid=str(uuid.uuid4())
    for _ in range(10):
        if user_uid_index.get(uid) is None: break
    else: return -2
    hashed_password=ph.hash(password)
    users.append({
        'uid': uid,
        'email': email,
        'name': name,
        'password': hashed_password,
        'role': role,
        })
    user_email_index[email]=len(users)-1
    user_uid_index[uid]=len(users)-1
    return 1

assert add_user('luc@mail.com','luc','1uC','user') == 1
assert add_user('eli@mail.com','eli','3L1','admin') == 1

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = user_email_index.get(email)
        if user is None:
            phash=dummy_hash
            password='something else'
        else:
            phash=users[user]['password']
            preal=password
        try:
            ph.verify(phash,preal)
        except:
            print('Not good pass')
            return jsonify({'message': 'Invalid email or password'}), 401
        if user is None:
            return jsonify({'message': 'Invalid email or password'}), 402
        token=jwt.encode({
            'uid': users[user]['uid'],
            'exp': datetime.now(timezone.utc) + timedelta(seconds=app.config['JWT_LIFETIME'])},
            app.config['JWT_SECRET_KEY'], algorithm="HS256")
        redirection = redirect(url_for('dashboard'))
        response = make_response(redirection)
        response.set_cookie('jwt_token', token)
        return response
    return render_template('login.html')

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('jwt_token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            data=jwt.decode(
                    token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        current_user = user_uid_index.get(data['uid'])
        if current_user is None:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(users[current_user], *args, **kwargs)
    return decorated

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/dashboard')
@token_required
def dashboard(current_user):
    return f"Welcome {current_user['name']}! You are logged in as {current_user['role']}."
