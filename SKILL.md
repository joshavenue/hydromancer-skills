---
name: hydromancer-hyperliquid
description: >
  Hyperliquid market and account data through the Hydromancer API: REST (POST /info) for
  positions, fills, funding, liquidations, oracle prices, candles, vaults, staking,
  builder-code fills and HIP-3 / HIP-4 markets; WebSocket streams for trades, fills,
  liquidations, BBO, L2 and L4 order books with session replay; and Reservoir, a free
  requester-pays S3 archive of historical Hyperliquid data in Parquet.
  Use when building Hyperliquid trading apps, bots, dashboards, copy-trading, tax tools,
  backtests or research, or when the task mentions Hyperliquid, HyperCore, HIP-3, HIP-4,
  builder codes, whale tracking, order book data, liquidations, funding history,
  wallet trade history, or Hydromancer.
license: MIT
---

# Hyperliquid data via Hydromancer

Hydromancer is a data provider for teams building on Hyperliquid. It serves HyperCore exchange data over a REST API, WebSocket streams and Reservoir, a historical archive on AWS S3.

| Need | Use | Reference |
|---|---|---|
| Account state, positions (one or up to 1,000 wallets per request), orders, fills, funding, ledger, PnL | REST `POST /info` | [references/rest-api.md](references/rest-api.md) |
| Market data: candles, oracle / mark / mid prices, open interest, liquidations, L2 / L4 snapshots, market-wide position snapshots | REST `POST /info` | [references/rest-api.md](references/rest-api.md) |
| HIP-4 prediction-market outcomes and HIP-3 perp DEXs | REST + WebSocket | [references/rest-api.md](references/rest-api.md) |
| Live trades, fills, liquidations, BBO, L2 / L4 order books, TP/SL, funding, user and builder events | WebSocket `wss://api.hydromancer.xyz/ws` | [references/websocket.md](references/websocket.md) |
| Long history for backtests (fills, 1-second candles, daily snapshots, 1-minute L2 books) | Reservoir (S3, no API key) | [references/reservoir.md](references/reservoir.md) |
| Budgets, endpoint weights, 429 handling | — | [references/rate-limits.md](references/rate-limits.md) |
| Task recipes (whale tracking, full trade history, builder revenue, liquidation feed, local L4 book) | — | [references/recipes.md](references/recipes.md) |

## Essentials

- **Auth.** REST: `Authorization: Bearer $HYDROMANCER_API_KEY`. WebSocket: `?token=$HYDROMANCER_API_KEY` on the URL. Read the key from the environment; never print it or commit it.
- **Base URLs.** Mainnet `https://api.hydromancer.xyz`, testnet `https://api-testnet.hydromancer.xyz` (WebSocket: same hosts with `wss://…/ws`). Testnet APIs are included in the Starter, Growth and Scale plans; if testnet returns 401 with your mainnet key, ask Hydromancer to enable testnet on it.
- **One REST endpoint.** Every query is `POST /info` with a JSON body whose `type` picks the operation, for example `{"type": "clearinghouseState", "user": "0x…"}`. Check the endpoint's own docs page for its fields; Hydromancer adds endpoints and fields that the public Hyperliquid API doesn't have (batch queries, builder data, market-wide snapshots, PnL, HIP-4).
- **Set a User-Agent.** Requests sent with Python's default `Python-urllib` agent are rejected with HTTP 403 and `error code: 1010`. Send your own `User-Agent` header (`requests` and the SDK already do).
- **Weights.** Each plan has a per-minute weight budget (5,000 / 20,000 / 50,000). Most requests cost 2; heavy history and analytics endpoints cost more. Honor `Retry-After` on HTTP 429. See [rate-limits.md](references/rate-limits.md).
- **Docs for agents.** Every docs page has a Markdown version (append `.md`), and the full index is at https://docs.hydromancer.xyz/llms.txt. Fetch the specific endpoint page before writing code against it.

## Quick start

```bash
export HYDROMANCER_API_KEY=...        # https://docs.hydromancer.xyz/readme/get-api-keys
python scripts/hydromancer.py info '{"type": "clearinghouseState", "user": "0xdfc24b077bc1425ad1dea75bcb6f8158e10df303"}'
python scripts/hydromancer.py positions 0xABC... 0xDEF...      # batchClearinghouseStates
python scripts/hydromancer.py fills 0xABC... --hours 24        # userFillsByTime, follows the cursor
python scripts/hydromancer.py liquidations --coin BTC --hours 6
pip install 'websockets>=13' && python scripts/stream_trades.py BTC  # live trades
```

`scripts/hydromancer.py` uses only the Python standard library. `scripts/stream_trades.py` needs `websockets>=13`.

For order book streaming in Python, the official SDK (`pip install git+https://github.com/hydromancerxyz/hydromancer-sdk.git`) maintains local L2 / L4 books for you; it reads `HYDROMANCER_API_KEY` from the environment.

## Pitfalls

- **Fill history is count-limited on the public API, not on Reservoir.** For a wallet's complete history, page `userFillsByTime` with its cursor, or read Reservoir fills (see [recipes.md](references/recipes.md)).
- **`userFillsByTime` pages with a cursor.** Pass `cursor` = `"<time>_<txIndex>"` from the last record of the previous page; `startTime` is ignored when `cursor` is set.
- **Batch response shape.** `batchClearinghouseStates` returns `{"successful_states": …, "failed_wallets": …}`. Up to 1,000 users per request, 100 with `"dex": "ALL_DEXES"`.
- **WebSocket heartbeats are JSON.** The server sends `{"type": "ping"}` every 60 seconds; reply `{"type": "pong"}` or the connection is closed. Protocol-level ping handling in your library is not enough.
- **Resume, don't resubscribe.** Save `sessionId` from the `connected` message and the `cursor` from every message. On reconnect, add `&sessionId=<id>&cursor=<last cursor>` to the URL: the server restores your subscriptions and replays what you missed. On `resync required`, reconnect without both and rebuild from a REST snapshot.
- **Replay windows vary by channel.** Replay covers up to 3 minutes for `l4BookUpdates`, 5 minutes for order updates and 15 minutes for other replayable channels (30 seconds where only the in-memory cache serves them). `bbo`, `l2Book`, `allActiveAssetCtx` and `setOracleUpdates` are live-only.
- **Market-wide snapshots are binary.** `perpSnapshots`, `spotSnapshots`, `accountValueSnapshots` and similar return zstd-compressed MessagePack (`pip install zstandard msgpack`) and have their own limit of 5 requests per 10 minutes.
- **Reservoir is requester-pays.** The data is free, but AWS bills your account for requests and transfer. Narrow paths by date and select only the columns you need.
- **HIP-3 coins are prefixed** with the DEX name, for example `"xyz:JPY"`, in the API and in Reservoir fills, candles and snapshots. Only Reservoir order-book file names drop the prefix.
- **A 200 with `[]` or `null` usually means no data for that input, not an error.** Some docs examples use old timestamps (2009, 2023) or the zero address and come back empty; use a recent window and an active wallet. Some requests are snapshots of current state (`registeredOutcomesSnapshot` with old `outcome_ids` returns 500 "No outcome snapshots found"; omit the ids to get every active outcome).
- **Hyperliquid-named WebSocket channels can differ in shape.** `userFills` takes an `addresses` list, not Hyperliquid's single `user`; `l2Book` and `trades` also accept a `coins` list. Check the channel's docs page before porting code from Hyperliquid's socket.
