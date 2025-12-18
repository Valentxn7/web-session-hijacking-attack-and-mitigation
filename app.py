from flask import Flask, render_template, request, redirect, url_for, make_response
import jwt
from datetime import datetime, timezone, timedelta
from functools import wraps
import uuid
from argon2 import PasswordHasher
from dotenv import load_dotenv
import os

DIFFILCULTY_ROUTE = "/difficulty"
DIFFILCULTY_PAGE = "difficulty.html"

ph = PasswordHasher()
dummy_hash = ph.hash('this is a dummy')
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'changethis'
app.config['JWT_LIFETIME'] = 3600

users: list[object] = []
user_email_index = {}
user_uid_index = {}
jour: int = 28
MESSAGE_JOUR_EMPTY: str = "Pas de message du jour, rajouter en un !"
EDITEUR_JOUR_EMPTY: str | None = None
message_jour_dict: dict[int, tuple[str, str | None]] = dict()

for nb_jour in range(0, 31 + 1):
    message_jour_dict[nb_jour] = (MESSAGE_JOUR_EMPTY, EDITEUR_JOUR_EMPTY)


#########################
#    MESSAGE DU JOUR
#########################

def get_message_jour_cont():
    global jour
    message = message_jour_dict[jour][0]
    print(f"get_message_jour_cont()={message}")
    return message


def get_message_jour_editeur():
    global jour
    editeur = message_jour_dict[jour][1]
    print(f"get_message_jour_editeur()={editeur}")
    return editeur


def get_message_jour_context():
    return {
        "jour": jour,
        "contenue_message_du_jour": get_message_jour_cont(),
        "editeur_message_du_jour": get_message_jour_editeur()
    }


def update_message_du_jour(message, user):
    message_jour_dict[jour] = (message, user['name'])


"""
assert get_message_jour_cont == MESSAGE_JOUR_EMPTY
assert get_message_jour_editeur == EDITEUR_JOUR_EMPTY
"""


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
assert add_user('hacker@gmail.com', 'XxUnknowUserxX', 'hacker', 'user') == 1


def get_security_level() -> int:
    print(f"get_security_level...")
    print(f"securité cookie: {request.cookies.get('security_level')}")
    level = request.cookies.get('security_level', '1')
    try:
        level = int(level)
        if level not in [1, 2, 3, 4]:
            level = 1
    except ValueError:
        level = 1
    print(f"security returned level: {level}")
    print(f"get_security_level OK")
    return level


def set_jwt_by_level(response, key, value, level):
    """
    1:
    Niveau 1 : Totalement vulnérable
    httponly=False --> JavaScript peut lire le cookie (XSS)
    secure=False   --> Fonctionne en HTTP
    samesite=None  --> Vulnérable au CSRF
    2:
    httponly=True --> Protection contre XSS
    Toujours vulnérable au CSRF
    3:
    samesite='Lax' --> Protection CSRF partielle
    4:
    httponly=True + secure=True + samesite='Strict'
    Maximum de protection
    """
    cookie_configs = {
        1: {  # Niveau 1 : Totalement vulnérable
            'httponly': False,
            'secure': False,
            'samesite': None,
        },
        2: {  # Niveau 2 : HttpOnly activé
            'httponly': True,
            'secure': False,
            'samesite': None,
        },
        3: {  # Niveau 3 : HttpOnly + SameSite
            'httponly': True,
            'secure': False,
            'samesite': 'Lax',
        },
        4: {  # Niveau 4 : Sécurité complète
            'httponly': True,
            'secure': True,
            'samesite': 'Strict',
        }
    }

    config = cookie_configs.get(level, cookie_configs[1])
    response.set_cookie(
        key,
        value,
        max_age=app.config['JWT_LIFETIME'],
        path="/",
        **config
    )
    return response


