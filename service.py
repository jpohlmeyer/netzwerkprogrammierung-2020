from http.server import BaseHTTPRequestHandler, HTTPServer

from peer import Peer


class Server(Peer):
    """
    Server class for the Netzwerkprogrammierng project, managing the master status of controllers
    by communicating with services started on all controllers.

    ...

    Attributes
    ----------
    host : str
        Host the service is started on
    port : int
        The port the service is accepting connections
    peers : [Peer]
        List of the peers currently in the cluster
    master : Peer
        Current master peer

    Methods
    -------
    start()
        Starts the HTTP server to accept connections
    """
    def __init__(self, host, port, searchList):
        super().__init__(host, port)
        self.searchList = searchList
        # TODO search List for peers

    def start(self):
        """
        Starts the HTTP server to accept connections
        :return:
        """
        with HTTPServer((self.host, self.port), ServiceRequestHandler) as httpserver:
            httpserver.model = self
            httpserver.serve_forever()


class ServiceRequestHandler(BaseHTTPRequestHandler):
    """
    Extends BaseHTTPRequestHandler to serve HTTP Requests.
    """

    def do_GET(self):
        """
        Defines how GET requests are handled.
        :return:
        """
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write("Netzwerkprogrammierung2020".encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write("Not Found.".encode('utf-8'))