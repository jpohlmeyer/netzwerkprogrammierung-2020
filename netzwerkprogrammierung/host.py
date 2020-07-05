"""
In this module the Host class is defined.
"""

import requests
import logging
import subprocess
import threading
from netzwerkprogrammierung.errors import JoiningClusterError, VotingError
from netzwerkprogrammierung.peer import Peer


class Host(Peer):
    """
    Communicating with other services via HTTP requests.

    Host class is sending the HTTP requests to the other services, to determine if they are alive,
    requesting to be added to the cluster or to vote for and announcing a new master.
    It knows the peer services and the current master.

    Attributes:
        search_list: type [Peer], List of possible peers
        peers: [Peer], List of currently active peers
        master: Peer, Current master
        masterscript: str, Name of the masterscript that will be executed by the master on change.
        slavescript: str,  Name of the slavescript that will be executed by the slaves on change.
        lock: threading.Lock, Lock that will used so make sure threads are not inferring with each other
    """

    def __init__(self, host, port, search_list, masterscript, slavescript):
        """
        Init Host.

        Args:
            host: hostname or ip of the host service
            port: port of the host service
            search_list: List of possible peers for autodetection
            masterscript: Name of the masterscript that will be executed by the master on change.
            slavescript: Name of the slavescript that will be executed by the slaves on change.
        """
        super().__init__(host, port)
        self.search_list = search_list
        self.masterscript = masterscript
        self.slavescript = slavescript
        self.lock = threading.RLock()
        self.master = None
        self.peers = []

    def start(self):
        """
        Start the host, adding it to the cluster.

        Host scans the possible peers for valid answers, and requests to join the cluster.
        It also determines the master peer and executes the script accordingly.
        """
        self.__search_peers()
        if len(self.peers) == 0:
            self.master = self
        self.__join_cluster()
        self.__execute_script()

    def add_peer(self, peer):
        """
        Append new peer to list of peers.

        Args:
            peer: peer to add to list
        """
        with self.lock:
            for p in self.peers:
                if peer.id == p.id:
                    # Make sure there are no duplicates
                    return False
            self.peers.append(peer)
        return True

    def request_heartbeats(self):
        """
        Send a heartbeart request to all current peers.

        Two consecutive missed heartbeats result in death, peer is then removed from cluster.
        If the dead peer is the master a vote is triggered by the peer with the highest ID.
        """
        with self.lock:
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
                        if self.master is not None and peer.id == self.master.id:
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
                                self.update_master(self)
                                return
                    continue
                if r.status_code == 200 and r.text == "pong":
                    peer.active = True

    def start_vote(self):
        """
        Trigger the voting process.

        Will trigger the voting process by initializing the vote list, giving its vote
        and send the voting request to the next service.
        """
        with self.lock:
            all_peers = self.peers.copy()
        all_peers.append(Peer(self.host, self.port))
        voting_message = {p.id: 0 for p in all_peers}
        voting_message["starter"] = self.id
        voting_message["old_master"] = self.master.id
        self.__cast_vote(voting_message)

    def vote(self, votes_dict):
        """
        Vote when receiving a vote request.

        Will vote on request of another service
        and forward the new vote count to the next peer.
        If the host is the starter of the vote and
        received the final voting message back it will determine the new master.

        Args:
            votes_dict: current vote count (id: int), starter id and old_master id in a dict
        """
        if votes_dict["starter"] == self.id:
            # this node is starter and can announce the new master
            del(votes_dict["starter"])
            del(votes_dict["old_master"])
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

        Args:
            peer: new master
        """
        if self.id == peer.id:
            self.master = self
        else:
            for p in self.peers:
                if p.id == peer.id:
                    self.master = peer
        self.__execute_script()

    def __execute_script(self):
        """
        Execute the corresponding script for master or slave hosts.

        The script will be executed asynchronously.
        """
        if self.master.id == self.id:
            logging.info("Executing master script:")
            subprocess.Popen("./"+self.masterscript)
        else:
            logging.info("Executing slave script:")
            subprocess.Popen("./"+self.slavescript)

    def __cast_vote(self, votes_dict):
        """
        Vote for a new master.

        Remove the old master from the list of peers and vote for a new master.
        Send the voting message to the next peer.

        Args:
            votes_dict: current vote count
        """
        self.master = None
        with self.lock:
            for peer in self.peers:
                if peer.id == votes_dict["old_master"]:
                    self.peers.remove(peer)
                if peer.id == votes_dict["starter"]:
                    starter = peer
            all_peers = self.peers.copy()
        all_peers.append(Peer(self.host, self.port))
        all_peers = sorted(all_peers, reverse=True, key=lambda p: p.id)
        next_peer = all_peers[0]
        for i in range(1, len(all_peers)):
            if all_peers[i].id < self.id:
                next_peer = all_peers[i]
                break
        votes_dict[all_peers[0].id] = votes_dict[all_peers[0].id] + 1
        logging.info("sending vote to {}".format(next_peer))
        try:
            r = requests.post("http://"+next_peer.host+":"+str(next_peer.port)+"/vote", json=votes_dict)
            if r.status_code != 200:
                raise VotingError
            voted = True
        except (VotingError, requests.exceptions.ConnectionError):
            logging.error("{} did not accept voting message. Sending vote back to starter.".format(next_peer))
            voted = False
        if not voted and starter is not None:
            try:
                r = requests.post("http://"+starter.host+":"+str(starter.port)+"/vote", json=votes_dict)
                if r.status_code != 200:
                    raise VotingError
            except (VotingError, requests.exceptions.ConnectionError):
                logging.error("Vote starter {} did not accept voting message back. "
                              "Everything is over, nothing works anymore.".format(starter))

    def __search_peers(self):
        """
        Autodetect active peers from the searchlist of possible peers.
        """
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
        """
        Send a request to join the cluster to all active peers.

        Raises:
            JoiningClusterError: An error occured during the process of joining the cluster.
        """
        for peer in self.peers:
            try:
                r = requests.post("http://"+peer.host+":"+str(peer.port)+"/new_node", json=self.to_dict())
            except requests.exceptions.ConnectionError:
                raise JoiningClusterError
            if r.status_code == 200:
                if r.text == "master":
                    logging.info("Found current master: {}".format(peer))
                    self.master = peer
            else:
                raise JoiningClusterError
        if self.master is None:
            raise JoiningClusterError
