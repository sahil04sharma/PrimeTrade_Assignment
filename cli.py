"""
CLI entry point for the Binance Futures Testnet trading bot.

Flag mode (scripted):
    python cli.py --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
    python cli.py --symbol BTCUSDT --side SELL --type LIMIT --quantity 0.001 --price 150000
    python cli.py --symbol BTCUSDT --side SELL --type STOP_LIMIT --quantity 0.001 --price 58000 --stop-price 59000

Interactive mode (menu + prompts):
    python cli.py
    python cli.py --interactive
"""

import argparse
import os
import sys
from pathlib import Path

from bot.client import BinanceClientError, BinanceFuturesTestnetClient
from bot.logging_config import setup_logger
from bot.orders import submit_order
from bot.validators import (
    ValidationError,
    validate_price,
    validate_quantity,
    validate_side,
    validate_stop_price,
    validate_symbol,
)

logger = setup_logger()

MENU = """
==================================================
  Binance Futures Demo Trading Bot
==================================================
  1) Place MARKET order
  2) Place LIMIT order
  3) Place STOP_LIMIT order
  4) Exit
--------------------------------------------------
"""


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
        description=(
            "Place MARKET, LIMIT, or STOP_LIMIT orders on Binance Futures Demo (USDT-M). "
            "Run with no flags (or --interactive) for the menu-driven UX."
        )
    )
    parser.add_argument(
        "-i", "--interactive", action="store_true",
        help="Launch interactive menu (default when no order flags are given)",
    )
    parser.add_argument("--symbol", required=False, help="Trading pair symbol, e.g. BTCUSDT")
    parser.add_argument("--side", required=False, choices=["BUY", "SELL", "buy", "sell"],
                         help="Order side")
    parser.add_argument(
        "--type",
        required=False,
        dest="order_type",
        choices=[
            "MARKET", "LIMIT", "STOP_LIMIT",
            "market", "limit", "stop_limit", "STOP-LIMIT", "stop-limit",
        ],
        help="Order type (MARKET, LIMIT, or STOP_LIMIT)",
    )
    parser.add_argument("--quantity", required=False, help="Order quantity")
    parser.add_argument("--price", required=False, default=None,
                         help="Limit price (required for LIMIT and STOP_LIMIT)")
    parser.add_argument("--stop-price", required=False, default=None, dest="stop_price",
                         help="Trigger/stop price (required for STOP_LIMIT)")
    return parser


def prompt_until_valid(label: str, validator, *extra_args, default: str = None):
    """
    Ask for a value repeatedly until the validator accepts it.
    Shows the ValidationError message and retries (enhanced CLI UX).
    """
    while True:
        suffix = f" [{default}]" if default else ""
        raw = input(f"{label}{suffix}: ").strip()
        if not raw and default is not None:
            raw = default
        try:
            return validator(raw, *extra_args)
        except ValidationError as exc:
            print(f"  ! {exc}  Please try again.")


def confirm(prompt: str = "Place this order?") -> bool:
    while True:
        answer = input(f"{prompt} [y/n]: ").strip().lower()
        if answer in {"y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("  ! Enter y or n.")


def collect_order_params(order_type: str) -> dict:
    """Interactive prompts for one order; reuses bot.validators for messages."""
    print(f"\n--- {order_type} order ---")
    symbol = prompt_until_valid("Symbol", validate_symbol, default="BTCUSDT")
    side = prompt_until_valid("Side (BUY/SELL)", validate_side)
    quantity = prompt_until_valid("Quantity", validate_quantity)

    price = None
    stop_price = None
    if order_type in {"LIMIT", "STOP_LIMIT"}:
        price = prompt_until_valid("Limit price", validate_price, order_type)
    if order_type == "STOP_LIMIT":
        stop_price = prompt_until_valid("Stop/trigger price", validate_stop_price, order_type)

    return {
        "symbol": symbol,
        "side": side,
        "order_type": order_type,
        "quantity": quantity,
        "price": price,
        "stop_price": stop_price,
    }


def print_preview(params: dict) -> None:
    print("\nOrder preview")
    print("-" * 40)
    for key, value in params.items():
        if value is None:
            continue
        print(f"  {key:12s}: {value}")
    print("-" * 40)


def run_interactive(client: BinanceFuturesTestnetClient) -> None:
    """Menu loop: pick order type, prompt fields, confirm, submit."""
    type_by_choice = {
        "1": "MARKET",
        "2": "LIMIT",
        "3": "STOP_LIMIT",
    }

    while True:
        print(MENU)
        choice = input("Select option [1-4]: ").strip()
        if choice == "4" or choice.lower() in {"q", "quit", "exit"}:
            print("Goodbye.")
            return
        if choice not in type_by_choice:
            print("  ! Invalid option. Choose 1, 2, 3, or 4.")
            continue

        params = collect_order_params(type_by_choice[choice])
        print_preview(params)
        if not confirm():
            print("Cancelled.\n")
            continue

        result = submit_order(client=client, **params)
        print()
        print(result.summary())
        print()


def create_client() -> BinanceFuturesTestnetClient:
    api_key = os.environ.get("BINANCE_TESTNET_API_KEY")
    api_secret = os.environ.get("BINANCE_TESTNET_API_SECRET")
    return BinanceFuturesTestnetClient(api_key, api_secret)


def run_flag_mode(client: BinanceFuturesTestnetClient, args: argparse.Namespace) -> int:
    missing = [
        name for name, value in (
            ("--symbol", args.symbol),
            ("--side", args.side),
            ("--type", args.order_type),
            ("--quantity", args.quantity),
        ) if not value
    ]
    if missing:
        print(f"FAILURE: Missing required flags for non-interactive mode: {', '.join(missing)}")
        print("Tip: run `python cli.py` (no flags) for the interactive menu.")
        return 1

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
    return 0 if result.success else 1


def wants_interactive(args: argparse.Namespace) -> bool:
    if args.interactive:
        return True
    # No order flags provided -> default to menu UX
    return not any([args.symbol, args.side, args.order_type, args.quantity])


def main():
    load_env_file()
    parser = build_parser()
    args = parser.parse_args()

    try:
        client = create_client()
    except BinanceClientError as exc:
        logger.error("Startup failed: %s", exc)
        print(f"FAILURE: {exc}")
        sys.exit(1)

    if wants_interactive(args):
        run_interactive(client)
        return

    exit_code = run_flag_mode(client, args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
