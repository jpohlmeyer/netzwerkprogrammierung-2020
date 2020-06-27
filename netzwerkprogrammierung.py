#!/usr/bin/env python3

"""
This service tries to establish a connection with peer services started on other controllers
to determine which controller is the master server in a high availabitlity cluster.
It can be started using the following command:

    python3 netzwerkprogrammierung.py [-h] [--host HOST] [--port PORT] [--searchlist SEARCHLIST]

"""

import argparse
from service import Server


def main():
    """
    Main function starting the service.
    :return:
    """
    parser = argparse.ArgumentParser(description="Determine master server in a high availability cluster.")
    parser.add_argument("--host", default="localhost",
                        help="Host the service is started on.")
    parser.add_argument("--port", type=int, default="7500",
                        help="Host the service is started on.")
    parser.add_argument("--searchlist", default="localhost",
                        help="List of possible hosts for autodetection of peer services.")
    args = parser.parse_args()
    possible_peers = args.searchlist.split(',')
    server = Server(args.host, args.port, possible_peers)
    server.start()


if __name__ == "__main__":
    main()