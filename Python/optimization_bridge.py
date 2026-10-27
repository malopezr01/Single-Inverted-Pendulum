"""Local JSON-lines bridge between the existing GUI and a console optimizer.

Only the GUI owns the ESP32 serial port. This Qt TCP server listens on
127.0.0.1, accepts at most one client, and never accesses the serial port.
"""
import json

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QHostAddress, QTcpServer


class OptimizationBridge(QObject):
    parameters_requested = Signal(int, float, float)
    notice = Signal(str)

    def __init__(self, parent=None, port=8765):
        super().__init__(parent)
        self.port = port
        self.server = QTcpServer(self)
        self.server.newConnection.connect(self._accept)
        self.client = None
        self._pending = bytearray()

    @property
    def active(self):
        return self.server.isListening()

    def start(self):
        if self.active:
            return True
        if not self.server.listen(QHostAddress.SpecialAddress.LocalHost, self.port):
            self.notice.emit("Optimization TCP error: " + self.server.errorString())
            return False
        self.notice.emit(f"Optimization bridge listening on 127.0.0.1:{self.port}")
        return True

    def stop(self):
        if self.client is not None:
            self.client.disconnectFromHost()
            self.client.close()
            self.client.deleteLater()
            self.client = None
        self._pending.clear()
        self.server.close()

    def _accept(self):
        while self.server.hasPendingConnections():
            client = self.server.nextPendingConnection()
            if self.client is not None:
                client.close()
                client.deleteLater()
                continue
            self.client = client
            self._pending.clear()
            client.readyRead.connect(self._read)
            client.disconnected.connect(lambda sock=client: self._disconnected(sock))
            self.send({"type": "hello", "protocol": 1})
            self.notice.emit("Optimizer connected")

    def _disconnected(self, socket):
        if socket is self.client:
            self.client = None
            self._pending.clear()
            self.notice.emit("Optimizer disconnected")
        socket.deleteLater()

    def send(self, payload):
        if self.client is None:
            return
        # Never allow a slow client to delay the GUI or grow an unbounded buffer.
        if self.client.bytesToWrite() > 65536:
            self.notice.emit("Optimizer is too slow; disconnecting")
            self.client.disconnectFromHost()
            return
        line = (json.dumps(payload, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")
        self.client.write(line)

    def publish_telemetry(self, data):
        self.send({"type": "telemetry", "data": data})

    def publish_ack(self, line):
        # Firmware replies with ACK,F,<request_id>,<C>,<epsilon>.
        fields = line.strip().split(",")
        if len(fields) != 5 or fields[:2] != ["ACK", "F"]:
            return
        try:
            request_id = int(fields[2])
            c = float(fields[3])
            epsilon = float(fields[4])
        except ValueError:
            return
        self.send({"type": "ack", "id": request_id, "c": c, "epsilon": epsilon})

    def _read(self):
        if self.client is None:
            return
        self._pending.extend(bytes(self.client.readAll()))
        if len(self._pending) > 4096:
            self.notice.emit("Optimizer command too long; disconnecting")
            self.client.disconnectFromHost()
            self._pending.clear()
            return
        while b"\n" in self._pending:
            raw, _, remaining = self._pending.partition(b"\n")
            self._pending = bytearray(remaining)
            try:
                message = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, ValueError):
                self.send({"type": "reject", "reason": "invalid JSON"})
                continue
            if not isinstance(message, dict) or message.get("type") != "set":
                self.send({"type": "reject", "reason": "unknown command"})
                continue
            try:
                request_id = message["id"]
                c = float(message["c"])
                epsilon = float(message["epsilon"])
                if isinstance(request_id, bool) or not isinstance(request_id, int):
                    raise ValueError()
            except (KeyError, ValueError, TypeError):
                self.send({"type": "reject", "reason": "invalid parameters"})
                continue
            self.parameters_requested.emit(request_id, c, epsilon)
