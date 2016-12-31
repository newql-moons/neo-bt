import requests

from util import bencode
from util.parse import parse_peers


class HTTPTracker(object):
    def __init__(self, url):
        self.__url = url

    def announce(self, info_hash, peer_id, port, left, event, ip=0, uploaded=0, downloaded=0):
        params = {
            'info_hash': info_hash,
            'peer_id': peer_id,
            'ip': ip,
            'port': port,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': left,
            'event': event,
        }
        data = requests.get(self.__url, params=params, timeout=10).content
        data = bencode.loads(data)
        return parse_peers(data[b'peers'])

    @property
    def url(self):
        return self.__url
