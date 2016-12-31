from p2p.task import BtTask


def main():
    task = BtTask('8b131f9569314d4a23eccd97dad8032e6bb5379e.torrent')
    task.start()


if __name__ == '__main__':
    main()
