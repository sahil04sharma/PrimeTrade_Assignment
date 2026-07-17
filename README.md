# Binance Futures Testnet Trading Bot

A simplified CLI trading bot that places MARKET and LIMIT orders on Binance
Futures Testnet (USDT-M), with structured code, input validation, and
logging.

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
```

## Setup

1. **Create a Futures Testnet account** at https://testnet.binancefuture.com
   and generate an API key + secret from the site.

2. **Install dependencies** (Python 3.9+):
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your API credentials** as environment variables:
   ```bash
   export BINANCE_TESTNET_API_KEY="your_key_here"
   export BINANCE_TESTNET_API_SECRET="your_secret_here"
   ```
   (On Windows PowerShell: `$env:BINANCE_TESTNET_API_KEY="..."`)

## Usage

### Place a MARKET order
```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
```

### Place a LIMIT order
```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 65000
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

## Demo mode (no API keys needed)

`demo_dry_run.py` mocks the Binance client layer so you can see the full
request → log → response → summary pipeline without valid testnet
credentials:

```bash
python demo_dry_run.py
```

This is what was used to generate the sample log entries included in this
submission (`logs/trading_bot.log`) for one MARKET and one LIMIT order.

## Error handling

- **Invalid input** (bad symbol format, non-numeric quantity/price, missing
  price on a LIMIT order, invalid side/type) is caught by `bot/validators.py`
  before any API call is made, and reported clearly without a stack trace.
- **API errors** (e.g. insufficient testnet balance, invalid symbol on
  Binance's side, bad precision) are caught around the `futures_create_order`
  call and surfaced as a clean failure message.
- **Network failures** (timeouts, connection errors) are caught by the same
  handler and logged with a full traceback in the log file for debugging,
  while the console only shows a short message.

## Assumptions

- Orders use `timeInForce=GTC` for LIMIT orders (not exposed as a flag, to
  keep the CLI surface small per the "simplified" scope of this task).
- Quantity/price precision (tick size, lot size) is left to Binance's own
  validation on the testnet; the app does not pre-round to each symbol's
  exchange filters.
- Only USDT-M futures are targeted, per the task spec.
- Credentials are read from environment variables rather than passed as CLI
  flags, to avoid leaking secrets into shell history.

## Bonus not implemented

Given the ~60 minute scope, the bonus items (Stop-Limit/OCO/TWAP/Grid,
richer interactive CLI UX, lightweight UI) were left out in favor of a
clean, correct, well-tested core. Happy to discuss extending any of these
in an interview.
