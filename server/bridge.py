#!/usr/bin/env python3
"""
Edge Rescue — HTTP + SSE bridge server.
Replaces the old WebSocket/rosbridge approach with plain HTTP.

Endpoints:
  POST /goal   — accepts {"prompt": "..."}, publishes to ROS2 topic
  GET  /events — SSE stream of plan and subtask updates

Run:  python3 bridge.py
"""

import json
import subprocess
import threading
import queue
from http.server import HTTPServer, BaseHTTPRequestHandler

HOST = "0.0.0.0"
PORT = 9090

# Global SSE event queue — each connected client gets a reference
sse_clients = []  # list of queue.Queue
sse_lock = threading.Lock()


def broadcast_sse(event_type, data):
    """Push an SSE event to all connected clients."""
    with sse_lock:
        dead = []
        for q in sse_clients:
            try:
                q.put((event_type, data), block=False)
            except queue.Full:
                dead.append(q)
        for q in dead:
            sse_clients.remove(q)


def ros2_pub(topic, message):
    """Publish a string message to a ROS2 topic via subprocess."""
    cmd = [
        "ros2", "topic", "pub", "--once",
        topic, "std_msgs/String",
        f'{{"data": "{message}"}}'
    ]
    print(f"[ros2] {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print(f"[ros2] stderr: {result.stderr.strip()}")
    except FileNotFoundError:
        print("[ros2] ros2 CLI not found — running in demo mode")
    except subprocess.TimeoutExpired:
        print("[ros2] publish timed out")


def handle_goal(prompt):
    """Process a mission goal: publish to ROS2, then run placeholder plan logic."""
    print(f"\n{'='*50}")
    print(f"  MISSION GOAL: {prompt}")
    print(f"{'='*50}\n")

    # Try to publish to real ROS2 topic
    ros2_pub("/mission/goal", prompt)

    # --- PLACEHOLDER: replace with actual LLM call ---
    plan = [
        f"Locate objects for: {prompt}",
        "Pick up first block",
        "Place block at target position",
        "Verify placement in simulation",
        "Report result",
    ]

    # Broadcast the full plan
    broadcast_sse("plan", json.dumps(plan))

    # Step through subtasks
    import time
    for i, step in enumerate(plan):
        broadcast_sse("subtask", step)
        print(f"  [{i+1}/{len(plan)}] {step}")
        time.sleep(1)

    broadcast_sse("subtask", "Done.")
    print("  Mission complete.\n")


class BridgeHandler(BaseHTTPRequestHandler):
    """Handles POST /goal and GET /events."""

    def _cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    def do_POST(self):
        if self.path == "/goal":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                prompt = data.get("prompt", "")
            except (json.JSONDecodeError, AttributeError):
                prompt = body.decode("utf-8", errors="replace")

            if not prompt:
                self.send_response(400)
                self._cors_headers()
                self.end_headers()
                self.wfile.write(b'{"error":"empty prompt"}')
                return

            self.send_response(200)
            self._cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())

            # Process in background thread so the response returns immediately
            threading.Thread(target=handle_goal, args=(prompt,), daemon=True).start()
        else:
            self.send_response(404)
            self._cors_headers()
            self.end_headers()

    def do_GET(self):
        if self.path == "/events":
            self.send_response(200)
            self._cors_headers()
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            q = queue.Queue(maxsize=256)
            with sse_lock:
                sse_clients.append(q)

            print(f"[sse]  Client connected ({len(sse_clients)} total)")

            try:
                while True:
                    try:
                        event_type, data = q.get(timeout=15)
                        payload = f"event: {event_type}\ndata: {data}\n\n"
                        self.wfile.write(payload.encode())
                        self.wfile.flush()
                    except queue.Empty:
                        # Send keepalive comment
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            finally:
                with sse_lock:
                    if q in sse_clients:
                        sse_clients.remove(q)
                print(f"[sse]  Client disconnected ({len(sse_clients)} total)")
        elif self.path == "/":
            self.send_response(200)
            self._cors_headers()
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Edge Rescue bridge is running.\n")
        else:
            self.send_response(404)
            self._cors_headers()
            self.end_headers()

    def log_message(self, format, *args):
        # Quieter logging — only show errors
        if args and "404" in str(args[0]):
            super().log_message(format, *args)


class ThreadedHTTPServer(HTTPServer):
    """Handle each request in a new thread (needed for long-lived SSE connections)."""
    allow_reuse_address = True
    daemon_threads = True

    def process_request(self, request, client_address):
        t = threading.Thread(target=self.process_request_thread, args=(request, client_address), daemon=True)
        t.start()

    def process_request_thread(self, request, client_address):
        try:
            self.finish_request(request, client_address)
        except Exception:
            self.handle_error(request, client_address)
        finally:
            self.shutdown_request(request)


def main():
    server = ThreadedHTTPServer((HOST, PORT), BridgeHandler)
    print(f"Edge Rescue bridge listening on http://{HOST}:{PORT}")
    print(f"  POST /goal    — send a mission prompt")
    print(f"  GET  /events  — SSE stream of plan/subtask updates")
    print(f"Waiting for connections...\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
