"""
CLI entry point for the Binance Futures Testnet trading bot.

Usage examples:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 150000
    python cli.py --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.001 --price 58000 --stop-price 59000
"""

import argparse
import os
import sys
from pathlib import Path

from bot.client import BinanceClientError, BinanceFuturesTestnetClient
from bot.logging_config import setup_logger
from bot.orders import submit_order

logger = setup_logger()


def load_env_file(path: str = ".env") -> None:
    """Load KEY=VALUE pairs from a local .env file into os.environ."""
    env_path = Path(__file__).resolve().parent / path
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Place MARKET, LIMIT, or STOP_LIMIT orders on Binance Futures Demo (USDT-M)."
    )
    parser.add_argument("--symbol", required=True, help="Trading pair symbol, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL", "buy", "sell"],
                         help="Order side")
    parser.add_argument(
        "--type",
        required=True,
        dest="order_type",
        choices=[
            "MARKET", "LIMIT", "STOP_LIMIT",
            "market", "limit", "stop_limit", "STOP-LIMIT", "stop-limit",
        ],
        help="Order type (MARKET, LIMIT, or STOP_LIMIT)",
    )
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument("--price", required=False, default=None,
                         help="Limit price (required for LIMIT and STOP_LIMIT)")
    parser.add_argument("--stop-price", required=False, default=None, dest="stop_price",
                         help="Trigger/stop price (required for STOP_LIMIT)")
    return parser


def main():
    load_env_file()
    parser = build_parser()
    args = parser.parse_args()

    api_key = os.environ.get("BINANCE_TESTNET_API_KEY")
    api_secret = os.environ.get("BINANCE_TESTNET_API_SECRET")

    try:
        client = BinanceFuturesTestnetClient(api_key, api_secret)
    except BinanceClientError as exc:
        logger.error("Startup failed: %s", exc)
        print(f"FAILURE: {exc}")
        sys.exit(1)

    result = submit_order(
        client=client,
        symbol=args.symbol,
        side=args.side,
        order_type=args.order_type,
        quantity=args.quantity,
        price=args.price,
        stop_price=args.stop_price,
    )

    print(result.summary())

    if not result.success:
        sys.exit(1)


if __name__ == "__main__":
    main()
