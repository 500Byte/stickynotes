"""Instancia única: el segundo lanzamiento pide una nota nueva a la primera."""
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

SERVER_NAME = "stickynotes-ipc"


def send_new(name=SERVER_NAME, timeout=300) -> bool:
    sock = QLocalSocket()
    sock.connectToServer(name)
    if not sock.waitForConnected(timeout):
        return False
    sock.write(b"new\n")
    if not sock.waitForBytesWritten(timeout):
        return False
    sock.disconnectFromServer()
    return True


class SingleInstance(QObject):
    newRequested = pyqtSignal()

    def __init__(self, name=SERVER_NAME, parent=None):
        super().__init__(parent)
        self._name = name
        self._server = QLocalServer(self)
        self._server.newConnection.connect(self._on_connection)

    def listen(self) -> bool:
        QLocalServer.removeServer(self._name)  # elimina socket huérfano
        return self._server.listen(self._name)

    def _on_connection(self):
        sock = self._server.nextPendingConnection()
        if sock is None:
            return

        def read():
            while sock.canReadLine():
                if bytes(sock.readLine()).strip() == b"new":
                    self.newRequested.emit()

        sock.readyRead.connect(read)
        sock.disconnected.connect(sock.deleteLater)
        read()
