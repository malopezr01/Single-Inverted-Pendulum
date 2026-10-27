"""Console optimizer for the ESP32 pendulum via the existing GUI TCP bridge.

Start the GUI, stabilize in LQR, enable OPTIMIZATION, then run this script.
The GUI is the sole serial owner. Requires ESP32 firmware supporting
F,<id>,<C>,<epsilon>\\n and ACK,F,<id>,<C>,<epsilon>.
"""
import argparse
import csv
import itertools
import json
import math
from pathlib import Path
import select
import socket
import statistics
import time
from datetime import datetime, timezone
from collections import deque


class ExperimentAborted(RuntimeError):
    pass


class BridgeClient:
    def __init__(self, host, port):
        self.sock = socket.create_connection((host, port), timeout=5)
        self.sock.setblocking(False)
        self.buffer = bytearray()
        self.events = deque()
        self.last_telemetry = time.monotonic()
        self.state = None
        self.mode = None

    def close(self):
        self.sock.close()

    def send(self, payload):
        self.sock.sendall((json.dumps(payload, allow_nan=False) + "\n").encode("utf-8"))

    def recv(self, timeout=0.4):
        if self.events:
            return self.events.popleft()
        ready, _, _ = select.select([self.sock], [], [], timeout)
        if not ready:
            return None
        chunk = self.sock.recv(8192)
        if not chunk:
            raise ExperimentAborted("GUI disconnected or optimization disabled")
        self.buffer.extend(chunk)
        if len(self.buffer) > 1000000:
            raise ExperimentAborted("Bridge message too long")
        while b"\n" in self.buffer:
            raw, _, remainder = self.buffer.partition(b"\n")
            self.buffer = bytearray(remainder)
            try:
                event = json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                raise ExperimentAborted("Invalid message from GUI") from None
            if isinstance(event, dict):
                self.events.append(event)
        return self.events.popleft() if self.events else None


def cost(samples):
    """All error terms dimensionless after normalization.

    Fixed weights are experimental defaults, not a tuned physical cost.
    """
    n = len(samples)
    if n < 3:
        raise ExperimentAborted("Too few valid samples")
    angles = [float(row["theta"]) for row in samples]
    carts = [float(row["x"]) for row in samples]
    commands = [float(row["u"]) for row in samples]
    if not all(math.isfinite(v) for v in angles + carts + commands):
        raise ExperimentAborted("Non-finite sample")
    theta_ref = math.radians(2)
    j_theta = sum((v / theta_ref) ** 2 for v in angles) / n
    j_cart = sum((v / 0.10) ** 2 for v in carts) / n
    j_effort = sum((v / 15.0) ** 2 for v in commands) / n
    j_changes = sum(((b - a) / 15.0) ** 2 for a, b in zip(commands, commands[1:])) / (n - 1)
    return {
        "J": j_theta + 0.2 * j_cart + 0.05 * j_effort + 0.05 * j_changes,
        "rms_deg": math.degrees(math.sqrt(sum(v * v for v in angles) / n)),
        "peak_deg": math.degrees(max(abs(v) for v in angles)),
        "rms_cart_m": math.sqrt(sum(v * v for v in carts) / n),
        "rms_u": math.sqrt(sum(v * v for v in commands) / n),
        "samples": n,
    }


class ExperimentRunner:
    def __init__(self, client, args):
        self.client = client
        self.args = args
        self.request_id = 0
        self.last_time = None

    def _checked_event(self, timeout=0.4, allow_wait=False):
        event = self.client.recv(timeout)
        if event is None:
            if not allow_wait and time.monotonic() - self.client.last_telemetry > 1.5:
                raise ExperimentAborted("Telemetry timeout")
            return None
        kind = event.get("type")
        if kind == "reject":
            raise ExperimentAborted(f"Parameter command rejected by GUI: {event}")
        if kind == "telemetry":
            data = event.get("data", {})
            self.client.last_telemetry = time.monotonic()
            state = data.get("state")
            mode = data.get("mode")
            self.client.state = state
            self.client.mode = mode
            if not allow_wait and (state != 3 or mode != 1):
                raise ExperimentAborted(f"Left RUNNING/LQR: state={state}, mode={mode}")
            if state == 3 and mode == 1:
                try:
                    theta = float(data["theta"])
                    x = float(data["x"])
                    u = float(data["u"])
                except (KeyError, TypeError, ValueError):
                    raise ExperimentAborted("Required theta/x/u telemetry missing") from None
                if not all(math.isfinite(v) for v in (theta, x, u)):
                    raise ExperimentAborted("Non-finite telemetry")
                if abs(theta) >= math.radians(self.args.max_theta_deg):
                    raise ExperimentAborted("Angular experiment guard exceeded")
                if abs(x) >= self.args.max_x:
                    raise ExperimentAborted("Cart-position experiment guard exceeded")
        return event

    def await_running(self):
        print("Waiting for RUNNING/LQR telemetry from GUI...")
        end = time.monotonic() + self.args.wait_running
        while time.monotonic() < end:
            event = self._checked_event(0.4, allow_wait=True)
            if event and event.get("type") == "telemetry" and self.client.state == 3 and self.client.mode == 1:
                return
        raise ExperimentAborted("Did not receive RUNNING/LQR telemetry")

    def set_parameters(self, c, epsilon):
        self.request_id += 1
        rid = self.request_id
        self.client.send({"type": "set", "id": rid, "c": c, "epsilon": epsilon})
        limit = time.monotonic() + 4.0
        while time.monotonic() < limit:
            event = self._checked_event()
            if event is None:
                continue
            if event.get("type") == "ack" and event.get("id") == rid:
                if abs(float(event.get("c", -99)) - c) > 0.00001 or abs(float(event.get("epsilon", -99)) - epsilon) > 0.00001:
                    raise ExperimentAborted("Firmware ACK mismatched requested parameters")
                return
        raise ExperimentAborted("No firmware ACK for F parameter command")

    def collect(self):
        settle_end = time.monotonic() + self.args.settle
        while time.monotonic() < settle_end:
            self._checked_event()
        start = time.monotonic()
        samples = []
        while time.monotonic() - start < self.args.window:
            event = self._checked_event()
            if event and event.get("type") == "telemetry":
                samples.append(event["data"])
        if len(samples) < max(15, int(self.args.window * 10)):
            raise ExperimentAborted(f"Insufficient samples in evaluation window: {len(samples)}")
        return cost(samples)


