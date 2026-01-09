# Hacking éthique : vol de session

http://forum:5000/ (HTTP)  
https://forum:5000/ (HTTPS)  
https://malveillance:5001/  
https://mouhaha:5002/  
https://mouhahaha:5003/

GitLab : [lien du répertoire](https://gibson.telecomnancy.univ-lorraine.fr/matteo.pouillat/hacking-ethique-vol-de-session)

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
# (ou utiliser le zip fourni)
python -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```

## Pour lancer `forum` en HTTPS/HTTP :

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

#### Et ensuite lancer l'application dans votre navigateur (les liens sont au début de ce fichier)

## Vos comptes à dispositions

### Compte utilisateur (val)

Il sera votre compte principal pour ce démonstrateur :

```
Email: val@gmail.com
Mot de passe: val
```

### Compte attaquant (hacker)

Si vous souhaitez faire une attaque réaliste, pour par exemple, déployer les injections XSS avec le compte hacker, se
déconnecter, et se faire piéger en se reconnectant avec votre compte utilisateur.

```
Email: hacker@gmail.com
Mot de passe: hacker
```

## Les payloads à dispositions

Vous trouverez sur `forum`, tout en bas de la page, 3 textes distinctement séparés.  
Chacun d'entre eux est un exemple à copier-coller plus tard (une attaque ou une action).  
Les payloads seront nommés 1ᵉ, 2ᵉ et 3ᵉ, dans leur sens vertical, le 1ᵉ étant le plus haut sur la page.

L'action "utiliser le Xᵉ payload" signifie copier le texte et le coller dans un message du jour et poster le message
(avec le compte attaquant). Ce payload devra ensuite être lue par le compte utilisateur (en changeant de compte) afin de
l'exécuter sur lui.

## Guideline

### ⚠️

Il est recommandé de toujours relancer chaque application qui est requise pour une étape afin de ne pas être embêté par l'étape
précédente (mot de passe changé, etc.).  
De plus, pour changer la difficulté, il est **obligatoire** de se **déconnecter** pour recréer le cookie qui indique le niveau.  
Le démonstrateur est conçu pour que chaque niveau corrige le précédent, testez vous-mêmes les manipulations !

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

Que se passe-t-il pour les cookies lorsqu'une ressource externe est chargée (comme une image) depuis `forum` ?

On va se placer dans le cadre où un attaquant possède un compte sur `forum` et publie un message chargeant une image située sur `malveillance`, un autre site que l'attaquant a conçu pour afficher les cookies que les requêtes contiennent.

Explication : se connecter au compte attaquant et utiliser le 2ᵉ payload. Se re-connecter avec votre compte utilisateur et consulter le message du jour publié par hacker.  
En allant voir sur https://malveillance:5001/ observer le résultat.  

On peut voir que 2 (ou plus si vous avez rechargé la page) requêtes ont été faites vers `malveillance` mais il n'y a aucun cookie. En effet lorsqu'un navigateur fait une requête vers un site, il n'envoie que les cookies qui concernent le site d'arrivée.  
Donc charger une image depuis `malveillance` n'envoie que les cookies qui concernent `malveillance` et non ceux de `forum`.

Attendu : une requête qui a juste réchauffé l'océan.

### 2. Vol cookie: XSS document.cookies

Prérequis :

- Lancer `forum` en HTTPS
- Sécurité 1
- Lancer `malveillance`

Pour pouvoir récupérer les cookies, on pourrait utiliser le fait qu'un script JavaScript a accès aux cookies de la page en cours à travers l'objet document.cookies.  
Cette fois-ci, on va inclure un script dans la page plutôt qu'une image.

Explication : utiliser le 1ᵉ payload (cliquer sur "jour suivant" ou "jour précédent" pour passer à un autre jour, ou relancer le `forum` **recommandé**).  
Attendu : `malveillance` reçoit le cookie de connexion, vous pouvez le copier dans son navigateur pour vérifier qu'il suffit pour usurper la session de votre compte utilisateur.  
Comment le recopier dans mon navigateur ?  
Effectuer un clic droit sur la page de `forum`, cliquer sur "Inspecter", cliquer sur "Stockage", ensuite sur "Cookies", ensuite sur "https://forum:5000" et changer la valeur du cookie dont le nom est "jwt_token" par la valeur que vous avez reçue sur `malveillance`.

### 3. Utilisation Cookie: CSRF changement de mdp

Prérequis :

- Sécurité 2
- Lancer `mouhaha` ⚠️ Au moment opportun !

Maintenant au niveau 3 les cookies sont marqués HTTP-Only ce qui signifie que ce cookie n'est plus accessible depuis JavaScript.  
On va donc chercher une nouvelle méthode.  

On a dit avant que lorsqu'on fait une requête vers un site B en étant sur une page du site A le navigateur envoie automatiquement les cookies nécessaires qui concernent le site B. Donc si l'attaquant parvient à faire visiter à une victime un site qui fait une requête vers forum, alors le navigateur ajoute le cookie de session de la victime pour forum (si elle a un compte).  
On ne peut pas récupérer le cookie, mais on peut l'utiliser indirectement avec le navigateur comme intermédiaire.

Explication : se reconnecter avec la bonne sécurité, lancer `mouhaha`, bravo, vous n'avez plus de compte.  
Attendu : nouveaux identifiants : "mouhaha@gmail.com" : "mouhaha".

Ici donc, `mouhaha` a demandé à votre place le changement de vos identifiants et votre navigateur a fourni votre cookie, car celui-ci n'était pas assez protégé.

### 4. Utilisation Cookie: CSRF action GET mal configurée

Prérequis :

- Sécurité 3
- Lancer `mouhahaha`

L'attribut Same-Site des cookies avec la valeur 'Lax' empêche l'envoi des cookies depuis un autre site, à l'exception du cas où il s'agit d'une requête GET en navigation top level.  
C'est-à-dire avec un clic de l'utilisateur et un changement de l'URL de votre navigateur.  
Aujourd'hui les navigateurs basés sur Chromium appliquent Same-Site à Lax à tous les cookies par défaut depuis 2020.

Lax permet les requêtes GET, car par convention, elles ne changent pas l'état (elles ne font que demander des données).  
Et puisque c'est une requête de navigation, elles ne permettent pas de récupérer ces données, donc cela est sans risque.  
Toutefois, il arrive que des développeurs peu attentifs changent l'état avec une route GET.  
Dans ces cas, on peut par du social engineering amener la victime à cliquer sur un lien qui va avoir un impact sur ces données.

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

Cette fois-ci avec Same-Site à 'Strict', même les requêtes GET de navigation top level avec un clic de l'utilisateur ne permettent plus la CSRF (testez par vous-même).

En revanche, on peut revenir au XSS, et appliquer les méthodes qu'on a utilisées en CSRF.  
On avait vu qu'on ne peut plus récupérer les cookies, mais on peut toujours faire des requêtes en utilisant le cookie, comme dans les CSRF.  
La grande différence, c'est que ça se fait à l'intérieur du domaine forum et donc sur le même site : on contourne la validation Same-Site=Strict.  
La faille XSS usurpe totalement l'identité et le comportement d'un utilisateur, et grâce à ce fait permet d'avoir toutes ses permissions et d'accéder à toutes ses données.

Explication : se reconnecter avec la bonne sécurité, utiliser le 3ᵉ payload et admirer ses plus grands secrets se
faire exfiltrer.  
Attendu : contenue de la page /journal sur `malveillance` (différence entre CSRF aveugle et XSS totalement usurpatrice).

### 6. Se mettre en sécurité grâce aux ninjas (jinja2)

Prérequis :

- Sécurité 5
- Lancez ce que vous voulez vous n'aurez plus jamais mes données !!

Ici, une vraie sécurité qui vient faire en sorte que notre balise \<script> (et toutes les autres balises HTML) qui est à la base de l'interprétation de notre code malveillant, soient affichés comme textes et non comme code qui doit être traité par notre navigateur.  
Cela nous protège donc contre l'attaque XSS dans notre cas.  

Explication : se reconnecter avec la bonne sécurité, utiliser chaque payload dans un jour différent.  
Attendu : l’attaquant se retrouve face à sa propre stupidité.
