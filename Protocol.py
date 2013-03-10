'''Module permettant la connexion a une application et l'ecoute sur un port via l'utilisation de sockets.'''

import Socket

class Protocol:
    '''Contient les elements necessaire a la construction d'un server et d'un client dans un protocol donne.

    Listener  -- Permet d'ecouter un port donne.
    Socket    -- Cree une connexion bidirectionnel entre deux processus.
    '''

    Listener = None
    Socket = None

class TCP(Protocol):
    '''Contient les elements necessaire pour une communication utilisant le protocol TCP'''

    Listener = Socket.TCPListener
    Socket = Socket.TCPSocket

class UDP(Protocol):
    '''Contient les elements necessaire pour une communication utilisant le protocol UDP'''

    Listener = Socket.UDPListener
    Socket = Socket.UDPSocket


