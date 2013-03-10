def cache(f):
    mem = {}

    def wrapper(*args):
        if args not in mem:
            mem[args] = f(*args)
        return mem[args]

    return wrapper

@cache
def read_image(path):
    '''Lecture d'une image a partir de son chemin.

    Parametre:
        path -- chemin de l'image
    '''

    path = path.replace('\\', '/')
    try:
        img = open(path, 'rb').read()
    except:
        print 'Error : Image not found at `' + path + '`'
        return ''

    return img

class flux:
    '''Classe symbolisant un flux par son id/nom/type/adresse/port/protocol/ips/images.'''

    def __init__(self, txt):
        '''Construction et lecture du flux'''

        self.id = 0
        self.name = ''
        self.type = ''
        self.addr = ''
        self.port = 0
        self.protocol = ''
        self.ips = 1.0
        self.ls_image = []
        self.ls_image_path = []

        for l in txt.split('\n'):
            l = l.strip().split(' ')

            if len(l) == 2:
                if l[0] == 'ID:':
                    self.id = int(l[1])

                if l[0] == 'Name:':
                    self.name = l[1]

                if l[0] == 'Type:':
                    self.type = l[1]

                if l[0] == 'Address:':
                    self.addr = l[1]

                if l[0] == 'Port:':
                    self.port = int(l[1])

                if l[0] == 'Protocol:':
                    self.protocol = l[1]

                if l[0] == 'IPS:':
                    self.ips = float(l[1])

            if len(l) == 1 and l[0]:
                self.ls_image += [read_image(l[0])]
                self.ls_image_path += [l[0]]

    def __str__(self):
        return 'Object ID=' + str(self.id) + ' name=' + self.name + ' type=' + self.type + ' address=' + self.addr + ' port=' + str(self.port) + ' protocol=' + self.protocol + ' ips=' + str(self.ips)

