import time
import requests
import logging
from peer import Peer


class Host(Peer):
    """
    Host class is sending the HTTP requests to the other services, to determine if they are alive,
    or to vote for a new master. It knows the peer services and the current master.

    ...

    Attributes
    ----------
    search_list : [Peer]
        List of possible peers
    peers : [Peer]
        List of currently active peers
    master : Peer
        Current master

    Methods
    -------
    start()
        Starts the host. It will search for peers and request to join the cluster.
    request_heartbeats()
        Send a heartbeat request to all current peers.
    start_vote()
        Initiating the voting process after the master died.
    vote()
        Casting a vote for a new master on request of another service and forward to the next peer.
    """

    def __init__(self, host, port, search_list):
        super().__init__(host, port)
        self.search_list = search_list
        self.master = None

    def start(self):
        """
        Host scans the possible peers for valid answers, and requests to join the cluster.
        It also determines the master peer.
        :return:
        """
        self.__searchPeers()
        if len(self.peers) == 0:
            self.master = self
        self.__join_cluster()

    def request_heartbeats(self):
        """
        Send a heartbeart request to all current peers.
        Two consecutive missed heartbeats result in death.
        :return:
        """
        for peer in self.peers:
            try:
                r = requests.get("http://"+peer.host+":"+str(peer.port)+"/heartbeat")
            except requests.exceptions.ConnectionError:
                if peer.active:
                    peer.active = False
                    logging.info("{} missed first heartbeat.".format(peer))
                else:
                    logging.warning("{} missed second heartbeat and is determined dead.".format(peer))
                    self.peers.remove(peer)
                    if peer.id == self.master.id:
                        logging.warning("master is dead".format(peer))
                        sorted_peers = sorted(self.peers, reverse=True, key=lambda p: p.id)
                        if self.id > sorted_peers[0].id:
                            logging.info("starting vote".format(peer))
                            self.start_vote()
                        else:
                            logging.info("waiting to vote".format(peer))
                continue
            if r.status_code == 200 and r.text == "pong":
                peer.active = True

    def start_vote(self):
        """
        Will sleep for 2 seconds to allow for all other services to determine the old master dead.
        Then it will trigger the voting process by initializing the vote list, giving its vote
        and send the voting request to the next service.
        :return:
        """
        time.sleep(2)  # to make sure every service knows the master is dead
        all_peers = self.peers
        all_peers.append(Peer(self.host, self.port))
        voting_message = {p.id: 0 for p in all_peers}
        voting_message["starter"] = self.id
        self.__cast_vote(voting_message)

    def vote(self, votes_dict):
        """
        Will vote on request of another service
        and forward the new vote count to the next peer.
        :param votes_dict: current vote count
        :return:
        """
        if votes_dict["starter"] == self.id:
            del(votes_dict["starter"])
            sorted_votes = [k for k, v in sorted(votes_dict.items(), reverse=True, key=lambda item: item[1])]
            logging.info("new master is {}".format(sorted_votes[0]))
            # TODO send master update
        else:
            self.__cast_vote(votes_dict)

    def __cast_vote(self, votes_dict):
        all_peers = self.peers
        all_peers.append(Peer(self.host, self.port))
        all_peers = sorted(all_peers, reverse=True, key=lambda p: p.id)
        next_peer = all_peers[0]
        for i in range(1,len(all_peers)):
            if all_peers[i].id < self.id:
                next_peer = all_peers[i]
                break
        votes_dict[all_peers[0].id] = votes_dict[all_peers[0].id] + 1
        logging.info("sending vote to {}".format(next_peer))
        r = requests.post("http://"+next_peer.host+":"+str(next_peer.port)+"/vote", json=votes_dict)
        if r.status_code != 200:
            logging.error("{} did not accept voting message".format(next_peer))

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
