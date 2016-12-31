import threadpool
import tracker
import socket
import queue
import struct
import time

from cfg import *
from bitstring import BitArray
from . import g
from util import parse


class Peer(object):
    def __init__(self, sock, file):
        self.sock = sock
        self.file = file

        self.__bitfield = None
        self.__am_chocking = True  # 本机是否阻塞peer
        self.__am_interested = False  # 本机是否对peer感兴趣
        self.peer_chocking = True  # peer是否阻塞本机
        self.peer_interested = False  # peer是否对本机感兴趣

        self.send_buf = queue.Queue()
        self.send_buf.put(self.handshake)
        self.send_buf.put(self.pack_msg(msg_id=5, bitfield=self.file.bitfield.tobytes()))

        self.has_hs = False

    def read_handle(self):
        if not self.has_hs:
            try:
                pstrlen = struct.unpack('!B', self.sock.recv(1))[0]
                if pstrlen != 19:
                    return
                pstr = self.sock.recv(19)
                if pstr != b'BitTorrent protocol':
                    return
                reserved = self.sock.recv(8)
                info_hash = self.sock.recv(20)
                if info_hash != self.file.torrent.info_hash():
                    return
                peer_id = self.sock.recv(20)
                self.has_hs = True
                print('%s 握手成功！' % self.addr)
            except:
                return
        else:
            length = struct.unpack('!I', self.sock.recv(4))[0]
            if length == 0:  # keep-alive
                return
            msg_id = struct.unpack('!B', self.sock.recv(1))[0]
            msg = self.sock.recv(length - 1)
            while len(msg) != length - 1:
                try:
                    msg += self.sock.recv(1)
                except socket.timeout:
                    pass
            print('Recv msg(%d) from %s' % (msg_id, self.addr))
            if msg_id == 0:  # choke
                self.peer_chocking = True
            elif msg_id == 1:  # unchoke
                self.peer_chocking = False
            elif msg_id == 2:  # interested
                self.peer_interested = True
            elif msg_id == 3:  # not interested
                self.peer_interested = False
            elif msg_id == 4:  # have
                index = struct.unpack('!I', msg)[0]
                self.bitfield[index] = True
            elif msg_id == 5:  # bitfield
                self.bitfield = BitArray(bytes=msg)[:len(self.file.bitfield)]
            elif msg_id == 6:  # request
                index, begin, length = struct.unpack('!III', msg)
                if not self.am_chocking:
                    self.send_buf.put(self.pack_msg(
                        msg_id=msg_id,
                        index=index,
                        begin=begin,
                        length=length,
                    ))
            elif msg_id == 7:  # piece
                index, begin = struct.unpack('!II', msg[:8])
                block = msg[8:]
                if g.can(self.file.pieces[index], self):
                    self.file.write(index, begin, block)
                g.rm_r(self, index, begin)
            elif msg_id == 8:  # cancel
                pass
            elif msg_id == 9:  # port
                pass

    def write_handle(self):
        try:
            msg = self.send_buf.get_nowait()
            self.sock.send(msg)
            parse.parse_req(msg, self.addr)
        except queue.Empty:
            if self.am_interested and not self.peer_chocking:
                try:
                    index, begin, length = self.file.create_req(self)
                    if g.can_r(self, index, begin):
                        msg = self.pack_msg(
                            msg_id=6,
                            index=index,
                            begin=begin,
                            length=length,
                        )
                        self.sock.send(msg)
                        parse.parse_req(msg, self.addr)
                except:
                    pass

    def pack_msg(self, msg_id, **kwargs):
        if 0 <= msg_id <= 9:
            _id = struct.pack('!B', msg_id)

        if msg_id == 0:  # choke
            content = b''
        elif msg_id == 1:  # unchoke
            content = b''
        elif msg_id == 2:  # interested
            content = b''
        elif msg_id == 3:  # not interested
            content = b''
        elif msg_id == 4:  # have
            index = kwargs['index']
            content = struct.pack('!I', index)
        elif msg_id == 5:  # bitfield
            bitfield = kwargs['bitfield']
            content = bitfield
        elif msg_id == 6:  # request
            index = kwargs['index']
            begin = kwargs['begin']
            length = kwargs['length']
            content = struct.pack('!III', index, begin, length)
        elif msg_id == 7:  # piece
            index = kwargs['index']
            begin = kwargs['begin']
            length = kwargs['length']
            block = self.file.read(index, begin, length)
            content = struct.pack('!II', index, begin)
            content += block
        elif msg_id == 8:  # cancel
            pass
        elif msg_id == 9:  # port
            pass
        msg = struct.pack('!I', len(content) + 1)
        msg += _id
        msg += content
        return msg

    def fileno(self):
        return self.sock.fileno()

    def have(self, index):
        self.bitfield[index] = True
        self.check_interest()

    def check_interest(self):
        self.am_interested = bool(~self.file.bitfield & self.bitfield)

    @property
    def handshake(self):
        pstrlen = struct.pack('!B', 19)
        pstr = b'BitTorrent protocol'
        reserved = b'\x00\x00\x00\x00\x00\x00\x00\x00'
        info_hash = self.file.torrent.info_hash()
        peer_id = PEER_ID
        return pstrlen + pstr + reserved + info_hash + peer_id

    @property
    def am_chocking(self):
        return self.__am_chocking

    @am_chocking.setter
    def am_chocking(self, flag):
        self.send_buf.put(self.pack_msg(msg_id=int(not flag)))
        self.__am_chocking = flag

    @property
    def am_interested(self):
        return self.__am_interested

    @am_interested.setter
    def am_interested(self, flag):
        self.send_buf.put(self.pack_msg(msg_id=int(not flag) + 2))
        self.__am_interested = flag

    @property
    def bitfield(self):
        return self.__bitfield

    @bitfield.setter
    def bitfield(self, bit_array):
        self.__bitfield = bit_array
        self.check_interest()

    @property
    def addr(self):
        return '%s:%s' % self.sock.getpeername()


