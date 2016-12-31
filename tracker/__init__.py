from .http import HTTPTracker
from .udp import UDPTracker

from urllib.parse import urlsplit

NONE_EVENT = 'none'
COMPLETED_EVENT = 'completed'
STARTED_EVENT = 'started'
STOPPED_EVENT = 'stopped'


def tracker(url):
    o = urlsplit(url)
    if o.scheme == b'udp' or o.scheme == 'udp':
        return UDPTracker(o.hostname, o.port)
    elif o.scheme == b'http' or o.scheme == 'http':
        return HTTPTracker(url)
