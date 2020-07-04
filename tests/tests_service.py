import threading
import unittest
import requests
from netzwerkprogrammierung.host import Host
from netzwerkprogrammierung.service import Server
from netzwerkprogrammierung.peer import Peer


class MockHost(Host):
    # Override __execute_script method of Host to not execute scripts during tests
    def _Host__execute_script(self):
        pass


class ServerTest(unittest.TestCase):

    def test_get_root(self):
        host = MockHost("localhost", 7000, [], "masterscript.sh", "slavescript.sh")
        server = Server(host)
        server_thread = threading.Thread(target=server.accept_connections)
        server_thread.start()
        r = requests.get("http://" + host.host + ":" + str(host.port) + "/")
        server.stop_server()
        server_thread.join()
        self.assertEqual(r.status_code, 200, "Status code should be 200")
        self.assertEqual(r.text, "Netzwerkprogrammierung2020", "Answer should be Netzwerkprogrammierung2020")

    def test_get_heartbeat(self):
        host = MockHost("localhost", 7000, [], "masterscript.sh", "slavescript.sh")
        server = Server(host)
        server_thread = threading.Thread(target=server.accept_connections)
        server_thread.start()
        r = requests.get("http://" + host.host + ":" + str(host.port) + "/heartbeat")
        server.stop_server()
        server_thread.join()
        self.assertEqual(r.status_code, 200, "Status code should be 200")
        self.assertEqual(r.text, "pong", "Heartbeat answer should be pong")

    def test_get_404(self):
        host = MockHost("localhost", 7000, [], "masterscript.sh", "slavescript.sh")
        server = Server(host)
        server_thread = threading.Thread(target=server.accept_connections)
        server_thread.start()
        r = requests.get("http://" + host.host + ":" + str(host.port) + "/test")
        server.stop_server()
        server_thread.join()
        self.assertEqual(r.status_code, 404, "Status code should be 404")

    def test_post_new_node(self):
        host = MockHost("localhost", 7000, [], "masterscript.sh", "slavescript.sh")
        host.start()
        server = Server(host)
        server_thread = threading.Thread(target=server.accept_connections)
        server_thread.start()
        peer = Peer("localhost", 7001)
        r = requests.post("http://" + host.host + ":" + str(host.port) + "/new_node", json=peer.to_dict())
        server.stop_server()
        server_thread.join()
        self.assertEqual(r.status_code, 200, "Status code should be 200")
        self.assertEqual(r.text, "master", "Answer should be master")
        self.assertEqual(len(host.peers), 1, "Number of peers should be 1")
        self.assertEqual(host.peers[-1].host, "localhost", "Host name of peer should be localhost")
        self.assertEqual(host.peers[-1].port, 7001, "Port of peer should be 7001")