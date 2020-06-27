from peer import Peer


class Host(Peer):
    def __init__(self, host, port, searchList):
        super().__init__(host, port)
        self.searchList = searchList
        # TODO search List for peers