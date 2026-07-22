"""Prove the autouse socket guard blocks outbound connections."""

from __future__ import annotations

import socket

import pytest


def test_direct_socket_connect_is_blocked() -> None:
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(OSError):
            connection.connect(("127.0.0.1", 9))
    finally:
        connection.close()


def test_create_connection_is_blocked() -> None:
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", 9), timeout=0.1)