class MsgBuff(object):
    def __init__(self):
        self.__data = b''
        self.hs = False

    def extend(self, s):
        temp = []
        for x in s:
            temp.append(x)
        self.__data += bytes(temp)

    def get(self):
        if not self.hs and len(self.__data) == 68:
            self.hs = True
            self.__data = b''
            print('握手成功！')
        elif len(self.__data) >= 4:
            content = self.__data[4:]
            length = struct.unpack('!I', self.__data[:4])[0]
            if len(content) == length:
                msg_id = struct.unpack('!B', content[:1])
                msg = content[1:]
                return msg_id, msg
        return None


def get_peers(torrent, file):
    temp = []
    peers = []
    address = None

    def announce(link):
        tra = tracker.tracker(link)
        try:
            left = torrent.info[b'length']
        except:
            left = 0
            for f in torrent.info[b'files']:
                left += f[b'length']
        prs = tra.announce(
            torrent.info_hash(),
            PEER_ID,
            PORT,
            left,
            tracker.STARTED_EVENT,
        )
        temp.extend(prs)
        print('从%s获取到%d个peer' % (link, len(prs)))
        nonlocal address
        address = set(temp)

    def conn2peer(addr):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        try:
            sock.connect(addr)
            peers.append(Peer(sock, file))
            print('连接到peer %s:%s' % addr)
        except Exception as e:
            raise e

    pool = threadpool.ThreadPool(5)
    for url in torrent.trackers:
        pool.add_task(announce, url)
    pool.destroy()
    # pool.show_errors()

    pool = threadpool.ThreadPool(5)
    for item in address:
        print('准备连接 %s:%s' % item)
        pool.add_task(conn2peer, item)
    pool.destroy()
    # pool.show_errors()

    return peers