@app.route('/login', methods=['GET', 'POST'])
def login():
    print(f"/login")
    print(f"REQUEST METHOD {request.method=}")
    if request.method == 'POST':
        print(f"POST")
        email = request.form['email']
        password = request.form['password']
        user = user_email_index.get(email)

        phash = users[user]['password'] if user else dummy_hash
        preal = password if user else 'something else'

        try:
            ph.verify(phash, preal)
        except:
            print('Not good pass')
            return render_template('loginV2.html', error='Invalid email or password'), 401

        if user is None:  # si mdp de test correspond au mdp user inexistant ...
            return render_template('loginV2.html', error='Invalid email or password'), 401

        token = jwt.encode({
            'uid': users[user]['uid'],
            'exp': datetime.now(timezone.utc) + timedelta(seconds=app.config['JWT_LIFETIME'])},
            app.config['JWT_SECRET_KEY'], algorithm="HS256")

        # Récupérer le niveau de sécurité
        security_level = get_security_level()

        redirection = redirect(url_for('dashboard'))
        response = make_response(redirection)

        # ici se met le JWT avec les params variable de sécurité
        response = set_jwt_by_level(response, 'jwt_token', token, security_level)

        # Ici on met juste le niveau de sécurité coté client sans expiration
        response.set_cookie('security_level', str(security_level), max_age=None)
        return response
    else:  # GET
        security_level = get_security_level()
        return render_template('loginV2.html', security_level=security_level)


@app.route('/set_level/<int:level>')
def set_level(level):
    """Endpoint pour changer le niveau de sécurité"""
    if level not in [1, 2, 3, 4]:
        return "Niveau invalide (1-4)", 400

    response = make_response(redirect(DIFFILCULTY_ROUTE))
    response.set_cookie('security_level', str(level), max_age=None)
    return response


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
    return users[current_user]


def token_load(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = get_user_from_jwt()
        security_level = get_security_level()
        print(f"token_load: user={user}, security_level={security_level}")
        return f(user, security_level, *args, **kwargs)

    return wrapper


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_user_from_jwt()
        if token is None:
            return render_template('indexV3.html', message='Veuillez vous connecter !'), 401
        security_level = get_security_level()
        return f(token, security_level, *args, **kwargs)

    return decorated


@app.route('/')
@token_load
def home(user, security_level):
    return render_template("indexV3.html", user=user, security_level=security_level,
                           **get_message_jour_context())


@app.route('/dashboard')
@token_load
def dashboard(user, security_level):
    return render_template("indexV3.html", user=user, security_level=security_level,
                           **get_message_jour_context())


@app.route('/logout')
@token_required
def logout(user, security_level):
    redirection = redirect('/')
    response = make_response(redirection)

    # Supprimer le cookie
    response.delete_cookie('jwt_token')
    return response


@app.route(DIFFILCULTY_ROUTE)
@token_load
def difficulty(user, security_level):
    print("/difficulty")
    print(f"user: {user}, security_level: {security_level}")
    return render_template(DIFFILCULTY_PAGE, user=user, security_level=security_level)


@app.route('/message_du_jour', methods=['POST'])
@token_required
def message_du_jour(user, security_level):
    print("/message_du_jour")
    message = request.form['message_du_jour']
    if not message:
        return render_template("indexV3.html", user=user, security_level=security_level,
                               **get_message_jour_context(),
                               message="Veuillez entrer un message !")
    print(f"{user=}, {security_level=}, {message=}")
    update_message_du_jour(message, user)
    print(f"{get_message_jour_cont()=}, {get_message_jour_editeur()=}")
    return render_template("indexV3.html", user=user, security_level=security_level,
                           **get_message_jour_context())


@app.route('/next_day', methods=['GET'])
@token_required
def next_day(user, security_level):
    global jour
    print("/next_day")
    if 1 <= jour <= 30:
        jour += 1
    return render_template("indexV3.html", user=user, security_level=security_level,
                           **get_message_jour_context())


@app.route('/prec_day', methods=['GET'])
@token_required
def prec_day(user, security_level):
    global jour
    print("/prec_day")
    if 2 <= jour <= 31:
        jour -= 1
    return render_template("indexV3.html", user=user, security_level=security_level,
                           **get_message_jour_context())


if __name__ == '__main__':
    load_dotenv()
    host = os.getenv("FLASK_HOST")
    port = os.getenv("FLASK_PORT_APP")
    print(f"Starting app on {host}:{port}")
    is_https: bool = False
    app.run(host=host, port=port, ssl_context = ("certificates/loutreserver.crt", "certificates/loutreserver.key") if is_https else None)
