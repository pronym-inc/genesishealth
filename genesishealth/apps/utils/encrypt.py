import subprocess

from django.conf import settings


def _crypt(data, cmd):
    po = subprocess.Popen([cmd, str(data), settings.AES_KEY], stdout=subprocess.PIPE)
    res = po.communicate()
    return res[0]


def decrypt(data):
    return _crypt(data, 'decrypt')


def encrypt(data):
    return _crypt(data, 'encrypt')
