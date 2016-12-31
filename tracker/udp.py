import struct
import socket
import random

from util.parse import parse_peers


class UDPTracker(object):
    event = {
        'none': 0,
        'completed': 1,
        'started': 2,
        'stopped': 3,
    }

    action = {
        'connect': 0,
        'announce': 1,
    }

    def __init__(self, host, port):
        self.__host = host
        self.__port = port
        self.connection_id = None

    def request(self, connection_id, action, data):
        transaction_id = random.getrandbits(32)

        package = struct.pack('!QII', connection_id, action, transaction_id)
        package += data

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(10)
        sock.sendto(package, (self.__host, self.__port,))
        readable = sock.makefile('rb')

        act, tran_id = struct.unpack('!II', readable.read(8))
        if act != action:
            raise Exception('The action is not equal to the one you chose.')
        if tran_id != transaction_id:
            raise Exception('The transaction ID is not equal to the one you chose.')
        sock.close()

        return readable

    def connect(self):
        resp = self.request(0x41727101980, self.action['connect'], b'')
        self.connection_id = struct.unpack('!Q', resp.read(8))[0]
        resp.close()

    def announce(self, info_hash, peer_id, port, left, event, ip=0, uploaded=0, downloaded=0, num_want=-1):
        if self.connection_id is None:
            self.connect()

        key = random.getrandbits(32)
        package = info_hash + peer_id
        package += struct.pack('!QQQ', downloaded, left, uploaded)
        package += struct.pack('!IIIi', self.event[event], ip, key, num_want)
        package += struct.pack('!H', port)

        resp = self.request(self.connection_id, self.action['announce'], package)

        interval, leechers, seeders = struct.unpack('!III', resp.read(12))
        peer_num = leechers + seeders
        data = resp.read(peer_num * 6)

        resp.close()

        return parse_peers(data)
