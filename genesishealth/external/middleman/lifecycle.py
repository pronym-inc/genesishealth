import os, sys


def die(s):
    os.write(2, 'fatal: %s\n' % s.strip())
    sys.exit(1)

