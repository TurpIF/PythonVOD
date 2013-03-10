import socket
import time

class Socket:
    '''Classe socket de base'''

    def __init__(self, handle = None):
        '''Cree un socket a partir d'un socket deja existant ou a partir de rien.
        Rend le socket reutilissable par une application meme si il est en etat d'attente de fermeture.

        Parametre:
            handle -- Si non nulle, alors le socket est cree a partir de ce handler. Sinon le socket est cree a partir de rien.
        '''

        if handle:
            self._handle = handle
        else:
            self._handle = self._create_socket()

        self._handle.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._addr = ''
        self._port = 0
        self._time = time.time()
        self._close = False

    def _create_socket(self):
        '''Methode a implementer pour cree un socket ayant le protocol voulue.'''

        raise Exception('Not implemented')

    def __str__(self):
        '''Donne la representation du socket.

        Format -- [Socket %addr%:%port%]'''

        return '[Socket ' + self._addr + ':' + str(self._port) + ']'

    def addr(self):
        '''Retourne l'addresse du socket.'''

        return self._addr

    def port(self):
        '''retourne le port du socket.'''

        return self._port

    def fileno(self):
        '''Retourne le descripteur de fichier du socket.'''

        return self._handle.fileno()

    def time_alive(self):
        '''Retourne le temps depuis lequel le socket n'a pas ete utilise'''

        return time.time() - self._time

    def maj_time(self):
        '''Indique que le socket a ete utilise et met a jour le temps de derniere utilisation.'''

        self._time = time.time()

    def close(self):
        '''Ferme le socket et coupe toutes les transmissions en cours.'''

        try:
            self._handle.shutdown(socket.SHUT_RDWR)
            self._handle.close()
        except socket.error:
            pass
        self._close = True

    def closed(self):
        '''Indique si le socket est ouvert ou ferme'''

        return self._close

class SocketListener(Socket):
    '''Classe de base pour un listener socket.'''

    def __str__(self):
        '''Representation d'un listener.

        Format -- [Listener %port%]'
        '''

        return '[Listener ' + str(self._port) + ']'

    def listen(self, port):
        '''Methode a implementer pour faire ecouter le listener sur le port donne.

        Parametre:
            port -- Port a ecouter
        '''

        raise Exception('Not implemented')

    def accept(self, size = 0):
        '''Methode a implementer pour accepter une connexion sur le port d'ecoute.

        Parametre:
            size -- taille des donnees pouvant etre recu en meme temps que la connexion.

        Retour:
            Renvoie un 2-tuple contenant le socket de communication entre le client et le server et les donnees recu pendant l'acceptation.
        '''

        raise Exception('Not implemented')

class ConnectedSocket(Socket):
    '''Classe de base pour un socket connectable.'''

    def __str__(self):
        '''Representation d'un listener.

        Format:
            [Socket %addr%:%port%]
        '''

        return '[Socket ' + self._addr + ':' + str(self._port) + ']'

    def connect(self, addr, port):
        '''Connecte le socket a l'adresse specifie.

        Parametre:
            addr -- Adresse IPv4 sous forme de chaine de caractere
            port -- Port de connection
        '''

        raise Exception('Not implemented')

    def send(self, buffer):
        '''Envoi sur l'adresse connecte le buffer donne.

        Parametre:
            buffer -- Buffer a envoyer au client
        '''

        raise Exception('Not implemented')

    def recv(self, size):
        '''Recoie des donnees de la part du client connecte.

        Parametre:
            size -- Taille maximum des donnes recuperables
        '''

        raise Exception('Not implemented')

class MCASTSocket(ConnectedSocket):
    '''Classe utilisant le protocole MCAST UDP pour l'envoie des donnees.
    UDP n'est pas un protocol de communication avec une vrai connection mais la surcouche permet de 'connecter' le socket UDP.'''

    def _create_socket(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
        return sock

    def connect(self, addr, port):
        self._addr = addr
        self._port = port

    def send(self, buffer):
        try:
            self._handle.sendto(buffer, (self._addr, self._port))
        except socket.error:
            raise

    def recv(self, size):
        return ''

class TCPSocket(ConnectedSocket):
    '''Classe de socket de communication server - client utilisant le protocol TCP.'''

    def _create_socket(self):
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, addr, port):
        try:
            self._handle.connect((addr, port))
        except socket.error:
            raise
        else:
            self.maj_time()
            self._addr = addr
            self._port = port

    def send(self, buffer):
        try:
            self._handle.sendall(buffer)
        except socket.error:
            raise
        else:
            self.maj_time()

    def recv(self, size):
        try:
            msg = self._handle.recv(size)
        except socket.error:
            raise
        else:
            self.maj_time()
            return msg

class TCPListener(SocketListener):
    '''Classe de socket d'ecoute utilisant le protocol TCP.'''

    def _create_socket(self):
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def listen(self, port):
        try:
            self._handle.bind(('', port))
            self._handle.listen(5)
        except socket.error:
            raise
        else:
            self._port = port
            self.maj_time()

    def accept(self, size = 0):
        try:
            sd, s_addr = self._handle.accept()
            sock = TCPSocket(sd)
            sock._addr = s_addr[0]
            sock._port = s_addr[1]
        except socket.error:
            raise
        else:
            self.maj_time()
            return sock, ''

class UDPSocket(ConnectedSocket):
    '''Classe de socket de communication server - client utilisant le protocol UDP.
    Le protocol UDP ne permet pas une veritable connection mais la surcouche permet de rendre cela transparent.'''

    def _create_socket(self):
        return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def connect(self, addr, port):
        self._addr = addr
        self._port = port

    def send(self, buffer):
        try:
            self._handle.sendto(buffer, (self._addr, self._port))
        except socket.error:
            raise

    def recv(self, size):
        try:
            msg, s_addr = self._handle.recvfrom(size)
        except socket.error:
            raise
        else:
            self.maj_time()
            return msg

class UDPListener(SocketListener):
    '''Classe de socket d'ecoute utilisant le protocol UDP.'''

    ls_connexion = {}

    def _create_socket(self):
        return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def listen(self, port):
        try:
            self._handle.bind(('', port))
        except socket.error:
            raise
        else:
            self.maj_time()
            self._port = port

    def accept(self, size = 0):
        try:
            data, s_addr = self._handle.recvfrom(size)
        except socket.error:
            raise
        else:
            self.maj_time()

            if s_addr in UDPListener.ls_connexion and not UDPListener.ls_connexion[s_addr].closed():
                return UDPListener.ls_connexion[s_addr], data

            sock = UDPSocket()
            sock.connect(s_addr[0], s_addr[1])
            #sock._handle.bind(('', self._port))
            UDPListener.ls_connexion[s_addr] = sock
            return sock, data

