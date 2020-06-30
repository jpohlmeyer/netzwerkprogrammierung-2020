import time
import requests
import logging
import subprocess
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
    masterscript : str
        Name of the masterscript that will be executed by the master on change.
    slavescript : str
        Name of the slavescript that will be executed by the slaves on change.

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
    update_master()
        Updates the current master peer.
    add_peer()
        Append a new peer to the list of peers.
    """

    def __init__(self, host, port, search_list, masterscript, slavescript):
        super().__init__(host, port)
        self.search_list = search_list
        self.masterscript = masterscript
        self.slavescript = slavescript
        self.master = None
        self.peers = None

    def start(self):
        """
        Host scans the possible peers for valid answers, and requests to join the cluster.
        It also determines the master peer and executes the script accordingly.
        :return:
        """
        self.__searchPeers()
        if len(self.peers) == 0:
            self.master = self
        self.__join_cluster()
        self.__execute_script()

    def add_peer(self, peer):
        """
        Append new peer to list of peers.
        :param peer: peer to add to list
        :return:
        """
        self.peers.append(peer)

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
                        if len(self.peers) != 0:
                            sorted_peers = sorted(self.peers, reverse=True, key=lambda p: p.id)
                            if self.id > sorted_peers[0].id:
                                logging.info("starting vote".format(peer))
                                self.start_vote()
                            else:
                                logging.info("waiting to vote".format(peer))
                        else:
                            logging.info("I am alone, and therefore the new master.")
                            self.master = self
                            return
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
        all_peers = self.peers.copy()
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
            new_master = None
            for p in self.peers:
                if p.id == sorted_votes[0]:
                    new_master = p
            if new_master is None:
                if self.id == sorted_votes[0]:
                    new_master = self
                else:
                    logging.error("Could not determine new master.")
                    return
            logging.info("new master is {}".format(new_master))
            self.update_master(new_master)
            for peer in self.peers:
                try:
                    r = requests.post("http://" + peer.host + ":" + str(peer.port) + "/new_master",
                                      json=new_master.to_dict())
                    if r.status_code != 200:
                        raise requests.exceptions.ConnectionError
                except requests.exceptions.ConnectionError:
                    logging.error("{} did not answer request update master successfully.".format(peer))
        else:
            self.__cast_vote(votes_dict)

    def update_master(self, peer):
        """
        Finds the peer object that corresponds to the given peer object and set it as master.
        :param peer: new master
        :return:
        """
        if self.id == peer.id:
            self.master = self
        else:
            for p in self.peers:
                if p.id == peer.id:
                    self.master = peer
        self.__execute_script()

    def __execute_script(self):
        if self.master.id == self.id:
            subprocess.Popen("./"+self.masterscript)
        else:
            subprocess.Popen("./"+self.slavescript)

    def __cast_vote(self, votes_dict):
        all_peers = self.peers.copy()
        all_peers.append(Peer(self.host, self.port))
        all_peers = sorted(all_peers, reverse=True, key=lambda p: p.id)
        next_peer = all_peers[0]
        for i in range(1,len(all_peers)):
            if all_peers[i].id < self.id:
                next_peer = all_peers[i]
                break
        votes_dict[all_peers[0].id] = votes_dict[all_peers[0].id] + 1
        logging.info("sending vote to {}".format(next_peer))
        try:
            r = requests.post("http://"+next_peer.host+":"+str(next_peer.port)+"/vote", json=votes_dict)
            if r.status_code != 200:
                raise requests.exceptions.ConnectionError
        except requests.exceptions.ConnectionError:
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
