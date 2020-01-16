#!/usr/bin/python3

def dev2nguid(dev):
    _l = list(map(lambda x: x.rjust(2, '0'),
            list(map(lambda x: x.split('x')[-1],
            list(map(hex, list(map(ord, dev))))))))
    _l.extend(['ff' for _ in range(16)])
    return ''.join(_l[:4])+'-'+''.join(_l[4:6])\
            +'-'+''.join(_l[6:8])+'-'+''.join(_l[8:10])\
            +'-'+''.join(_l[10:16])


def nguid2dev(guid):
    _s = guid.replace('-', '')
    _l = [_s[i:i+2] for i in range(0, len(_s), 2)]
    return ''.join(list(map(chr, \
            list(map(lambda x: int(x, 16), \
            list(filter(lambda x: x!='ff', _l)) )) )) )

