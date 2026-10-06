import uuid

from PyQt6.QtTest import QTest

from stickynotes import ipc


def test_send_new_without_server_returns_false(qapp):
    assert ipc.send_new(f"sn-test-{uuid.uuid4()}", timeout=50) is False


def test_second_client_delivers_new(qapp):
    name = f"sn-test-{uuid.uuid4()}"
    inst = ipc.SingleInstance(name)
    got = []
    inst.newRequested.connect(lambda: got.append(1))
    assert inst.listen()
    assert ipc.send_new(name) is True
    QTest.qWait(150)
    assert got == [1]


def test_send_new_returns_false_if_bytes_not_written(qapp, monkeypatch):
    from PyQt6.QtNetwork import QLocalSocket
    monkeypatch.setattr(QLocalSocket, "waitForConnected", lambda self, t: True)
    monkeypatch.setattr(QLocalSocket, "waitForBytesWritten", lambda self, t: False)
    assert ipc.send_new("dummy", timeout=50) is False
