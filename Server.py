import select
import threading
import Queue
import socket

import Socket
import debug

class BasicServer(threading.Thread):
    '''Classe de server basic multithread mais lineaire dans l'envoie et la reception des donnees.
    Le serveur reste non bloquant grace a une attente des entrees/sorties disponible.'''

    def __init__(self, keep_alive):
        '''Initialise le serveur.

        Parametre:
            keep_alive -- temps d'inactivite maximum pour un socket
        '''

        threading.Thread.__init__(self)

        self.inputs = []
        self.outputs = []
        self.link = {}
        self.message_queue = {}

        self.running = False

        self.always_alive = []
        self.keep_alive = keep_alive

    def start(self):
        '''Lance le serveur'''

        self.running = True
        threading.Thread.start(self)

    def stop(self):
        '''Stop le serveur et ferme toutes les connexions.'''

        self.running = False
        for sock in self.inputs + self.outputs:
            self.disconnect(sock)

        self.inputs = []
        self.outputs = []
        self.link = {}
        self.message_queue = {}

    def disconnect(self, sock):
        '''Ferme la connexion d'un socket et de tous les sockets lies a celui-ci.

        Parametre:
            sock -- socket a ferme
        '''

        if not sock.closed():
            debug.log(self, 'Disconnection of ' + str(sock), 1)

        sock.close()

        if sock in self.link:
            self.disconnect(self.link[sock])

            try:
                del self.link[sock]
            except KeyError:
                debug.wtf(self, 'Python fait toujours la meme merde.')
        if sock in self.inputs:
            self.inputs.remove(sock)
        if sock in self.outputs:
            self.outputs.remove(sock)
        if sock in self.message_queue:
            try:
                del self.message_queue[sock]
            except KeyError:
                debug.wtf(self, 'Go home Python ! You\'re drunk')

    def run(self):
        '''Fonction d'execution de serveur.'''

        while self.running:
            # suppression des sockets ferme ainsi que des socket inactifs
            for sock in self.inputs + self.outputs:
                if sock.closed():
                    self.disconnect(sock)
                elif not sock in self.always_alive:
                    if sock.time_alive() > self.keep_alive and self.keep_alive > 0:
                        self.disconnect(sock)

            # Obtention des sockets lisable/ecrivable
            try:
                readable, writable, exceptable = select.select(self.inputs, self.outputs, self.inputs, 0)
            except socket.error:
                    debug.wtf(self, 'Stop that shit dude')
            except:
                pass

            if self.running:
                for sock in readable:
                    self.read(sock)

            if self.running:
                for sock in writable:
                    self.write(sock)

            if self.running:
                for sock in exceptable:
                    self.exception(sock)

        self.stop()

    def read(self, sock):
        '''Operation de lecture du socket.

        Parametre:
            sock -- instance du socket a lire
        '''

        raise Exception('Not implemented')

    def write(self, sock):
        '''Operation d'ecriture sur le socket.
        Le mecanisme d'ecriture est gere par une Queue d'operation.

        Parametre:
            sock -- instance du socket a ecrire
        '''

        try:
            msg = self.message_queue[sock].get_nowait()
        except Queue.Empty:
            self.outputs.remove(sock)

            if sock in self.message_queue:
                try:
                    del self.message_queue[sock]
                except KeyError:
                    debug.wtf(self, 'GTFO Python !!!')
        except KeyError:
            if sock in self.outputs:
                self.outputs.remove(sock)
        else:
            try:
                sock.send(msg)
            except socket.error:
                debug.error(self, 'Error for sending to ' + str(sock))
                self.disconnect(sock)
            else:
                debug.log(self, 'Sending to ' + str(sock), 3)
                debug.log(self, 'To ' + str(sock) + '`' + msg + '`', 5)

    def exception(self, sock):
        '''Definie le socket donne en etat d'exception et le ferme.'''

        self.disconnect(sock)

    def add_message(self, sock, msg):
        '''Ajoute un message a la queue d'envoie associe au socket en parametre.

        Parametre:
            sock -- socket ou envoyer le message
            msg  -- message a rajouter a la queue d'envoie
        '''

        try:
            if not sock in self.message_queue:
                self.message_queue[sock] = Queue.Queue()

            try:
                self.message_queue[sock].put_nowait(msg)
            except KeyError:
                debug.wtf(self, 'Python fait encore de la merde')

            if not sock in self.outputs:
                self.outputs += [sock]
        except Queue.Full:
            pass

