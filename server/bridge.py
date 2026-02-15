#!/usr/bin/env python3
"""
Edge Rescue — HTTP + SSE bridge server.

Endpoints:
  POST /goal        — accepts {"prompt": "..."}, publishes to ROS2 topic
  GET  /events      — SSE stream of plan and subtask updates
  GET  /cam0/stream — MJPEG stream from /cam0/compressed ROS2 topic
  GET  /cam0/snap   — single JPEG snapshot

Run:  source /opt/ros/humble/setup.bash && python3 bridge.py
"""

import json
import subprocess
import threading
import queue
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

HOST = "0.0.0.0"
PORT = 9090

# ---- SSE state ----
sse_clients = []  # list of queue.Queue
sse_lock = threading.Lock()

# ---- Camera state ----
latest_frame = None        # raw JPEG bytes
latest_frame_lock = threading.Lock()
cam_clients = []           # list of threading.Event to notify MJPEG clients
cam_clients_lock = threading.Lock()
cam_running = False


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

    ros2_pub("/mission/goal", prompt)

    # --- PLACEHOLDER: replace with actual LLM call ---
    plan = [
        f"Locate objects for: {prompt}",
        "Pick up first block",
        "Place block at target position",
        "Verify placement in simulation",
        "Report result",
    ]

    broadcast_sse("plan", json.dumps(plan))

    for i, step in enumerate(plan):
        broadcast_sse("subtask", step)
        print(f"  [{i+1}/{len(plan)}] {step}")
        time.sleep(1)

    broadcast_sse("subtask", "Done.")
    print("  Mission complete.\n")


# ---- Camera subscriber (rclpy) ----

def start_cam_subscriber():
    """Background thread: subscribe to /cam0/compressed via rclpy and store frames."""
    global latest_frame, cam_running

    try:
        import rclpy
        from rclpy.node import Node
        from sensor_msgs.msg import CompressedImage
    except ImportError:
        print("[cam]  rclpy not available — camera feed disabled")
        print("[cam]  Run: source /opt/ros/humble/setup.bash")
        return

    rclpy.init()

    class CamSub(Node):
        def __init__(self):
            super().__init__("bridge_cam_sub")
            self.sub = self.create_subscription(
                CompressedImage, "/cam0/compressed", self.on_frame, 1
            )
            self.frame_count = 0

        def on_frame(self, msg):
            global latest_frame
            frame_bytes = bytes(msg.data)
            with latest_frame_lock:
                latest_frame = frame_bytes
            # Notify all MJPEG clients
            with cam_clients_lock:
                for evt in cam_clients:
                    evt.set()
            self.frame_count += 1
            if self.frame_count == 1:
                print(f"[cam]  First frame received ({len(frame_bytes)} bytes, format: {msg.format})")
            elif self.frame_count % 300 == 0:
                print(f"[cam]  {self.frame_count} frames received")

    node = CamSub()
    cam_running = True
    print("[cam]  Subscribed to /cam0/compressed")

    try:
        rclpy.spin(node)
    except Exception as e:
        print(f"[cam]  Subscriber error: {e}")
    finally:
        cam_running = False
        node.destroy_node()
        rclpy.shutdown()


class BridgeHandler(BaseHTTPRequestHandler):
    """Handles POST /goal, GET /events, GET /cam0/stream, GET /cam0/snap."""

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

            threading.Thread(target=handle_goal, args=(prompt,), daemon=True).start()
        else:
            self.send_response(404)
            self._cors_headers()
            self.end_headers()

    def do_GET(self):
        if self.path == "/events":
            self._handle_sse()
        elif self.path == "/cam0/stream":
            self._handle_mjpeg()
        elif self.path == "/cam0/snap":
            self._handle_snapshot()
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

    def _handle_sse(self):
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
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with sse_lock:
                if q in sse_clients:
                    sse_clients.remove(q)
            print(f"[sse]  Client disconnected ({len(sse_clients)} total)")

    def _handle_mjpeg(self):
        """Stream MJPEG from /cam0/compressed ROS2 topic."""
        BOUNDARY = b"--frameboundary"

        self.send_response(200)
        self._cors_headers()
        self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frameboundary")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()

        evt = threading.Event()
        with cam_clients_lock:
            cam_clients.append(evt)

        print(f"[cam]  MJPEG client connected")

        try:
            last_frame = None
            while True:
                # Wait for a new frame or timeout (send last known frame as keepalive)
                evt.wait(timeout=1.0)
                evt.clear()

                with latest_frame_lock:
                    frame = latest_frame

                if frame is None:
                    continue

                # Skip if same frame (no new data)
                if frame is last_frame:
                    continue
                last_frame = frame

                self.wfile.write(BOUNDARY + b"\r\n")
                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                self.wfile.write(f"Content-Length: {len(frame)}\r\n".encode())
                self.wfile.write(b"\r\n")
                self.wfile.write(frame)
                self.wfile.write(b"\r\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with cam_clients_lock:
                if evt in cam_clients:
                    cam_clients.remove(evt)
            print(f"[cam]  MJPEG client disconnected")

    def _handle_snapshot(self):
        """Return a single JPEG frame."""
        with latest_frame_lock:
            frame = latest_frame

        if frame is None:
            self.send_response(503)
            self._cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"no frame available"}')
            return

        self.send_response(200)
        self._cors_headers()
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(frame)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(frame)

    def log_message(self, format, *args):
        if args and "404" in str(args[0]):
            super().log_message(format, *args)


class ThreadedHTTPServer(HTTPServer):
    """Handle each request in a new thread (needed for long-lived SSE/MJPEG connections)."""
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
    # Start camera subscriber in background
    cam_thread = threading.Thread(target=start_cam_subscriber, daemon=True)
    cam_thread.start()

    server = ThreadedHTTPServer((HOST, PORT), BridgeHandler)
    print(f"Edge Rescue bridge listening on http://{HOST}:{PORT}")
    print(f"  POST /goal        — send a mission prompt")
    print(f"  GET  /events      — SSE stream of plan/subtask updates")
    print(f"  GET  /cam0/stream — MJPEG video from /cam0/compressed")
    print(f"  GET  /cam0/snap   — single JPEG snapshot")
    print(f"Waiting for connections...\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
