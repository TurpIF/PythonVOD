#!/usr/bin/python

import signal
import random
import time
import os
import sys
import argparse

import debug
import flux
import MyServer

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Creation d\'un serveur de diffusion de flux d\'images.')
    parser.add_argument('image', metavar = 'IMAGE', type = str, nargs = '*', help = 'liste des images composants le flux')
    parser.add_argument('--flux', help = 'creation d\'un flux a partir de ce fichier de description', dest = 'flux')
    parser.add_argument('--save', help = 'enregistre la description du flux generer au chemin donne', dest = 'save')
    parser.add_argument('--addr', help = 'adresse sous format IPv4 du serveur', dest = 'addr')
    parser.add_argument('--port', type = int, help = 'port d\'ecoute du serveur', dest = 'port')
    parser.add_argument('--ips', type = int, help = 'nombre d\'images envoye aux clients par seconde', dest = 'ips')
    parser.add_argument('--name', help = 'nom du flux', dest = 'name')
    parser.add_argument('--method', help = 'methode de diffusion du flux', dest = 'method', choices = ['tcp_pull', 'tcp_push', 'udp_pull', 'udp_push', 'mcast_push'])
    parser.add_argument('--id', type = int, help = 'id du flux', dest = 'id')
    parser.add_argument('--type', help = 'format des images composants le flux', dest = 'type', choices = ['GIF', 'JPG', 'JPEG', 'BMP', 'PNG'])
    parser.add_argument('--no-server', '-s', action = 'store_true', help = 'n\'execute pas le serveur', dest = 'server')
    parser.add_argument('--verbose', '-v', action = 'count', help = 'niveau de verbosite', dest = 'verbose')

    args = parser.parse_args()

    ff = ''
    if args.flux:
        try:
            ff = open(args.flux, 'r').read()
        except:
            parser.print_help()
            debug.error('[Application]', 'Le fichier de flux `' + args.flux + '` n\'existe pas.')
            sys.exit(1)

    f = flux.flux(ff)

    debug.verbose = args.verbose

    if args.addr:
        f.addr = args.addr
    if args.port:
        f.port = int(args.port)
    if args.ips:
        f.ips = int(args.ips)
    if args.name:
        f.name = args.name
    if args.method:
        f.protocol = args.method.upper()
    if args.id:
        f.id = int(args.id)
    if args.type:
        f.type = args.type
    if args.image:
        f.ls_image_path = list(args.image)
        f.ls_image = []
        for i in f.ls_image_path:
            f.ls_image += [flux.read_image(i)]

    debug.log('[Application' + str(f.id) + ']', 'Flux genere : ' + str(f), 2)


    if args.save:
        m = ''
        m += 'ID: ' + str(f.id) + '\n'
        m += 'Name: ' + f.name + '\n'
        m += 'Type: ' + f.type + '\n'
        m += 'Address: ' + f.addr + '\n'
        m += 'Port: ' + str(f.port) + '\n'
        m += 'Protocol: ' + f.protocol + '\n'
        m += 'IPS: ' + str(f.ips) + '\n'

        for i in f.ls_image_path:
            m += i + '\n'

        try:
            open(args.save, 'w').write(m)
        except:
            parser.print_help()
            debug.error('[Application' + str(f.id) + ']', 'Impossible d\'ecrire dans le fichier `' + args.save + '`')
            sys.exit(1)

    if not args.server:
        debug.log('[Application' + str(f.id) + ']', 'Lancement du serveur', 1)
        name_file = './running/' + str(time.time()) + str(random.random())

        if f.protocol == 'TCP_PUSH':
            server = MyServer.TCPPushServer(f.port, f)
        elif f.protocol == 'TCP_PULL':
            server = MyServer.TCPPullServer(f.port, f)
        elif f.protocol == 'UDP_PUSH':
            server = MyServer.UDPPushServer(f.port, f)
        elif f.protocol == 'UDP_PULL':
            server = MyServer.UDPPullServer(f.port, f)
        elif f.protocol == 'MCAST_PUSH':
            server = MyServer.MyMCASTServer(f.addr, f.port, f)

        def quit(*args):
            debug.log('[Application' + str(f.id) + ']', 'Arret du serveur', 1)

            server.stop()
            server.join()

            try:
                os.remove(name_file)
            except:
                pass
            sys.exit(0)

        signal.signal(signal.SIGINT, quit)

        try:
            server.start()

            m = ''
            m += 'ID: ' + str(f.id) + '\n'
            m += 'Name: ' + f.name + '\n'
            m += 'Type: ' + f.type + '\n'
            m += 'Address: ' + f.addr + '\n'
            m += 'Port: ' + str(f.port) + '\n'
            m += 'Protocol: ' + f.protocol + '\n'
            m += 'IPS: ' + str(f.ips) + '\n'

            for i in f.ls_image_path:
                m += i + '\n'

            try:
                open(name_file, 'w').write(m)
            except:
                pass

            while True:
                pass
        except KeyboardInterrupt:
            quit()

