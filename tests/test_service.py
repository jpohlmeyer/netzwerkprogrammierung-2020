import threading
import time
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
        peer = Peer("peerhost", 7001)
        r = requests.post("http://" + host.host + ":" + str(host.port) + "/new_node", json=peer.to_dict())
        server.stop_server()
        server_thread.join()
        self.assertEqual(r.status_code, 200, "Status code should be 200")
        self.assertEqual(r.text, "master", "Answer should be master")
        self.assertEqual(len(host.peers), 1, "Number of peers should be 1")
        self.assertEqual(host.peers[-1].host, "peerhost", "Host name of peer should be peerhost")
        self.assertEqual(host.peers[-1].port, 7001, "Port of peer should be 7001")

    def test_post_new_node_duplicate(self):
        host = MockHost("localhost", 7000, [], "masterscript.sh", "slavescript.sh")
        host.start()
        server = Server(host)
        server_thread = threading.Thread(target=server.accept_connections)
        server_thread.start()
        peer = Peer("peerhost", 7001)
        host.peers.append(peer)
        r = requests.post("http://" + host.host + ":" + str(host.port) + "/new_node", json=peer.to_dict())
        server.stop_server()
        server_thread.join()
        self.assertEqual(r.status_code, 503, "Status code should be 503")

    def test_simple_vote(self):
        host = MockHost("localhost", 7000, [], "masterscript.sh", "slavescript.sh")
        server = Server(host)
        server_thread = threading.Thread(target=server.accept_connections)
        server_thread.start()
        self.assertIsNone(host.master)
        voting_message = {host.id: 1, "starter": host.id, "old_master": 0}
        r = requests.post("http://" + host.host + ":" + str(host.port) + "/vote", json=voting_message)
        server.stop_server()
        server_thread.join()
        time.sleep(1)
        self.assertEqual(r.status_code, 200, "Status code should be 200")
        self.assertEqual(host.master.id, host.id, "Host should be master")

    def test_heartbeat_successful(self):
        host = MockHost("localhost", 7000, [], "masterscript.sh", "slavescript.sh")
        host.start()
        server = Server(host)
        server_thread = threading.Thread(target=server.accept_connections)
        server_thread.start()
        self.assertEqual(len(host.peers), 0, "Should be 0 peers")
        peer = Peer("localhost", 7000)
        host.peers.append(peer)
        host.request_heartbeats()
        host.request_heartbeats()
        host.request_heartbeats()
        server.stop_server()
        server_thread.join()
        self.assertEqual(len(host.peers), 1, "Should be 1 peer")

    def test_heartbeat_unsuccessful(self):
        host = MockHost("localhost", 7000, [], "masterscript.sh", "slavescript.sh")
        host.start()
        server = Server(host)
        server_thread = threading.Thread(target=server.accept_connections)
        server_thread.start()
        self.assertEqual(len(host.peers), 0, "Should be 0 peers")
        peer = Peer("localhost", 7001)
        host.peers.append(peer)
        self.assertEqual(len(host.peers), 1, "Should be 1 peers")
        host.request_heartbeats()
        self.assertEqual(len(host.peers), 1, "Should be 1 peers")
        host.request_heartbeats()
        server.stop_server()
        server_thread.join()
        self.assertEqual(len(host.peers), 0, "Should be 1 peer")

    def test_heartbeat_unsuccessful_master(self):
        host = MockHost("localhost", 7000, [], "masterscript.sh", "slavescript.sh")
        host.start()
        server = Server(host)
        server_thread = threading.Thread(target=server.accept_connections)
        server_thread.start()
        self.assertEqual(len(host.peers), 0, "Should be 0 peers")
        peer = Peer("localhost", 7001)
        host.peers.append(peer)
        host.update_master(peer)
        self.assertEqual(len(host.peers), 1, "Should be 1 peers")
        host.request_heartbeats()
        self.assertEqual(len(host.peers), 1, "Should be 1 peers")
        host.request_heartbeats()
        server.stop_server()
        server_thread.join()
        self.assertEqual(len(host.peers), 0, "Should be 1 peer")
        self.assertEqual(host.master.id, host.id, "host should be master")

    def test_post_new_node_unavailable(self):
        host = MockHost("localhost", 7000, [], "masterscript.sh", "slavescript.sh")
        server = Server(host)
        server_thread = threading.Thread(target=server.accept_connections)
        server_thread.start()
        peer = Peer("peerhost", 7001)
        r = requests.post("http://" + host.host + ":" + str(host.port) + "/new_node", json=peer.to_dict())
        server.stop_server()
        server_thread.join()
        self.assertEqual(r.status_code, 503, "Status code should be 503")

    def test_post_new_master(self):
        host = MockHost("localhost", 7000, [], "masterscript.sh", "slavescript.sh")
        host.start()
        server = Server(host)
        server_thread = threading.Thread(target=server.accept_connections)
        server_thread.start()
        peer = Peer("masterhost", 7001)
        host.add_peer(peer)
        r = requests.post("http://" + host.host + ":" + str(host.port) + "/new_master", json=peer.to_dict())
        server.stop_server()
        server_thread.join()
        self.assertEqual(r.status_code, 200, "Status code should be 200")
        self.assertEqual(host.master.host, "masterhost", "Host name of master should be masterhost")
        self.assertEqual(host.master.port, 7001, "Port of master should be 7001")

    def test_post_404(self):
        host = MockHost("localhost", 7000, [], "masterscript.sh", "slavescript.sh")
        server = Server(host)
        server_thread = threading.Thread(target=server.accept_connections)
        server_thread.start()
        r = requests.post("http://" + host.host + ":" + str(host.port) + "/test")
        server.stop_server()
        server_thread.join()
        self.assertEqual(r.status_code, 404, "Status code should be 404")
