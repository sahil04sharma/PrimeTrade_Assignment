"""
CLI entry point for the Binance Futures Testnet trading bot.

Usage examples:
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.01
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.01 --price 60000
"""

import argparse
import os
import sys

from bot.client import BinanceClientError, BinanceFuturesTestnetClient
from bot.logging_config import setup_logger
from bot.orders import submit_order

logger = setup_logger()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Place MARKET or LIMIT orders on Binance Futures Testnet (USDT-M)."
    )
    parser.add_argument("--symbol", required=True, help="Trading pair symbol, e.g. BTCUSDT")
    parser.add_argument("--side", required=True, choices=["BUY", "SELL", "buy", "sell"],
                         help="Order side")
    parser.add_argument("--type", required=True, dest="order_type",
                         choices=["MARKET", "LIMIT", "market", "limit"],
                         help="Order type")
    parser.add_argument("--quantity", required=True, help="Order quantity")
    parser.add_argument("--price", required=False, default=None,
                         help="Limit price (required for LIMIT orders)")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    api_key = os.environ.get("BINANCE_TESTNET_API_KEY")
    api_secret = os.environ.get("BINANCE_TESTNET_API_SECRET")

    try:
        client = BinanceFuturesTestnetClient(api_key, api_secret)
    except BinanceClientError as exc:
        logger.error("Startup failed: %s", exc)
        print(f"❌ FAILURE: {exc}")
        sys.exit(1)

    result = submit_order(
        client=client,
        symbol=args.symbol,
        side=args.side,
        order_type=args.order_type,
        quantity=args.quantity,
        price=args.price,
    )

    print(result.summary())

    if not result.success:
        sys.exit(1)


if __name__ == "__main__":
    main()
