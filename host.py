from peer import Peer

import requests
import logging


class Host(Peer):
    def __init__(self, host, port, search_list):
        super().__init__(host, port)
        self.search_list = search_list

    def start(self):
        self.__searchPeers()
        if len(self.peers) == 0:
            self.master = self
        self.__join_cluster()

    def __searchPeers(self):
        self.peers = []
        for peer in self.search_list:
            try:
                r = requests.get("http://"+peer.host+":"+str(peer.port)+"/")
            except requests.exceptions.ConnectionError:
                continue
            if r.status_code == 200 and r.text == "Netzwerkprogrammierung2020":
                self.peers.append(peer)
                logging.info("Found peer: {}".format(peer))

    def __join_cluster(self):
        for peer in self.peers:
            try:
                r = requests.post("http://"+peer.host+":"+str(peer.port)+"/new_node", json=self.to_dict())
            except requests.exceptions.ConnectionError:
                logging.error("{} did not answer request to be added to the cluster succesfully.".format(peer))
                raise SystemExit
            if r.status_code == 200:
                if r.text == "master":
                    logging.info("Found current master: {}".format(peer))
                    self.master = peer
            else:
                logging.error("{} did not answer request to be added to the cluster succesfully.".format(peer))
                raise SystemExit