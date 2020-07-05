import unittest
from netzwerkprogrammierung.host import Host
from netzwerkprogrammierung.peer import Peer


class MockHost(Host):
    # Override __execute_script method of Host to not execute scripts during tests
    def _Host__execute_script(self):
        pass


class HostTest(unittest.TestCase):

    def test_simple_add_peer(self):
        host = MockHost("localhost", "7000", [], "masterscript.sh", "slavescript.sh")
        old_peers = host.peers.copy()
        peer = Peer("peerhost", "7001")
        host.add_peer(peer)
        self.assertEqual(len(host.peers)-len(old_peers), 1, "Difference in number of peers should be 1")
        self.assertEqual(host.peers[-1].host, "peerhost", "Hostname of last peer should be peerhost")
        self.assertEqual(host.peers[-1].port, "7001", "Port of last peer should be 7001")

    def test_duplicate_add_peer(self):
        host = MockHost("localhost", "7000", [], "masterscript.sh", "slavescript.sh")
        old_peers = host.peers.copy()
        peer = Peer("peerhost", "7001")
        host.add_peer(peer)
        host.add_peer(peer)
        self.assertEqual(len(host.peers)-len(old_peers), 1, "Difference in number of peers should be 1")

    def test_update_master(self):
        host = MockHost("localhost", "7000", [], "masterscript.sh", "slavescript.sh")
        peer = Peer("localhost", "7001")
        host.add_peer(peer)
        host.update_master(peer)
        self.assertEqual(host.master.host, "localhost", "Master host should be localhost")
        self.assertEqual(host.master.port, "7001", "Master port should be 7001")

    def test_start_no_peers(self):
        host = MockHost("localhost", "7000", [], "masterscript.sh", "slavescript.sh")
        host.start()
        self.assertEqual(host.master.host, "localhost", "Master host should be localhost")
        self.assertEqual(host.master.port, "7000", "Master port should be 7000")
        self.assertEqual(len(host.peers), 0, "Number of peers should be 0")

    def test_start_with_not_started_peers(self):
        peer1 = Peer("peer1host", "7001")
        peer2 = Peer("peer2host", "7002")
        host = MockHost("localhost", "7000", [peer1, peer2], "masterscript.sh", "slavescript.sh")
        host.start()
        self.assertEqual(host.master.host, "localhost", "Master host should be localhost")
        self.assertEqual(host.master.port, "7000", "Master port should be 7000")
        self.assertEqual(len(host.peers), 0, "Number of peers should be 0")
