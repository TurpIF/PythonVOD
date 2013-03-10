#!/usr/bin/python

import os
import sys
import argparse

import debug
import flux
import MyServer

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Creation d\'un serveur HTTP diffusant le catalogue des serveurs en fonctionnement.')
    parser.add_argument('--dir', help = 'change le dossier ou sont lu les descripteurs de serveurs actifs', dest = 'dir')
    parser.add_argument('--port', type = int, help = 'port d\'ecoute du serveur', dest = 'port', required = True)
    parser.add_argument('--verbose', '-v', action = 'count', help = 'niveau de verbosite', dest = 'verbose')

    args = parser.parse_args()

    debug.verbose = args.verbose

    dir = './running/'
    if args.dir:
        dir = args.dir

    http_addr = '127.0.0.1'
    http_port = int(args.port)

    ls =  [dir + f for f in os.listdir(dir)]
    debug.log('[Application]', str(len(ls)) + ' serveur en activite.', 1)

    ls_flux = []
    for f in ls:
        ls_flux += [flux.flux(open(f, 'r').read())]

    header = '''HTTP/1.1 200 OK
Content-Type: text/plain
Connection: Keep-Alive
Server: TP_3IF_SERVER
Content-Length: '''

    catalog = ''
    catalog += 'ServerAddress: ' + http_addr + ' \r\n'
    catalog += 'ServerPort: ' + str(http_port) + ' \r\n'
    catalog += ' \r\n'.join([str(f) for f in ls_flux])
    catalog += '\r\n'
    catalog = header + str(len(catalog)) + '\r\n\r\n' + catalog

    debug.log('[Application]', 'Generated catalog from server informations : \r\n' + catalog, 2)

    server = MyServer.CatalogServer(http_port, catalog, 5)

    try:
        debug.log('[Application]', 'Running ...', 1)
        server.start()

        while True:
            pass
    except KeyboardInterrupt:
        debug.log('[Application]', 'Stoopping ...', 1)
        server.stop()
        server.join()

