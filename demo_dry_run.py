"""
Dry-run demo (NO real API calls).

Generates sample log entries and console output for MARKET, LIMIT, and
STOP_LIMIT orders by mocking the Binance client's place_order method. This is
useful for:
  - Verifying the logging/validation/formatting pipeline works end-to-end
  - Producing example log files when real testnet credentials aren't
    available yet (e.g. for a quick review before wiring up real keys)

To place REAL orders on the testnet, use cli.py instead with valid
BINANCE_TESTNET_API_KEY / BINANCE_TESTNET_API_SECRET env vars set.
"""

import itertools
from unittest.mock import patch

from bot.client import BinanceFuturesTestnetClient
from bot.logging_config import setup_logger
from bot.orders import submit_order

logger = setup_logger()
_order_id_counter = itertools.count(100001)


def fake_place_order(self, symbol, side, order_type, quantity, price=None, stop_price=None):
    """Simulates a Binance futures order response without any network call."""
    order_id = next(_order_id_counter)
    if order_type == "STOP_LIMIT":
        fake_response = {
            "algoId": order_id,
            "symbol": symbol,
            "algoStatus": "NEW",
            "side": side,
            "type": "STOP",
            "executedQty": "0",
            "price": str(price),
            "stopPrice": str(stop_price),
        }
    else:
        fake_response = {
            "orderId": order_id,
            "symbol": symbol,
            "status": "FILLED" if order_type == "MARKET" else "NEW",
            "side": side,
            "type": order_type,
            "executedQty": str(quantity) if order_type == "MARKET" else "0",
            "avgPrice": str(price) if price else "60123.50",
        }
    logger.info("Submitting order request: %s", {
        "symbol": symbol, "side": side, "type": order_type,
        "quantity": quantity, "price": price, "stop_price": stop_price,
    })
    logger.info("Order response: %s", fake_response)
    return fake_response


def run_demo():
    with patch.object(BinanceFuturesTestnetClient, "place_order", new=fake_place_order):
        # Bypass real credential check for the demo
        client = BinanceFuturesTestnetClient.__new__(BinanceFuturesTestnetClient)

        print("\n--- DEMO: MARKET order (BUY) ---\n")
        result = submit_order(client, symbol="BTCUSDT", side="BUY",
                               order_type="MARKET", quantity=0.01)
        print(result.summary())

        print("\n--- DEMO: LIMIT order (SELL) ---\n")
        result = submit_order(client, symbol="BTCUSDT", side="SELL",
                               order_type="LIMIT", quantity=0.01, price=65000)
        print(result.summary())

        print("\n--- DEMO: STOP_LIMIT order (SELL) ---\n")
        result = submit_order(
            client,
            symbol="BTCUSDT",
            side="SELL",
            order_type="STOP_LIMIT",
            quantity=0.01,
            price=58000,
            stop_price=59000,
        )
        print(result.summary())

    print("\nSample logs written to logs/trading_bot.log\n")


if __name__ == "__main__":
    run_demo()
