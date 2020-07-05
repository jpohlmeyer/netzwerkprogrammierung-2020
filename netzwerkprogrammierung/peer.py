"""
In this module the Peer class is defined.
"""

import hashlib


class Peer:
    """
    Peer class representing a peer host in a high availability cluster running the same service.

    Attributes:
        id: str, ID to identify peer
        host: str, Host the service is started on
        port: int, The port the service is accepting connections
        active: bool, True if the last heartbeat request was succesfully answered, False if not.
    """

    def __init__(self, host, port):
        """
        Inits the Peer, generating an unique id.

        Args:
            host: hostname or ip of the peer
            port: port of the peer
        """
        hostport = str(host)+":"+str(port)
        self.id = hashlib.sha256(hostport.encode("utf8")).hexdigest()
        self.host = host
        self.port = port
        self.active = True

    def __str__(self):
        """
        String Representation of Peer class.

        Returns:
            String Representation of Peer class in the form

            Peer(ID: {}, Host: {}, Port: {})
        """
        return "Peer(ID: {}, Host: {}, Port: {})".format(self.id, self.host, self.port)

    def to_dict(self):
        """
        Generate a dict, representing the Peer. Used in the payload of requests.

        Returns:
             dict with id, host and port
        """
        return {"id": self.id, "host": self.host, "port": self.port}
