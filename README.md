# hacking-ethique-vol-de-session

https://forum:5000/  
https://malveillance:5001/  
https://mouhaha:5002/  
https://mouhahaha:5003/  

# Réserver les noms de domaines locaux

Le fichier hosts se trouve dans:
## Windows
```
C:\Windows\System32\drivers\etc\hosts
```

## Linux, MacOS et autres UNIX
```
/etc/hosts
```

Ajouter dans ce fichier:
```
127.0.0.1   forum
127.0.0.1   malveillance
127.0.0.1   mouhaha
127.0.0.1   mouhahaha
```

Veillez à bien remettre ce fichier tel qu'il était après avoir terminé la démo.

# Lancer la démo
```
git clone lerepo
python -m venv venv
pip install -m requirements.txt
```
Pour lancer forum en HTTPS:
```
HTTPS=1 python app.py
```
Pour changer entre HTTP et HTTPS:
```
HTTPS=0 python app.py
```
Pour lancer malveillance:
```
python interceptor.py
```
Pour lancer mouhaha:
```
python mouhaha.py
```
Pour lancer mouhahaha:
```
python mouhahaha.py
```

## Guide Line
### 1.Vol cookie: MITM

Prérequis: 
- Lancer le serveur en HTTP
- Sécurité 1

explication: avec wireshark, il faut profiter du non chiffrement et de son acceptation pour voler les jwt et se connecter au compte de la victime
voir: [mitm.md](mitm.md)


### 1.5 Prémice PoC: les cookies ne sont pas envoyés en dehors du domaine, comment les exfilter alors ??

Prérequis: 
- Lancer le serveur en HTTPS
- sécurité 1
- Lancer malveillance

explication: prendre le 2eme payload et demander une image à malveillance, ah bah malveillance n'a rien..  
attendu: une requête qui a juste réchauffé l'océan

### 2. Vol cookie: XSS document.cookies

Prérequis: 
- Lancer le serveur en HTTPS
- sécurité 1
- Lancer malveillance

explication: prendre le 1er payload et le mettre dans un commentaire  
attendu: malveillance reçoit le cookie de connexion

### 3. Utilisation Cookie: CSRF changement de mdp

Prérequis:
- sécurité 2
- Lancer mouhaha /!\ Au moment importun !

explication: se reconnecter avec la bonne sécurité, lancer mouhaha, bravo vous n'avez plus de compte  
attendu: nouveau credentials: "mouhaha@gmail.com":"mouhaha"

### 4. Utilisation Cookie: CSRF action GET mal configurée

Prérequis:
- sécurité 3
- Lancer mouhahaha

explication: se reconnecter avec la bonne sécurité, lancer mouhahaha, cliquer sur le lien
attendu: Vous êtes maintenant désabonné car vous avez été leurré. Dans votre malheur, vous avez la chance que notre site utilise un message explicite à votre demande 'Vous êtes désabonné(e) !' au lieu que la majorité des sites qui redirige vers un message général comme "Votre demande a été prise en compte" où l'utilisateur ne se rend pas compte directement qu'il a été trompé et croit toujours avoir participé à un jeux concours par exemple.

### 5. Utilisation Cookie: XSS journal intime

Prérequis:
- sécurité 4 (Strict juste pour flex à mort et montrer la puissance XSS)
- Lancer malveillance

explication: se reconnecter avec la bonne sécurité, mettre le dernière payload et admirer ses plus grands secrets se faire exfiltrer  
attendu: contenue de la page /journal sur malveillance (différence entre CSRF aveugle et XSS totalement usurpatrice)

### 6. Se mettre en sécurité grâce aux ninjas (jinja2 tu l'as ?)

Prérequis:
- sécurité 5
- Lancez ce que vous voulez vous n'aurez plus jamais mes données !!

explication: se reconnecter avec la bonne sécurité, lancer chaque payload dans un jour différent  
attendu: l'attaquant se retrouve fâce à sa propre stupidité
