"""
Order placement logic - sits between the CLI and the Binance client.

Responsible for validating input, formatting a clear request summary,
invoking the client, and formatting the response for display. Keeping
this separate from cli.py means the same logic could be reused by a
future web UI or test suite without touching argument parsing.
"""

import logging

from .client import BinanceClientError, BinanceFuturesTestnetClient
from .validators import ValidationError, validate_order_params

logger = logging.getLogger("trading_bot")


class OrderResult:
    """Simple container for a completed (or failed) order attempt."""

    def __init__(self, success: bool, request: dict, response: dict = None, error: str = None):
        self.success = success
        self.request = request
        self.response = response
        self.error = error

    def summary(self) -> str:
        lines = ["=" * 50, "ORDER REQUEST", "=" * 50]
        for key, value in self.request.items():
            lines.append(f"  {key:12s}: {value}")

        lines.append("")
        if self.success:
            lines.append("=" * 50)
            lines.append("ORDER RESPONSE")
            lines.append("=" * 50)
            lines.append(f"  orderId      : {self.response.get('orderId')}")
            lines.append(f"  status       : {self.response.get('status')}")
            lines.append(f"  executedQty  : {self.response.get('executedQty')}")
            avg_price = self.response.get("avgPrice")
            if avg_price is not None:
                lines.append(f"  avgPrice     : {avg_price}")
            lines.append("")
            lines.append("SUCCESS: Order placed successfully.")
        else:
            lines.append("FAILURE: " + str(self.error))

        return "\n".join(lines)


def submit_order(
    client: BinanceFuturesTestnetClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity,
    price=None,
) -> OrderResult:
    """
    Validate inputs, submit the order via the client, and return an
    OrderResult describing the outcome. Never raises - all failure modes
    (validation, API, network) are captured in the returned OrderResult
    so the CLI layer can decide how to present/exit.
    """
    try:
        clean = validate_order_params(symbol, side, order_type, quantity, price)
    except ValidationError as exc:
        logger.warning("Validation failed: %s", exc)
        return OrderResult(
            success=False,
            request={
                "symbol": symbol,
                "side": side,
                "order_type": order_type,
                "quantity": quantity,
                "price": price,
            },
            error=f"Invalid input - {exc}",
        )

    request_summary = {
        "symbol": clean["symbol"],
        "side": clean["side"],
        "order_type": clean["order_type"],
        "quantity": clean["quantity"],
        "price": clean["price"] if clean["price"] is not None else "N/A (market order)",
    }

    try:
        response = client.place_order(
            symbol=clean["symbol"],
            side=clean["side"],
            order_type=clean["order_type"],
            quantity=clean["quantity"],
            price=clean["price"],
        )
        return OrderResult(success=True, request=request_summary, response=response)
    except BinanceClientError as exc:
        return OrderResult(success=False, request=request_summary, error=str(exc))
