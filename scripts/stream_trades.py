#!/usr/bin/env python3
"""Stream live Hyperliquid trades from Hydromancer's WebSocket.

  pip install 'websockets>=13'
  export HYDROMANCER_API_KEY=...
  python stream_trades.py BTC ETH            # prints trades; Ctrl+C to stop
"""
import asyncio
import json
import os
import sys

import websockets

URL = "wss://api.hydromancer.xyz/ws?token={key}"


async def main(coins, max_messages=None):
    key = os.environ.get("HYDROMANCER_API_KEY")
    if not key:
        sys.exit("Set HYDROMANCER_API_KEY first (https://docs.hydromancer.xyz/readme/get-api-keys)")
    # The server sends a JSON {"type": "ping"} every 60 s; reply with a pong or it drops the connection.
    async with websockets.connect(URL.format(key=key), max_size=None,
                                  user_agent_header="hydromancer-skill/0.1") as ws:
        await ws.send(json.dumps({
            "method": "subscribe",
            "requestId": "trades-1",
            "subscription": {"type": "trades", "coins": coins},
        }))
        seen = 0
        async for raw in ws:
            msg = json.loads(raw)
            if msg.get("type") == "ping":
                await ws.send(json.dumps({"type": "pong"}))
                continue
            kind = msg.get("type")
            if kind in ("connected", "subscriptionUpdate"):
                print("control:", json.dumps(msg), file=sys.stderr)
                if kind == "subscriptionUpdate" and msg.get("failed"):
                    sys.exit(f"subscription failed: {json.dumps(msg)}")
                continue
            if kind == "error":
                sys.exit(f"server error: {json.dumps(msg)}")
            if kind != "trades":
                continue  # ignore other message types (the protocol adds new ones over time)
            print(json.dumps(msg))
            seen += 1
            if max_messages and seen >= max_messages:
                break


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or ["BTC"]))
