"""
This service tries to establish a connection with peer services started on other controllers
to determine which controller is the master server in a high availabitlity cluster.
It can be started using the following command:

    python3 app.py [-h] [--host HOST] [--port PORT] [--searchlist SEARCHLIST]

"""

import argparse
import threading
import time
import logging
import sys
from netzwerkprogrammierung.errors import JoiningClusterError
from netzwerkprogrammierung.peer import Peer
from netzwerkprogrammierung.host import Host
from netzwerkprogrammierung.service import Server

def main():
    """
    Main function starting the service.
    :return:
    """
    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

    parser = argparse.ArgumentParser(description="Determine master server in a high availability cluster.")
    parser.add_argument("--host", default="localhost",
                        help="Host the service is started on.")
    parser.add_argument("--port", type=int, default="7500",
                        help="Host the service is started on.")
    parser.add_argument("--searchlist", default="",
                        help="List of possible hosts with ports for autodetection of peer services.")
    parser.add_argument("--masterscript", default="masterscript.sh",
                        help="Script that will be executed by the new master after the master changes.")
    parser.add_argument("--slavescript", default="slavescript.sh",
                        help="Script that will be executed by every slave after the master changes.")
    args = parser.parse_args()
    possible_peers = []
    for peer in args.searchlist.split(','):
        peer_split = peer.split(":")
        if len(peer_split) == 2:
            possible_peers.append(Peer(peer_split[0], peer_split[1]))
    host = Host(args.host, args.port, possible_peers, args.masterscript, args.slavescript)
    try:
        server = Server(host)
    except OSError:
        logging.error("Address already in use. Exiting.")
        sys.exit(1)
    server_thread = threading.Thread(target=server.accept_connections)
    server_thread.start()
    try:
        host.start()
    except JoiningClusterError:
        logging.error("Could not join cluster. Exiting.")
        server.stop_server()
        server_thread.join()
        sys.exit(1)
    try:
        while True:
            time.sleep(1)
            host.request_heartbeats()
    except KeyboardInterrupt:
        logging.info("Terminating.")
        server.stop_server()
        server_thread.join()