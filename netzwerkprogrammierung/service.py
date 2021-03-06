"""
This module includes a HTTP server and a ServiceRequestHandler.
"""

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from netzwerkprogrammierung.peer import Peer


class Server:
    """
    Server class for managing the HTTP requests made to the service.

    Attributes:
        host : Host, Host the service is started on.
    """

    def __init__(self, host):
        """
        Init the server.

        Args:
            host: Host, host corresponding to the server.
        """
        self.host = host
        self.httpserver = HTTPServer((self.host.host, self.host.port), ServiceRequestHandler)
        self.httpserver.host = self.host

    def accept_connections(self):
        """
        Starts the HTTP server to accept connections.
        """
        logging.info("HTTP server started")
        self.httpserver.serve_forever()

    def stop_server(self):
        """
        Stops the HTTP server.
        """
        logging.info("HTTP server stopped")
        self.httpserver.shutdown()
        self.httpserver.server_close()


class ServiceRequestHandler(BaseHTTPRequestHandler):
    """
    Extends BaseHTTPRequestHandler to serve HTTP Requests.
    """

    def do_GET(self):
        """
        Defines how GET requests are handled. Overrides BaseHTTPRequestHandler method.
        """
        if self.path == "/":
            self.__set_response()
            self.wfile.write("Netzwerkprogrammierung2020".encode('utf-8'))
        elif self.path == "/heartbeat":
            self.__set_response()
            self.wfile.write("pong".encode('utf-8'))
        else:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write("Not Found.".encode('utf-8'))

    def do_POST(self):
        """
        Defines how POST requests are handled. Overrides BaseHTTPRequestHandler method.
        """
        if self.path == "/new_node":
            # Add new node to cluster
            if self.server.host.master is None:
                logging.info("Did not allow new peer to join during voting process.")
                self.__respond_service_unavailable("Service temporarily unavailable.")
                return  # Do not accept new peers to the cluster while there is no new master yet.
            peer_json = self.__receive_post_payload()
            peer = Peer(peer_json['host'], int(peer_json['port']))
            if not self.server.host.add_peer(peer):
                logging.info("Did not allow duplicate peer to join.")
                self.__respond_service_unavailable("Duplicate ID detected.")
                return  # Do not accept duplicate peers to the cluster
            self.__set_response()
            if self.server.host.master == self.server.host:
                answer = "master"
            else:
                answer = "not master"
            self.wfile.write(answer.encode('utf-8'))
            logging.info("Added peer {} to the cluster.".format(peer))
        elif self.path == "/vote":
            # vote for new master
            votes_dict = self.__receive_post_payload()
            vote_thread = threading.Thread(target=self.server.host.vote, args=(votes_dict,))
            vote_thread.start()
            self.__set_response()
            self.wfile.write("".encode('utf-8'))
        elif self.path == "/new_master":
            # get new master from vote starter
            peer_json = self.__receive_post_payload()
            peer = Peer(peer_json['host'], int(peer_json['port']))
            self.server.host.update_master(peer)
            self.__set_response()
            self.wfile.write("".encode('utf-8'))
            logging.info("New master {}.".format(peer))
        else:
            # undefined operation
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write("Not Found.".encode('utf-8'))

    def __receive_post_payload(self):
        """
        Decode json content as dict.

        Returns:
            dict corresponding to the json object/
        """
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        return json.loads(post_data)

    def __set_response(self):
        """
        Set standard response.
        """
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()

    def __respond_service_unavailable(self, message):
        """
        Set response if the service is unavailable.

        Args:
            message: Message to be sent.
        """
        self.send_response(503)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(message.encode('utf-8'))

    def log_request(self, code='-', size='-'):
        """
        Define how requests are logged.

        Override log_request method from BaseHTTPRequestHandler to not log every
        normal incoming HTTP request to stdout.
        """
        pass
