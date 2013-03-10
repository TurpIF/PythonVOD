import sys

import flux
import debug
import MyServer

if __name__ == '__main__':
    http_addr = ''
    http_port = 0
    ls_flux = []

    f = ''
    try:
        f = open(sys.argv[1], 'r').read()
    except:
        raise Exception('Error : server informations not found at `' + sys.argv[1] + '`')
        sys.exit()

    debug.verbose = int(sys.argv[2])

    for l in f.split('\n'):
        l = [e.strip() for e in l.strip().split(' ') if e.strip()]

        if len(l) == 2 and l[0] == 'ServerAddress:':
            http_addr = l[1]

        if len(l) == 2 and l[0] == 'ServerPort:':
            http_port = int(l[1])

        if len(l) == 1:
            ls_flux += [flux.flux(open(l[0].replace('\\', '/')).read())]

    if http_addr == '' or http_port == 0:
        raise Exception('Error : server address or server port not found')

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

    server = []
    server += [MyServer.CatalogServer(http_port, catalog, 5)]

    for f in ls_flux:
        if f.protocol == 'TCP_PUSH':
            server += [MyServer.TCPPushServer(f.port, f)]
        elif f.protocol == 'TCP_PULL':
            server += [MyServer.TCPPullServer(f.port, f)]
        elif f.protocol == 'UDP_PUSH':
            server += [MyServer.UDPPushServer(f.port, f)]
        elif f.protocol == 'UDP_PULL':
            server += [MyServer.UDPPullServer(f.port, f)]
        elif f.protocol == 'MCAST_PUSH':
            server += [MyServer.MyMCASTServer(f.addr, f.port, f)]

    debug.log('[Application]', 'Starting...', 1)
    for s in server:
        s.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        debug.log('[Application]', 'Stopping...', 1)

        for s in server:
            s.stop()

        for s in server:
            s.join()

