#!/usr/bin/env python3
"""
Edge Rescue — WebSocket bridge server.
Speaks the rosbridge v2 protocol just enough for roslibjs to connect,
subscribe, and publish string topics.

Run:  python3 bridge.py
Then the frontend at ws://<this-ip>:9090 will connect.
"""

import asyncio
import json
from websockets.asyncio.server import serve

# ---- State ----
subscribers = {}   # topic -> set of websocket connections
clients = set()

# ---- Rosbridge-compatible message handling ----

async def handle_message(ws, raw):
    """Parse a rosbridge JSON message and route it."""
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        print(f"[warn] non-JSON message: {raw[:200]}")
        return

    op = msg.get("op")

    if op == "subscribe":
        topic = msg.get("topic", "")
        if topic not in subscribers:
            subscribers[topic] = set()
        subscribers[topic].add(ws)
        print(f"[sub]  {topic} (now {len(subscribers[topic])} listener(s))")

    elif op == "unsubscribe":
        topic = msg.get("topic", "")
        if topic in subscribers:
            subscribers[topic].discard(ws)

    elif op == "publish":
        topic = msg.get("topic", "")
        data = msg.get("msg", {})
        print(f"[pub]  {topic}: {json.dumps(data)[:200]}")
        await on_publish(ws, topic, data)

    elif op == "advertise":
        # roslibjs sends this before publishing; just acknowledge
        pass

    else:
        print(f"[info] unhandled op: {op}")


async def broadcast(topic, data):
    """Send a rosbridge publish message to all subscribers of a topic."""
    if topic not in subscribers:
        return
    msg = json.dumps({"op": "publish", "topic": topic, "msg": data})
    dead = set()
    for ws in subscribers[topic]:
        try:
            await ws.send(msg)
        except Exception:
            dead.add(ws)
    subscribers[topic] -= dead


# ---- Application logic ----
# This is where you hook in the LLM and arm control.

async def on_publish(ws, topic, data):
    """Handle incoming publishes from the frontend."""

    if topic == "/mission/goal":
        prompt = data.get("data", "")
        print(f"\n{'='*50}")
        print(f"  MISSION GOAL: {prompt}")
        print(f"{'='*50}\n")

        # --- PLACEHOLDER: replace with actual LLM call ---
        # For now, generate a dummy plan to prove the loop works.
        plan = [
            f"Locate objects for: {prompt}",
            "Pick up first block",
            "Place block at target position",
            "Verify placement in simulation",
            "Report result"
        ]

        # Send the plan back to the frontend
        await broadcast("/plan/full", {"data": json.dumps(plan)})

        # Simulate stepping through subtasks
        for i, step in enumerate(plan):
            await broadcast("/subtask/current", {"data": step})
            print(f"  [{i+1}/{len(plan)}] {step}")
            await asyncio.sleep(1)

        await broadcast("/subtask/current", {"data": "Done."})
        print(f"  Mission complete.\n")


# ---- WebSocket server ----

async def handler(ws):
    clients.add(ws)
    addr = ws.remote_address
    print(f"[conn] {addr[0]}:{addr[1]} connected ({len(clients)} total)")

    try:
        async for raw in ws:
            await handle_message(ws, raw)
    except Exception:
        pass
    finally:
        clients.discard(ws)
        # Clean up subscriptions
        for topic in subscribers:
            subscribers[topic].discard(ws)
        print(f"[disc] {addr[0]}:{addr[1]} disconnected ({len(clients)} total)")


async def main():
    host = "0.0.0.0"
    port = 9090
    print(f"Edge Rescue bridge listening on ws://{host}:{port}")
    print(f"Waiting for frontend connections...\n")
    async with serve(handler, host, port):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
