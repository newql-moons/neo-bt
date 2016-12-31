from util import bencode
from hashlib import sha1


class Torrent(object):
    def __init__(self, path):
        with open(path, 'rb') as fp:
            s = fp.read()
        self.__meta = bencode.loads(s)

    def info_hash(self, hex_str=False):
        info = self.__meta[b'info']
        h = sha1(bencode.dumps(info))
        if hex_str:
            return h.hexdigest()
        else:
            return h.digest()

    def piece_hash(self, index):
        return self.info[b'pieces'][index * 20: index * 20 + 20]

    @property
    def meta(self):
        return self.__meta

    @property
    def info(self):
        return self.meta[b'info']

    @property
    def trackers(self):
        trackers = set()
        try:
            trackers.add(self.meta[b'announce'])
        except:
            pass
        try:
            for tracker in self.meta[b'announce-list']:
                trackers.add(tracker[0])
        except:
            pass
        return trackers
