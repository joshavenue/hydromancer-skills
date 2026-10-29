# Reservoir: historical Hyperliquid data on S3

Free archive of Hyperliquid exchange data, stored as Parquet in `s3://hydromancer-reservoir` (region `ap-northeast-1`). No Hydromancer API key is needed. The bucket is **requester-pays**: the data is free, but AWS bills your account for requests and transfer, so you need AWS credentials.

Docs: https://docs.hydromancer.xyz/reservoir · schemas: [fills](https://docs.hydromancer.xyz/reservoir/schema-reference/fills), [candles](https://docs.hydromancer.xyz/reservoir/schema-reference/candles), [snapshots](https://docs.hydromancer.xyz/reservoir/schema-reference/snapshots), [orderbook](https://docs.hydromancer.xyz/reservoir/schema-reference/orderbook)

## Datasets (Hyperliquid core markets)

| Dataset | Path |
|---|---|
| All perp fills | `by_dex/hyperliquid/fills/perp/all/date=YYYY-MM-DD/` |
| Liquidations | `by_dex/hyperliquid/fills/perp/liquidations/date=YYYY-MM-DD/` |
| ADL | `by_dex/hyperliquid/fills/perp/adl/date=YYYY-MM-DD/` |
| Builder fills | `by_dex/hyperliquid/fills/perp/builder_fills/date=YYYY-MM-DD/` |
| TWAP fills | `by_dex/hyperliquid/fills/perp/twap_fills/date=YYYY-MM-DD/` |
| Spot fills | `global/fills/spot/all/date=YYYY-MM-DD/` |
| 1-second candles | `by_dex/hyperliquid/candles/1s/date=YYYY-MM-DD/` |
| Perp position snapshots (daily) | `by_dex/hyperliquid/snapshots/perp/date=YYYY-MM-DD/` |
| Spot holdings snapshots (daily) | `global/snapshots/spot/date=YYYY-MM-DD/` |
| Account values (daily) | `global/snapshots/account_values/date=YYYY-MM-DD/` |
| L2 order book, 20 levels, 1-minute | `by_dex/hyperliquid/orderbook/1m/{asset_class}/date=YYYY-MM-DD/{coin}.parquet` (see the orderbook schema page for `asset_class` values) |

HIP-3 DEXs have their own folders under `by_dex/<dex>/`; see the per-DEX pages in the docs. Inside Reservoir, HIP-3 coin names don't carry the `dex:` prefix; the path's `<dex>` segment identifies the DEX. Sub-datasets (liquidations, ADL…) only have files for dates with events. Check the docs for current coverage dates before assuming a range exists.

## Access

AWS CLI (always pass `--request-payer requester`):

```bash
aws s3 ls s3://hydromancer-reservoir/by_dex/ --request-payer requester
aws s3 cp s3://hydromancer-reservoir/by_dex/hyperliquid/fills/perp/liquidations/date=2026-10-18/fills.parquet \
  ./liquidations-2026-10-18.parquet --request-payer requester
```

DuckDB (reads only the columns and row groups a query needs):

```sql
INSTALL httpfs; LOAD httpfs;
CREATE SECRET (TYPE s3, PROVIDER credential_chain, REGION 'ap-northeast-1');
SET s3_requester_pays = true;

-- BTC fills for one day
SELECT timestamp, side, price, size, direction, address
FROM read_parquet('s3://hydromancer-reservoir/by_dex/hyperliquid/fills/perp/all/date=2026-03-22/fills.parquet')
WHERE coin = 'BTC'
ORDER BY timestamp;

-- 1-minute candles built from 1-second candles
SELECT time_bucket(INTERVAL '1 minute', timestamp) AS minute,
       first(open) AS open, max(high) AS high, min(low) AS low, last(close) AS close,
       sum(volume) AS volume, sum(trade_count) AS trades
FROM read_parquet('s3://hydromancer-reservoir/by_dex/hyperliquid/candles/1s/date=2026-03-22/candles.parquet')
WHERE coin = 'BTC'
GROUP BY minute ORDER BY minute;

-- Largest BTC positions in a daily snapshot
SELECT user, size, notional, entry_price, leverage, leverage_type
FROM read_parquet('s3://hydromancer-reservoir/by_dex/hyperliquid/snapshots/perp/date=2026-03-22/*.parquet')
WHERE market = 'BTC'
ORDER BY abs(size) DESC LIMIT 10;
```

The queries come from the Reservoir docs. `SET s3_requester_pays = true` and the secret syntax were checked against DuckDB 1.4.5; the queries themselves need your AWS credentials to run.

## Cost control

- A wildcard path reads (and bills) every file it matches. Keep date ranges tight and select only needed columns.
- A daily snapshot isn't necessarily the daily close; the file name gives the block and time.
- Prefer `aws s3 sync` with `--include` patterns over repeated full scans when you need many days locally.
