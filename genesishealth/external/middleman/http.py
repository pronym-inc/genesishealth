from urllib.error import HTTPError
from urllib.parse import urlencode as urlencode_
from urllib.request import urlopen


def urlencode(data):
    return urlencode_(data)


def lowerkeys(d):
    d2 = {}
    for k, v in d.items():
        d2[str(k).lower()] = v
    return d2


def http(url, data=None):
    data = urlencode(lowerkeys(data))
    try:
        req = urlopen(url, data)
    except HTTPError as e:
        return str(e)
    try:
        encoding = req.headers['content-type'].split('charset=')[-1]
    except KeyError:
        encoding = 'utf-8'
    return req.read().decode(encoding)