def candidates(args):
    # LQR baseline must be measured first, before applying any nonlinear term.
    yield 0.0, 1.0
    for c, epsilon in itertools.product(args.c_values, args.epsilon_values):
        if c > 0:
            yield c, epsilon


def run(args):
    client = BridgeClient(args.host, args.port)
    writer = None
    csv_file = None
    try:
        runner = ExperimentRunner(client, args)
        runner.await_running()
        filename = Path(args.output)
        filename.parent.mkdir(parents=True, exist_ok=True)
        exists = filename.exists() and filename.stat().st_size > 0
        csv_file = filename.open("a", newline="", encoding="utf-8")
        fields = ["utc", "request_id", "c", "epsilon", "J", "rms_deg", "peak_deg", "rms_cart_m", "rms_u", "samples"]
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        if not exists:
            writer.writeheader()

        best = None
        for index, (c, epsilon) in enumerate(candidates(args), 1):
            print(f"Trial {index}: requesting C={c:.3f}, epsilon={epsilon:.3f} ...")
            runner.set_parameters(c, epsilon)
            result = runner.collect()
            writer.writerow({
                "utc": datetime.now(timezone.utc).isoformat(),
                "request_id": runner.request_id,
                "c": c,
                "epsilon": epsilon,
                **result,
            })
            csv_file.flush()
            if best is None or result["J"] < best[0]:
                best = (result["J"], c, epsilon)
            print(f"  J={result['J']:.5f} | RMS={result['rms_deg']:.3f} deg "
                  f"| peak={result['peak_deg']:.3f} deg | n={result['samples']}")
        if best:
            print(f"BEST: J={best[0]:.5f} at C={best[1]:.3f}, epsilon={best[2]:.3f}")
            print("End of scan: returning to nominal C=0. Best config is NOT left active.")
    finally:
        # Attempt only. Recovery cannot be guaranteed by sending nominal gains.
        try:
            if client.state == 3 and client.mode == 1:
                client.send({"type": "set", "id": 2147483647, "c": 0.0, "epsilon": 1.0})
                print("Requested nominal C=0 restore; verify firmware ACK/GUI.")
        except OSError:
            pass
        if csv_file:
            csv_file.close()
        client.close()


def main():
    parser = argparse.ArgumentParser(description="Console-only pendulum compensator search")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--window", type=float, default=15.0)
    parser.add_argument("--settle", type=float, default=2.0)
    parser.add_argument("--wait-running", type=float, default=30.0)
    parser.add_argument("--max-theta-deg", type=float, default=6.0)
    parser.add_argument("--max-x", type=float, default=0.12)
    parser.add_argument("--c-values", type=float, nargs="+", default=[0.05, 0.10, 0.15])
    parser.add_argument("--epsilon-values", type=float, nargs="+", default=[0.8, 1.5])
    parser.add_argument("--output", default="optimization_results.csv")
    args = parser.parse_args()
    if not (args.window >= 3 and args.settle >= 0 and args.wait_running > 0
            and 0 < args.max_theta_deg < 15 and 0 < args.max_x < 0.15
            and all(math.isfinite(c) and 0 <= c <= 1 for c in args.c_values)
            and all(math.isfinite(e) and 0.05 <= e <= 5 for e in args.epsilon_values)):
        parser.error("Invalid experiment safety or candidate limits")
    try:
        run(args)
    except (ExperimentAborted, OSError, KeyboardInterrupt) as exc:
        print(f"OPTIMIZATION STOPPED: {exc}")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
