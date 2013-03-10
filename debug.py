'''Module de log ecrivant soit sur le canal de sortie standard soit sur le canal de sortie d'erreur en fonction du niveau de verbosite du programme.'''

import sys

verbose = 0

def log(sender, message, verbose_level = 1):
    if verbose_level <= verbose:
        sys.stdout.write(str( sender) + ' : ' + message + '\r\n')
        sys.stdout.flush()

def error(sender, message):
    sys.stderr.write(str(sender) + ' : ' + message + '\r\n')
    sys.stderr.flush()

def wtf(sender, message):
    sys.stdout.write(str(sender) + ' : ' + message + '\r\n')
    sys.stdout.flush()

