import hashlib

class Peer:
    """
    Peer class representing a peer host in a high availability cluster running the same service.

    ...

    Attributes
    ----------
    id : str
        ID to identify peer
    host : str
        Host the service is started on
    port : int
        The port the service is accepting connections
    """

    def __init__(self, host, port):
        hostport = str(host)+":"+str(port)
        self.id = hashlib.sha256(hostport.encode("utf8")).hexdigest()
        self.host = host
        self.port = port

    def __str__(self):
        return "Peer(ID: {}, Host: {}, Port: {})".format(self.id, self.host, self.port)

    def to_dict(self):
        return {"id": self.id, "host": self.host, "port": self.port}