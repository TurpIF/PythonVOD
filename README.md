PythonVOD
=========
Serveur de diffusion d'image en python.
Différents protocoles sont gérés pour la diffusion : TCP, UDP et MultiCAST.
Les protocoles TCP et UDP ont deux modes de focntionnement : Pull et Push.
L'un envoie continuellement les images au clients tandis que l'autre attend la demande du client
pour envoyer l'image.
Pour des images de faibles qualité, le serveur peut les envoyer à plus de 24 images par seconde.
Il peut donc être utilisé comme serveur vidéo.

Je ne fournis pas de client n'en ayant pas fait moi même et je ne connais pas la licence de diffusion de ceux que j'ai testé.

Pour tester :
A executer dans une console
    python __main__.py ./serv 1
1 correspond au niveau de verbosite (compris entre 0 et 4)

ou

    for file in `ls ./flux/*`; do ((./server.py --flux=$file -v) &); done;
    ./catalog --port 8080 -v &

Pour arreter :
    ps -aux | grep ./server | awk '{ print $2 }' | xargs kill SIGINT
    ps -aux | grep ./catalog | awk '{ print $2 }' | xargs kill SIGINT


Le dossier ./running doit etre ecrivable par python
Les fichiers d'interface ./server.py et ./catalog.py doivent etre executable. Sinon, alors la commande correspondante est python server.py et python catalog.py.
Les serveurs utilisent python 2.7

Lancement d'un serveur de diffusion d'image:

    usage: server.py [-h] [--flux FLUX] [--save SAVE] [--addr ADDR] [--port PORT]
                     [--ips IPS] [--name NAME]
                     [--method {tcp_pull,tcp_push,udp_pull,udp_push,mcast_push}]
                     [--id ID] [--type {GIF,JPG,JPEG,BMP,PNG}] [-no-server]
                     [--verbose]
                     [IMAGE [IMAGE ...]]
    
    Creation d'un serveur de diffusion de flux d'images.
    
    positional arguments:
      IMAGE                 liste des images composants le flux
    
    optional arguments:
      -h, --help            show this help message and exit
      --flux FLUX           creation d'un flux a partir de ce fichier de
                            description
      --save SAVE           enregistre la description du flux generer au chemin
                            donne
      --addr ADDR           adresse sous format IPv4 du serveur
      --port PORT           port d'ecoute du serveur
      --ips IPS             nombre d'images envoye aux clients par seconde
      --name NAME           nom du flux
      --method {tcp_pull,tcp_push,udp_pull,udp_push,mcast_push}
                            methode de diffusion du flux
      --id ID               id du flux
      --type {GIF,JPG,JPEG,BMP,PNG}
                            format des images composants le flux
      --no-server, -s        n'execute pas le serveur
      --verbose, -v         niveau de verbosite


Lancement du serveur de distribution du catalogue

    usage: catalog.py [-h] [--dir DIR] --port PORT [--verbose]
    
    Creation d'un serveur HTTP diffusant le catalogue des serveurs en fonctionnement.
    
    optional arguments:
      -h, --help     show this help message and exit
      --dir DIR      change le dossier ou sont lu les descripteurs de serveurs
                     actifs
      --port PORT    port d'ecoute du serveur
      --verbose, -v  niveau de verbosite


Exemple d'utilisation :

    #!/bin/bash
    
    # Lancement de tous les serveurs de flux décrits par les fichiers du dossier ./flux
    ls_pid = array()
    for file in `ls ./flux/*`; do
        ./server.py --flux=$file -v &;
        ls_pid[$file] = $!
    done;
    
    # Demarrage du serveur de catalogue
    ./catalog --port 8080 -v
    
    # Arret du catalog
    kill SIGINT $!
    
    # Arret des serveurs de diffusion
    for pid in "${ls_pid[@]}"; do
        kill SIGINT $pid;
    done;
    
    # Ou arret des serveurs si on a perdu les PID
    ps -aux | grep './server.py' | awk '{ print $2 }' | xargs kill SIGINT
