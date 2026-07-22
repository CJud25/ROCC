from __future__ import annotations

import socket

import pytest

from tens_hq.synthetic import generate_demo_data


class _BlockedNetwork(OSError):
    """Raised when a test attempts to open an outbound socket connection."""


@pytest.fixture(autouse=True)
def _block_network(monkeypatch):
    """Fail closed so no test can reach a live host.

    The guard blocks the outbound connection primitives ``socket.connect``,
    ``connect_ex``, ``create_connection``, and ``getaddrinfo``. Creating an
    unconnected socket remains harmless and is allowed for in-process tools.
    """

    def _blocked(*_args, **_kwargs):
        raise _BlockedNetwork("network access is blocked during tests (offline guarantee)")

    monkeypatch.setattr(socket.socket, "connect", _blocked, raising=True)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked, raising=True)
    monkeypatch.setattr(socket, "create_connection", _blocked, raising=True)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked, raising=True)
    yield


@pytest.fixture(scope="session")
def demo_data():
    return generate_demo_data()
