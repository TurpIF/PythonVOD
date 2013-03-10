import threading
import math

import Server
import Protocol
import flux

class MyMCASTServer(Server.MCASTServer):
    '''Serveur MCAST diffusant un flux donne.'''

    def __init__(self, grp_addr, port, flux):
        '''Initialisation du serveur et generation et mise en cache des messages a envoyer.

        Parametre:
            grp_addr -- Adresse IPv4 du groupe de diffusion
            port     -- Port du groupe de diffusion
            flux     -- flux de donne a envoyer
        '''

        super(MyMCASTServer, self).__init__(grp_addr, port, 1.0 / flux.ips)

        self.flux = flux
        self.id = 0
        self.fragment_size = 1024

        self.ls_message = []
        self.init_messages()

    def init_messages(self):
        '''Mise en memoire des message a diffuser.'''

        self.ls_message = []

        for id, img in enumerate(self.flux.ls_image):
            header = str(id) + '\r\n' + str(len(img)) + '\r\n'
            size = min(512, self.fragment_size) - len(header) - len('\r\n\r\n' + str(self.fragment_size)) - 10
            nbr = int(math.ceil(len(img) / size))

            self.ls_message += [[]]
            for i in xrange(nbr + 1):
                fr = min(i * size, len(img))
                to = min((i + 1) * size, len(img))
                msg = header + str(fr) + '\r\n' + str(to - fr) + '\r\n' + img[fr : to]
                self.ls_message[-1] += [msg]

                self.add_message(self.sock, msg)

    def diffuse_msg(self):
        '''Diffusion du message courant et passage au suivant.'''

        if self.id >= 0 and self.id < len(self.ls_message):
            for msg in self.ls_message[self.id]:
                self.add_message(self.sock, msg)

        self.id = (self.id + 1) % len(self.ls_message)


class CatalogServer(Server.Server(Protocol.TCP)):
    '''Serveur HTTP envoyant la meme page a chaque connexion/requete.'''

    def __init__(self, port, page, keep_alive = 5):
        '''Initialisation du serveur.

        Parametre:
            port       -- port d'ecoute du serveur
            page       -- page a envoyer a chaque requete entrante
            keep_alive -- duree de vie d'un socket (5 en generale pour une connexion HTTP)
        '''

        super(CatalogServer, self).__init__(port, keep_alive)

        self.page = page

    def accept_client(self, client):
        '''Fonction d'acceptation du client.'''

        return True

    def __str__(self):
        return '[Catalog ' + str(self.port) + ']'

    def parse(self, sock, msg):
        if msg == '':
            self.add_message(sock, self.page)

def MyServer(_Protocol):
    '''Generateur d'une meta-class de serveur en fonction du parametre utilise.'''

    class _MyServer(Server.Server(_Protocol)):
        '''Serveur associant une action a faire pour une requete de la forme MOT ARG1 ARGS2 ...\r\n.'''

        def __init__(self, port, flux, keep_alive = -1):
            '''Initialisation du serveur et association des actions de bases.

            Parametre:
                port       -- port d'ecoute du serveur
                flux       -- flux a envoyer
                keep_alive -- temps max d'inactivite d'un socket
            '''

            super(_MyServer, self).__init__(port, keep_alive)

            self.flux = flux
            self.id = {}

            self.ls_action = {}

            self.ls_action['END'] = self._end
            self.ls_action['LISTEN_PORT'] = self._listen_port

            if _Protocol == Protocol.UDP:
                self.fragment_size = 1
                self.ls_action['FRAGMENT_SIZE'] = self._fragment_size

            self.ls_message = []
            self.init_messages()

        if _Protocol == Protocol.UDP:
            def _fragment_size(self, sock, size):
                '''Action associe au mot FRAGMENT_SIZE.

                Parametre:
                    sock -- socket ayant demande l'action
                    size -- argument du mot FRAGMENT_SIZE
                '''

                self.fragment_size = int(size)
                self.init_messages()

        def accept_client(self, client):
            '''Fonction d'acceptation des clients.

            Parametre:
                client -- socket de connexion au client
            '''

            return _Protocol == Protocol.TCP

        def init_messages(self):
            '''Mise en memoire des messages a envoyer a partir du flux.'''

            self.ls_message = []

            for id, img in enumerate(self.flux.ls_image):
                if _Protocol == Protocol.TCP:
                    self.ls_message += [[str(id) + '\r\n' + str(len(img)) + '\r\n' + img]]
                elif _Protocol == Protocol.UDP:
                    header = str(id) + '\r\n' + str(len(img)) + '\r\n'
                    size = min(512, self.fragment_size) - len(header) - len('\r\n\r\n' + str(self.fragment_size)) - 10
                    n = int(math.ceil(len(img) / size))

                    packet = []
                    for i in xrange(n + 1):
                        fr = min(i * size, len(img))
                        to = min((i + 1) * size, len(img))
                        packet += [header + str(fr) + '\r\n' + str(to - fr) + '\r\n' + img[fr : to]]
                    self.ls_message += [packet]
                else:
                    raise Exception('Not implemented')

        def get_packet(self, id):
            '''Renvoie la liste des paquets a envoyer pour le message numero id

            Parametre:
                id -- id du message
            '''

            if id >= 0 and id < len(self.ls_message):
                return self.ls_message[id]
            return []

        def parse(self, sock, msg):
            '''Decoupe le message en ligne et l'analyse. Si pour une ligne, le premier mot est une action valide, alors la fonction associe est appele avec les parametres transmis.

            Parametre:
                sock -- socket ayant envoyer le message
                msg  -- message envoye
            '''

            lines = [l.strip() for l in msg.split('\r\n') if l.strip()]
            for l in lines:
                words = [w.strip() for w in l.split(' ') if w.strip()]

                if len(words) > 0:
                    if words[0] in self.ls_action:
                        f = self.ls_action[words[0]]
                        args = tuple([sock] + words[1:])
                        f(*args)

        def _end(self, sock):
            '''Fonction de fin de la communication

            Parametre:
                sock -- client ayant demande la fin de la communication.
            '''

            self.disconnect(sock)

        def _listen_port(self, sock, port):
            '''Creation du canal de donne entre le serveur et le client

            Parametre:
                sock -- client
                port -- port ou le canal est connecte
            '''

            if not sock in self.link:
                s = _Protocol.Socket()
                s.connect(sock.addr(), int(port))
                self.link[sock] = s
                self.id[sock] = 0

    return _MyServer

