import socket
import struct
import struct


def parse_peers(data):
    peers = []
    for i in range(len(data) // 6):
        block = data[i * 6: i * 6 + 6]
        peer = (socket.inet_ntoa(block[:4])
                , struct.unpack('!H', block[4:])[0],)
        peers.append(peer)
    return peers


def parse_req(msg, addr):
    if msg[:20] == b'\x13BitTorrent protocol':
        print('Send handshake to %s' % addr)
        return
    length = struct.unpack('!I', msg[:4])[0]
    if length == 0:
        print('Send keep-alive to %s' % addr)
        return 0
    msg_id = msg[4]
    if msg_id == 0:
        print('Send choke to %s' % addr)
    elif msg_id == 1:
        print('Send unchoke to %s' % addr)
    elif msg_id == 2:
        print('Send interest to %s' % addr)
    elif msg_id == 3:
        print('Send not interest to %s' % addr)
    elif msg_id == 4:
        index = struct.unpack('!I', msg[5:])[0]
        print('Send have(%d) to %s' % (index, addr))
    elif msg_id == 5:
        print('Send bitfield to %s' % addr)
    elif msg_id == 6:
        index, begin, length = struct.unpack('!III', msg[5:])
        print('Send req(%d, %d, %d) to %s' % (index, begin, length, addr))
    elif msg_id == 7:
        print('Send data to %s' % addr)
    elif msg_id == 8:
        pass
    elif msg_id == 9:
        pass
