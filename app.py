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
LEVEL_POSSIBLE = [1, 2, 3, 4, 5]

class User:
    def __init__(self, uuid, email: str, name: str, password: str, role: str, journal: str = None, is_subscribe=True):
        self.uuid = uuid
        self.email = email
        self.name = name
        self.password = password
        self.role = role
        self.journal = journal
        self.is_subscribe = is_subscribe

    def __repr__(self):
        return f"<User: {self.uuid=} {self.email=} {self.name=} {self.role=} {self.journal=}>"


users: list[User] = []
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
    message_jour_dict[jour] = (message, user.name)


"""
assert get_message_jour_cont == MESSAGE_JOUR_EMPTY
assert get_message_jour_editeur == EDITEUR_JOUR_EMPTY
"""


#########################
#    DECORATEUR
#########################


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


#########################
#    USER
#########################


def get_user_by_email(email) -> User | None:
    print(f"get_user_by_email({email=})")
    for one_user in users:
        if one_user.email == email:
            return one_user

    return None


def get_user_by_uuid(uuid4) -> User | None:
    print(f"get_user_by_uuid({uuid4=})")
    for one_user in users:
        if one_user.uuid == uuid4:
            return one_user

    return None


def add_user(email, name, password, role, journal_p=None):
    already_exist = get_user_by_email(email)
    if already_exist is not None: return -1

    uuid4 = str(uuid.uuid4())
    hashed_password = ph.hash(password)
    users.append(User(uuid=uuid4, email=email, name=name, password=hashed_password, role=role, journal=journal_p))
    return 1


def change_user_credentials(user_logged, email, password) -> int:
    print(f"change_user_credentials({user_logged=}, {email=}, {password=})")
    old_email = user_logged.email

    hashed_password = ph.hash(password)
    for one_user in users:
        if one_user.email == old_email:
            one_user.email = email
            one_user.password = hashed_password
            break
    return 1


assert add_user('luc@mail.com', 'luc', '1uC', 'user') == 1
assert add_user('eli@mail.com', 'eli', '3L1', 'admin') == 1
assert add_user('val@gmail.com', 'val', 'val', 'admin',
                "Mon mot de passe maître pour firefox: MonM2PMX1TR3221, ma clé API Discord: D1sCORDAP1K2I") == 1
assert add_user('hacker@gmail.com', 'XxUnknowUserxX', 'hacker', 'user') == 1