def PullServer(_Protocol):
    '''Generateur de la meta-class PullServer'''

    class _PullServer(MyServer(_Protocol)):
        '''Specialisation du serveur de base ajoutant l'action GET.'''

        def __init__(self, port, flux):
            super(_PullServer, self).__init__(port, flux)

            self.ls_action['GET'] = self._get

        def __str__(self):
            return '[' + ('TCP ' if _Protocol == Protocol.TCP else ('UDP ' if _Protocol == Protocol.UDP else '')) + 'Pull Server ' + str(self.port) + ']'

        def _get(self, sock, id):
            '''Action GET envoyant le message demande au client.

            Parametre:
                sock -- client demandant le message
                id   -- id du message a envoyer
            '''

            id = int(id)
            if id == -1:
                if not sock in self.id:
                    id = 0
                    self.id[sock] = id
                else:
                    id = self.id[sock]

            if sock in self.link:
                for m in self.get_packet(id):
                    self.add_message(self.link[sock], m)

            self.id[sock] = (id + 1) % len(self.flux.ls_image)

    return _PullServer

def PushServer(_Protocol):
    '''Generateur de la meta-classe PushServer.'''

    class _PushServer(MyServer(_Protocol)):
        '''Specialisation du serveur de base ajoutant les actions START et PAUSE.'''

        def __init__(self, port, flux):
            super(_PushServer, self).__init__(port, flux, 60 if _Protocol == Protocol.UDP else -1)

            self.ls_action['START'] = self._start
            self.ls_action['PAUSE'] = self._pause

            self.started = set()

        def __str__(self):
            return '[' + ('TCP ' if _Protocol == Protocol.TCP else ('UDP ' if _Protocol == Protocol.UDP else '')) + 'Push Server ' + str(self.port) + ']'

        def disconnect(self, sock):
            if sock in self.started:
                self.started.remove(sock)

            super(_PushServer, self).disconnect(sock)

        def send_image(self, sock):
            '''Envoie d'une image tous les 1 / ips secondes

            Parametre:
                sock -- client a qui envoyer les images
            '''

            if sock in self.started:
                if not sock in self.id:
                    self.id[sock] = 0

                if sock in self.link:
                    s = self.link[sock]
                    for m in self.get_packet(self.id[sock]):
                        self.add_message(s, m)
                self.id[sock] = (self.id[sock] + 1) % len(self.flux.ls_image)

                t = threading.Timer(1.0 / self.flux.ips, self.send_image, args = (sock,))
                t.start()

        def stop(self):
            self.started = set()
            super(_PushServer, self).stop()

        def _start(self, sock):
            '''Debut de la transmission au client

            Parametre:
                sock -- client pour lequel la transmission a debute
            '''

            self.started.add(sock)
            t = threading.Timer(1.0 / self.flux.ips, self.send_image, args = (sock,))
            t.start()

        def _pause(self, sock):
            '''Mise en pause de la transmission

            Parametre:
                sock -- client pour lequel la transmission est mise en pause
            '''

            if sock in self.started:
                self.started.remove(sock)

    return _PushServer

'''Declinaison des serveurs en fonction du protocol.'''
TCPPushServer = PushServer(Protocol.TCP)
TCPPullServer = PullServer(Protocol.TCP)
UDPPushServer = PushServer(Protocol.UDP)
UDPPullServer = PullServer(Protocol.UDP)

