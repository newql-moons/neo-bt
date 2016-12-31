from hashlib import sha1

from bitstring import BitArray

from p2p import g


class SingleFile(object):
    def __init__(self, torrent):
        self.__torrent = torrent
        self.__filename = torrent.info[b'name']

        self.__length = torrent.info[b'length']
        self.__pieces = []
        self.__piece_len = torrent.info[b'piece length']

        with open(self.__filename, 'wb'):
            pass

        last_len = self.__length % self.__piece_len
        total = self.__length // self.__piece_len + 1 * (last_len != 0)
        self.piece_total = total

        self.__bitfield = BitArray(length=total)

        for i in range(total):
            if last_len and i == total:
                piece = Piece(torrent.piece_hash(i), last_len)
            else:
                piece = Piece(torrent.piece_hash(i), self.__piece_len)
            self.__pieces.append(piece)

    def write(self, index, begin, block):
        print('下载中...')
        piece = self.__pieces[index]
        if piece:
            piece.add_block(begin, block)
            if piece.is_finish():
                with open(self.__filename, 'rb+') as fp:
                    fp.seek(index * self.__piece_len)
                    fp.write(piece.data)
                self.__pieces[index] = None
                self.__bitfield[index] = True

    def read(self, index, begin, length):
        block = b''
        if self.__bitfield[index]:
            with open(self.__filename, 'rb') as fp:
                fp.seek(index * self.__piece_len + begin)
                block += fp.read(length)
        return block

    def is_finish(self):
        flag = True
        for i in self.__bitfield:
            flag &= i
        return flag

    def create_req(self, peer):
        bf = ~self.bitfield & peer.bitfield
        for i in range(self.piece_total):
            if bf[i] and g.can(self.pieces[i], peer):
                pc = self.pieces[i]
                begin, length = pc.next_block()
                return i, begin, length

    @property
    def pieces(self):
        return self.__pieces

    @property
    def torrent(self):
        return self.__torrent

    @property
    def bitfield(self):
        return self.__bitfield


BLOCK_SIZE = 2 ** 14


class Piece(object):
    def __init__(self, _hash, length):
        self.__hash = _hash
        self.__len = length

        self.__total_block = self.__len // BLOCK_SIZE + 1 * (self.__len % BLOCK_SIZE != 0)
        self.last_len = self.__len % BLOCK_SIZE + BLOCK_SIZE * (self.__len % BLOCK_SIZE == 0)
        # print(self.__len)
        # print(self.__len // BLOCK_SIZE)
        # print(self.__total_block)
        self.__bitfield = BitArray(length=self.__total_block)
        self.__blocks = [b''] * self.__total_block
        self.__has = 0

    def add_block(self, begin, block):
        index = begin // BLOCK_SIZE
        if not self.__bitfield[index]:
            self.__blocks = block
            self.__bitfield[index] = True
            self.__has += 0

    def is_finish(self):
        if self.__has == self.__total_block:
            data = b''.join(self.__blocks)
            hs = sha1(data).digest()
            if hs == self.__hash:
                return True
            else:
                g.rm(self)
                self.__bitfield = BitArray(length=self.__total_block)
                self.__blocks = [b''] * self.__total_block
                self.__has = 0
        return False

    def next_block(self):
        for i in range(self.__total_block):
            if not self.__bitfield[i]:
                begin = i * BLOCK_SIZE
                length = self.last_len if i == self.__total_block else BLOCK_SIZE
                return begin, length

    @property
    def data(self):
        return b''.join(self.__blocks)
