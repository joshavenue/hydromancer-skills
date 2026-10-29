# Hydromancer Hyperliquid skill

An [Agent Skill](https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills) that teaches coding agents (Claude Code, Codex, Cursor and others that read `SKILL.md`) how to use Hyperliquid data from [Hydromancer](https://hydromancer.xyz):

- **REST API** (`POST /info`): positions for one or up to 1,000 wallets per request, orders, fills with cursor paging, funding, liquidations, oracle and mark prices, candles, vaults, staking, builder-code data, PnL, HIP-3 and HIP-4 markets.
- **WebSocket streams**: trades, fills, liquidations, BBO, L2 and L4 order books, TP/SL, funding, user and builder events, with session replay after reconnects.
- **Reservoir**: free historical Hyperliquid data (fills, 1-second candles, daily snapshots, 1-minute L2 books) as Parquet on AWS S3, requester-pays.

## Install

Claude Code, as a plugin:

```
/plugin marketplace add joshavenue/hydromancer-skills
/plugin install hydromancer-hyperliquid@hydromancer
```

Or as a personal skill:

```bash
git clone https://github.com/joshavenue/hydromancer-skills.git ~/.claude/skills/hydromancer-hyperliquid
```

Or per project: copy the folder into `.claude/skills/hydromancer-hyperliquid/`. Other agents: point them at `SKILL.md`; the `references/` files load on demand.

## Requirements

- A Hydromancer API key in `HYDROMANCER_API_KEY` ([plans and onboarding](https://docs.hydromancer.xyz/readme/get-api-keys); free access for public goods and early-stage builder-code apps: [details](https://docs.hydromancer.xyz/readme/hydromancer-for-early-stage-teams)).
- Python 3.9+ for `scripts/hydromancer.py` (standard library only). `scripts/stream_trades.py` needs the `websockets` package, version 13 or later.
- AWS credentials for Reservoir (the bucket is requester-pays; no Hydromancer key needed).

## Contents

```
SKILL.md                  overview, essentials and pitfalls (loaded first)
references/rest-api.md    request shape, tested examples, full endpoint catalog
references/websocket.md   messages, heartbeat, sessions and replay, limits, channel catalog
references/reservoir.md   S3 paths, AWS CLI and DuckDB access, cost control
references/rate-limits.md weights, windowed endpoints, 429 handling
references/recipes.md     whale tracking, full trade history, builder revenue, liquidations, local L4 book, HIP-4, backtesting
scripts/hydromancer.py    REST helper: info, positions, fills (cursor paging), liquidations, usage
scripts/stream_trades.py  WebSocket trades stream with heartbeat handling
```

## Links

[Docs](https://docs.hydromancer.xyz) · [llms.txt](https://docs.hydromancer.xyz/llms.txt) · [Python SDK](https://github.com/hydromancerxyz/hydromancer-sdk) · [Reservoir](https://docs.hydromancer.xyz/reservoir) · [Discord](https://discord.gg/xfAWcSygQT)

## License

MIT
