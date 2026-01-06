"""
Port Manager - Allocates unique ports for test agents.

Ensures no port conflicts during parallel testing.
"""

import socket
from typing import Set


class PortManager:
    """
    Manages port allocation for test agents.

    Ensures each agent gets a unique port during testing.
    """

    def __init__(self, start_port: int = 8000):
        """
        Initialize port manager.

        Args:
            start_port: Starting port number for allocation
        """
        self.start_port = start_port
        self.allocated_ports: Set[int] = set()
        self.current_port = start_port

    def allocate(self) -> int:
        """
        Allocate a free port.

        Returns:
            int: Available port number
        """
        while self.current_port in self.allocated_ports:
            self.current_port += 1

        port = self.current_port
        self.allocated_ports.add(port)
        self.current_port += 1
        return port

    def release(self, port: int) -> None:
        """
        Release a previously allocated port.

        Args:
            port: Port number to release
        """
        self.allocated_ports.discard(port)

    def is_port_available(self, port: int) -> bool:
        """
        Check if a port is available.

        Args:
            port: Port number to check

        Returns:
            bool: True if port is available
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.bind(("127.0.0.1", port))
            sock.close()
            return True
        except OSError:
            return False

    def reset(self) -> None:
        """Reset the port manager."""
        self.allocated_ports.clear()
        self.current_port = self.start_port
