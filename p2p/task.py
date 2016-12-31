import select

from p2p.file import SingleFile

from p2p.peer import get_peers
from torrent import Torrent


class BtTask(object):
    def __init__(self, torrent):
        self.__torrent = Torrent(torrent)
        self.__file = SingleFile(self.__torrent)
        bitfield = self.__file.bitfield
        self.__peers = get_peers(self.__torrent, self.__file)

    def start(self):
        self.loop()

    def loop(self):
        while not self.__file.is_finish():
            readable, writable, err = \
                select.select(self.__peers, self.__peers, [])
            for peer in readable:
                peer.read_handle()
            for peer in writable:
                peer.write_handle()
        print('下载完成！')
