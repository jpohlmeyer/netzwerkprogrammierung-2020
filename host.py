from peer import Peer

import requests
import logging


class Host(Peer):
    def __init__(self, host, port, searchList):
        super().__init__(host, port)
        self.peers = Host.searchPeers(searchList)

    @staticmethod
    def searchPeers(searchList):
        peers = []
        for peer in searchList:
            try:
                r = requests.get("http://"+peer.host+":"+str(peer.port)+"/")
            except requests.exceptions.ConnectionError:
                continue
            if r.status_code == 200 and r.text == "Netzwerkprogrammierung2020":
                peers.append(peer)
                logging.info("Found peer: {}".format(peer))
        return peers