def get_security_level() -> int:
    print(f"get_security_level...")
    print(f"securité cookie: {request.cookies.get('security_level')}")
    level = request.cookies.get('security_level', '1')
    try:
        level = int(level)
        if level not in LEVEL_POSSIBLE:
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
    Maximum de protection --> mais tjr XSS pour usurpation d'action
    5:
    jinja2 sanitize et empeche l'injection xss
    """
    cookie_configs = {
        1: {  # Niveau 1 : Totalement vulnérable
            'httponly': False,
            'secure': True,
            'samesite': 'None',
        },
        2: {  # Niveau 2 : HttpOnly activé        VOL COOKIE XSS IMP
            'httponly': True,
            'secure': True,
            'samesite': 'None',
        },
        3: {  # Niveau 3 : HttpOnly + SameSite     CSRF AUTO IMP (nécessite GET + user action)
            'httponly': True,
            'secure': True,
            'samesite': 'Lax',
        },
        4: {  # Niveau 4 : Sécurité complète        CSRF IMP
            'httponly': True,
            'secure': True,
            'samesite': 'Strict',
        },
        5: {  # Niveau 5 : Sécurité complète + la template jinja2 va tout échapper
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
        user = get_user_by_email(email)

        phash = user.password if user else dummy_hash
        preal = password if user else 'something else'

        try:
            ph.verify(phash, preal)
        except:
            print('Not good pass')
            return render_template('loginV2.html', error='Invalid email or password'), 401

        if user is None:  # si mdp de test correspond au mdp user inexistant ...
            return render_template('loginV2.html', error='Invalid email or password'), 401

        token = jwt.encode({
            'uid': user.uuid,
            'exp': datetime.now(timezone.utc) + timedelta(seconds=app.config['JWT_LIFETIME'])},
            app.config['JWT_SECRET_KEY'], algorithm="HS256")

        # Récupérer le niveau de sécurité
        security_level = get_security_level()

        redirection = redirect(url_for('dashboard'))
        response = make_response(redirection)

        # ici se met le JWT avec les params variable de sécurité
        response = set_jwt_by_level(response, 'jwt_token', token, security_level)

        # Ici on met juste le niveau de sécurité coté client sans expiration
        response.set_cookie('security_level', str(security_level), max_age=None, samesite='None', secure=True)
        return response
    else:  # GET
        security_level = get_security_level()
        return render_template('loginV2.html', security_level=security_level)


@app.route('/set_level/<int:level>')
def set_level(level):
    """Endpoint pour changer le niveau de sécurité"""
    if level not in LEVEL_POSSIBLE:
        return "Niveau invalide (1-5)", 400

    response = make_response(redirect(DIFFILCULTY_ROUTE))
    response.set_cookie('security_level', str(level), max_age=None, samesite='None', secure=True)
    return response


def get_user_from_jwt() -> User | None:
    token = request.cookies.get('jwt_token')
    if not token:
        return None
    try:
        data = jwt.decode(
            token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
    except:
        return None

    return get_user_by_uuid(data['uid'])


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


@app.route('/journal', methods=['GET'])
@token_required
def journal(user, security_level):
    print("/journal")
    print(f"{user=}, {security_level=}")
    return render_template("journal.html", user=user)


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


@app.route('/api/change_credential', methods=['POST'])
@token_required
def change_credential(user, security_level):
    print(f"change_credential({user=}, {security_level=})")
    new_email = request.form['new_email']
    new_password = request.form['new_password']
    error = change_user_credentials(user, new_email, new_password)
    if error == -1: return render_template("indexV3.html", message='Une erreur est survenue', user=user,
                                           security_level=security_level,
                                           **get_message_jour_context())
    print(f"change_credential OK")
    return render_template("indexV3.html", user=user, security_level=security_level,
                           **get_message_jour_context())


@app.route('/api/unsubscribe', methods=['GET'])
@token_required
def user_unsubscribe(user, security_level):
    print(f"user_unsubscribe({user=}, {security_level=})")
    if not user.is_subscribe:
        print(f"user_unsubscribe NO SUBSCRIBED")
        return render_template("indexV3.html", message="Vous n'êtes pas abonné(e) !", user=user,
                               security_level=security_level,
                               **get_message_jour_context())
    user.is_subscribe = False
    print(f"user_unsubscribe OK")
    return render_template("indexV3.html", message="Vous êtes désabonné(e) !", user=user, security_level=security_level,
                           **get_message_jour_context())


@app.route('/api/unsubscribeSAFE', methods=['POST'])
@token_required
def user_unsubscribe_safe(user, security_level):
    print(f"user_unsubscribeSAFE({user=}, {security_level=})")
    if not user.is_subscribe:
        print(f"user_unsubscribeSAFE NO SUBSCRIBED")
        return render_template("indexV3.html", message="Vous n'êtes pas abonné(e) !", user=user,
                               security_level=security_level,
                               **get_message_jour_context())
    user.is_subscribe = False
    print(f"user_unsubscribeSAFE OK")
    return render_template("indexV3.html", message="Vous êtes désabonné(e) !", user=user, security_level=security_level,
                           **get_message_jour_context())


if __name__ == '__main__':
    load_dotenv()
    host = os.getenv("FLASK_HOST")
    port = os.getenv("FLASK_PORT_APP")
    print(f"Starting app on {host}:{port}")
    is_https: bool = True if str(os.getenv("HTTPS")) == "1" else False
    app.run(host=host, port=port,
            ssl_context=("certificates/loutreserver.crt", "certificates/loutreserver.key") if is_https else None)
