# Hacking éthique : vol de session

https://forum:5000/  
https://malveillance:5001/  
https://mouhaha:5002/  
https://mouhahaha:5003/

# Réserver les noms de domaines locaux

## Le fichier hosts se trouve dans:

### Windows

```
C:\Windows\System32\drivers\etc\hosts
```

### Linux, MacOS et autres UNIX

```
/etc/hosts
```

## Ajouter dans ce fichier :

```
127.0.0.1   forum
127.0.0.1   malveillance
127.0.0.1   mouhaha
127.0.0.1   mouhahaha
```

Veillez à bien remettre ce fichier tel qu'il était après avoir terminé la démo.

# Lancer la démo

## Initialisation

```
git clone git@gibson.telecomnancy.univ-lorraine.fr:matteo.pouillat/hacking-ethique-vol-de-session.git
(ou utiliser le zip fourni)
python -m venv venv
./venv/bin/activate
source ./venv/bin/activate
pip install -r requirements.txt
```

## Pour lancer `forum` en HTTPS/HTTP:

### HTTPS

Dans le `.env`

```
HTTPS=1
```

### HTTP

Dans le `.env`

```
HTTPS=0
```

⚠️ Relancer `forum` par la suite.

## Pour lancer les différentes applications

Pour lancer `forum` :

```
python3 forum.py
```

Pour lancer `malveillance` :

```
python3 malveillance.py
```

Pour lancer `mouhaha`:

```
python3 mouhaha.py
```

Pour lancer `mouhahaha`:

```
python3 mouhahaha.py
```

## Guideline

### ⚠️

Il est recommandé de toujours relancer chaque application qui nécessite une étape afin de ne pas être embêté par l'étape
précédente (mot de passe changé, etc.).

### 1.Vol cookie: MITM

Prérequis :

- Lancer `forum` en HTTP
- Sécurité 1

Explication : se référer au fichier [mitm.md](mitm.md).

### 1.5 Prémice PoC : les cookies ne sont pas envoyés en dehors du domaine, comment les exfiltrer alors ??

Prérequis :

- Lancer `forum` en HTTPS
- Sécurité 2
- Lancer `malveillance`

Explication : prendre le 2e payload et demander une image à `malveillance` ; ah bah `malveillance` n’a rien...  
Attendu : une requête qui a juste réchauffé l'océan.

### 2. Vol cookie: XSS document.cookies

Prérequis :

- Lancer `forum` en HTTPS
- Sécurité 1
- Lancer `malveillance`

Explication : prendre le 1er payload et le mettre dans un commentaire.  
Attendu : `malveillance` reçoit le cookie de connexion.

### 3. Utilisation Cookie: CSRF changement de mdp

Prérequis :

- Sécurité 2
- Lancer `mouhaha` ⚠️ Au moment importun !

Explication : se reconnecter avec la bonne sécurité, lancer `mouhaha`, bravo, vous n'avez plus de compte.  
Attendu : nouveaux identifiants : "mouhaha@gmail.com" : "mouhaha".

### 4. Utilisation Cookie: CSRF action GET mal configurée

Prérequis :

- Sécurité 3
- Lancer `mouhahaha`

Explication : se reconnecter avec la bonne sécurité, lancer `mouhahaha`, cliquer sur le lien.  
Attendu : Vous êtes maintenant désabonné, car vous avez été leurré.  
Dans votre malheur, vous avez la chance que notre site utilise un message explicite à votre demande : 'Vous êtes
désabonné(e) !'. Au lieu que la majorité des sites qui redirige vers un message général comme "Votre demande a été prise
en compte" où l'utilisateur ne se rend pas compte immédiatement qu'il a été trompé et croit toujours avoir participé à
un jeu concours par exemple.

### 5. Utilisation Cookie: XSS journal intime

Prérequis :

- Sécurité 4 (Strict juste pour montrer la puissance de l'injection XSS)
- Lancer `malveillance`

Explication : se reconnecter avec la bonne sécurité, mettre le dernier payload et admirer ses plus grands secrets se
faire exfiltrer.  
Attendu : contenue de la page /journal sur `malveillance` (différence entre CSRF aveugle et XSS totalement usurpatrice).

### 6. Se mettre en sécurité grâce aux ninjas (jinja2)

Prérequis :

- Sécurité 5
- Lancez ce que vous voulez vous n'aurez plus jamais mes données !!

Explication : se reconnecter avec la bonne sécurité, lancer chaque payload dans un jour différent.  
Attendu : l’attaquant se retrouve face à sa propre stupidité.
