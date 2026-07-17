# Binance Futures Testnet Trading Bot

A simplified CLI trading bot that places MARKET and LIMIT orders on Binance
Futures Testnet / Demo Trading (USDT-M), with structured code, input
validation, and logging.

## Project Structure

```
trading_bot/
  bot/
    __init__.py
    client.py          # Binance client wrapper (API layer)
    orders.py          # Order placement / result formatting logic
    validators.py       # Input validation
    logging_config.py   # Logging setup
  cli.py                # CLI entry point (command layer)
  demo_dry_run.py        # Mocked demo - no real API calls, no keys needed
  logs/
    trading_bot.log       # Generated at runtime
  README.md
  requirements.txt
  .env.example
```

## Setup

### 1. Get Demo / Testnet API credentials

> **Note:** Binance migrated Futures Testnet off `testnet.binancefuture.com`
> to **Demo Trading**. API base URL used by this bot:
> `https://demo-fapi.binance.com` (via `python-binance` `Client(..., demo=True)`).

1. Open **https://demo.binance.com** (incognito is fine).
2. Log in (GitHub login works; use the Demo Trading account, not live keys).
3. Profile → **API Management** / **Demo Trading API** → **Create API**
   (System Generated is fine).
4. Copy the **API Key** and **Secret Key**. Save the secret now — it is shown once.
5. Optional: open the Futures demo UI and confirm you have a USDT demo balance.
   If balance is **0**, use the **Faucet** in the Assets panel on
   **https://demo.binance.com/en/futures** → select **USDT** → **Add Asset**
   (credits ~1,000 USDT demo funds).

### 2. Install dependencies (Python 3.9+)

```bash
pip install -r requirements.txt
```

### 3. Set API credentials (environment variables — never hardcode)

**Windows PowerShell (current session only):**
```powershell
$env:BINANCE_TESTNET_API_KEY="your_key_here"
$env:BINANCE_TESTNET_API_SECRET="your_secret_here"
```

**macOS / Linux:**
```bash
export BINANCE_TESTNET_API_KEY="your_key_here"
export BINANCE_TESTNET_API_SECRET="your_secret_here"
```

Or copy `.env.example` → `.env` and load it yourself; `.env` is gitignored.

## Usage

### Place a MARKET order
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
```

### Place a LIMIT order
(Use a price far from market so it rests as `NEW` and does not fill immediately.)
```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 150000
```

### Arguments
| Flag | Required | Notes |
|---|---|---|
| `--symbol` | yes | e.g. `BTCUSDT` |
| `--side` | yes | `BUY` or `SELL` (case-insensitive) |
| `--type` | yes | `MARKET` or `LIMIT` (case-insensitive) |
| `--quantity` | yes | must be > 0 |
| `--price` | only for LIMIT | must be > 0 |

Every run prints an order request summary, the API response (orderId,
status, executedQty, avgPrice), and a success/failure message. All requests,
responses, and errors are also written to `logs/trading_bot.log`.

## Dry-run demo (no API keys needed)

`demo_dry_run.py` mocks the Binance client layer so you can see the full
request → log → response → summary pipeline without credentials:

```bash
python demo_dry_run.py
```

For the submission, prefer real demo-API log lines (real `orderId` values)
from running `cli.py` after setting credentials.

## Error handling

- **Invalid input** (bad symbol format, non-numeric quantity/price, missing
  price on a LIMIT order, invalid side/type) is caught by `bot/validators.py`
  before any API call is made, and reported clearly without a stack trace.
- **API errors** (e.g. insufficient demo balance, invalid symbol on
  Binance's side, bad precision) are caught around the `futures_create_order`
  call and surfaced as a clean failure message.
- **Network failures** (timeouts, connection errors) are caught by the same
  handler and logged with a full traceback in the log file for debugging,
  while the console only shows a short message.

## Assumptions

- Binance's current Futures "testnet" is Demo Trading at
  `https://demo-fapi.binance.com` (the old `testnet.binancefuture.com` host
  is deprecated). Env var names keep the `BINANCE_TESTNET_*` prefix from the
  assignment for familiarity.
- Orders use `timeInForce=GTC` for LIMIT orders (not exposed as a flag, to
  keep the CLI surface small per the "simplified" scope of this task).
- Quantity/price precision (tick size, lot size) is left to Binance's own
  validation; the app does not pre-round to each symbol's exchange filters.
- Only USDT-M futures are targeted, per the task spec.
- Credentials are read from environment variables rather than passed as CLI
  flags, to avoid leaking secrets into shell history / git.

## Bonus not implemented

Given the ~60 minute scope, the bonus items (Stop-Limit/OCO/TWAP/Grid,
richer interactive CLI UX, lightweight UI) were left out in favor of a
clean, correct core. Happy to discuss extending any of these in an interview.
