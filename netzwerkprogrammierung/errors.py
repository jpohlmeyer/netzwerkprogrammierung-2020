"""
This module defines the error classes used by the service.

Here JoiningClusterError and VotingError are defined
"""


class JoiningClusterError(Exception):
    """
    Error when joining the server cluster.
    """
    pass


class VotingError(Exception):
    """
    Error when voting for a new master.
    """
    pass