class MCASTServer(BasicServer):
    ''''''
    def __init__(self, grp_addr, port, dt):
        '''Initialise le serveur en connectant un socket MCAST sur le groupe de diffusion.

        Parametre:
            grp_addr -- adresse IPv4 sous forme de chaine de caractere de l'adresse de diffusion.
            port     -- port de l'adresse de diffusion.
            dt       -- delai entre chaque envoie de donnees.
        '''

        super(MCASTServer, self).__init__(-1)

        self.grp_addr = grp_addr
        self.port = port
        self.sock = Socket.MCASTSocket()
        self.sock.connect(self.grp_addr, self.port)

        self.outputs += [self.sock]

        self.dt = dt
        self.timer = threading.Timer(self.dt, self.diffuse)

    def __str__(self):
        return '[MCAST Server ' + self.grp_addr + ':' + str(self.port) + ']'

    def read(self, sock):
        pass

    def start(self):
        self.timer.start()
        super(MCASTServer, self).start()

    def diffuse(self):
        '''Diffuse le message'''
        if self.running:
            self.diffuse_msg()
            self.timer = threading.Timer(self.dt, self.diffuse)
            self.timer.start()

    def diffuse_msg(self):
        '''Methode de base a implemente pour l'envoi du message.
        Cette methode est appele tous les dt temps quand le serveur est en fonctionnement.'''

        raise Exception('Not implemented')

def Server(Protocol):
    '''Generateur de meta class template de serveur en fonction du protocol utilise.

    Parametre:
        Protocol -- protocole utilise par le serveur
    '''

    class _Server(BasicServer):
        '''Classe de serveur avec un listener pour gerer les nouvelles connexions et un systeme de socket en input et de socket en output.'''

        def __init__(self, port, keep_alive):
            '''Initialise le serveur et le connecte sur un port.

            Parametre:
                port       -- port d'ecoute du serveur
                keep_alive -- temps d'inactivite maximum pour un socket avant d'etre deconnecte
            '''

            super(_Server, self).__init__(keep_alive)

            self.port = port
            self.listener = Protocol.Listener()
            self.listener.listen(port)
            self.inputs += [self.listener]
            self.always_alive += [self.listener]

        def read(self, sock):
            if sock is self.listener:
                try:
                    client, data = self.listener.accept(1024)
                except socket.error:
                    debug.error(self, 'Error for accepting client')
                else:
                    if not client in self.inputs:
                        self.inputs += [client]
                        debug.log(self, 'Client connected : ' + str(client), 1)
                    if data:
                        debug.log(self, 'Getting data from ' + str(client), 2)
                        debug.log(self, 'From ' + str(client) + '`' + data + '`', 4)
                    self.maj_time(client)
                    self.parse(client, data)
            else:
                try:
                    msg = sock.recv(1024)
                except socket.error:
                    debug.error(self, 'Error for reading on ' + str(sock))
                    self.disconnect(sock)
                else:
                    debug.log(self, 'Getting data from ' + str(sock), 2)
                    debug.log(self, 'From ' + str(sock) + '`' + msg + '`', 4)

                    self.maj_time(sock)
                    self.parse(sock, msg)

        def maj_time(self, sock):
            '''Met a jour le temps d'activite d'un socket ainsi que tous ses sockets lies.'''

            sock.maj_time()
            if sock in self.link:
                try:
                    s = self.link[sock]
                except KeyError:
                    debug.wtf(self, 'WTF Python !!')
                else:
                    self.maj_time(s)

        def parse(self, sock, msg):
            '''Lit un message provenant du socket donne.

            Parametre:
                sock -- socket en provenance du message
                msg  -- message envoye par le socket
            '''

            raise Exception('Not implemented')

    return _Server

