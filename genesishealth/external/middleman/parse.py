import io, subprocess, sys


def decrypt(data, key):
    po = subprocess.Popen(
        ['/webapps/genesishealth/bin/decrypt', data, key],
        stdout=subprocess.PIPE
    )
    res = po.communicate()
    return po.returncode, res[0]


def parse(inp):
    d = dict()
    lines = inp.split('/')
    for l in lines:
        k, data = l.split('=')
        data = ''.join(data.strip().split(' '))
        d[k] = data
    return d


def ords(bs):
    return ' '.join(map(lambda x: str(hex(ord(x))), bs))


def debug(parsed):
    s = io.StringIO()
    for k, data in parsed.items():
        s.write('%s %-11s len:%2d %s \n' % (data['raw'], k, len(data['plain']),
                                            ords(data['plain'])))
    return s.getvalue()


def parse_and_decrypt(inp, key):
    d = dict()
    for k, data in parse(inp).items():
        code, value = decrypt(data, key)
        d[k] = {'raw': data, 'plain': value}
        if code > 0:
            return False
    return d


def verified(inp, key):
    if parse_and_decrypt(inp, key):
        return True


if __name__  == '__main__':
    print(parse_and_decrypt(sys.stdin.read(), sys.argv[1]))

