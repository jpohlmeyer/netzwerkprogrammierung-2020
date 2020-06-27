from http.server import BaseHTTPRequestHandler, HTTPServer

import logging

class Server():
    """
    Server class for the Netzwerkprogrammierng project, managing the master status of controllers
    by communicating with services started on all controllers.

    ...

    Attributes
    ----------
    host : Host
        Host the service is started on

    Methods
    -------
    acceptConnections()
        Starts the HTTP server to accept connections
    """
    def __init__(self, host):
        self.host = host
        self.httpserver = HTTPServer((self.host.host, self.host.port), ServiceRequestHandler)
        self.httpserver.host = self.host

    def accept_connections(self):
        """
        Starts the HTTP server to accept connections.
        :return:
        """
        logging.info("HTTP server started")
        self.httpserver.serve_forever()

    def stop_server(self):
        """
        Stops the HTTP server.
        :return:
        """
        logging.info("HTTP server stopped")
        self.httpserver.shutdown()


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