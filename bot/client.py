"""
Thin wrapper around the Binance Futures Testnet client.

Isolating all direct SDK/API usage here means the rest of the app (CLI,
order logic) never talks to python-binance directly - it only depends on
this module's interface. That makes it easy to swap the SDK for raw REST
calls later, or to mock this layer entirely in tests.
"""

import logging

from binance import Client
from binance.exceptions import BinanceAPIException, BinanceOrderException, BinanceRequestException

logger = logging.getLogger("trading_bot")

# Assignment spec originally cited testnet.binancefuture.com. Binance has since
# migrated USDT-M Futures "testnet" to Demo Trading:
#   https://demo-fapi.binance.com
# python-binance >= 1.0.28 exposes this via Client(..., demo=True), which sets
# FUTURES_DEMO_URL. Using testnet=True still points at the deprecated host.
DEMO_FUTURES_BASE_URL = "https://demo-fapi.binance.com"


def _format_api_number(value):
    """Format numbers for Binance without scientific notation or 6-decimal truncation."""
    if isinstance(value, (int, float)):
        # Default "f" truncates to 6 decimals; ".15f" matches float64 precision.
        text = format(value, ".15f")
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text
    return value


class BinanceClientError(Exception):
    """Raised when the Binance client cannot be initialized or a call fails unexpectedly."""


class BinanceFuturesTestnetClient:
    """
    Wraps python-binance's Client, pinned to Binance Futures Demo Trading
    (the current replacement for Futures Testnet), and exposes only the
    operations this app needs.
    """

    def __init__(self, api_key: str, api_secret: str):
        if not api_key or not api_secret:
            raise BinanceClientError(
                "API key and secret are required. Set BINANCE_TESTNET_API_KEY and "
                "BINANCE_TESTNET_API_SECRET environment variables."
            )
        try:
            # demo=True routes futures calls to FUTURES_DEMO_URL
            # (https://demo-fapi.binance.com/fapi). Do NOT use testnet=True —
            # that still targets the deprecated testnet.binancefuture.com host.
            self._client = Client(api_key, api_secret, demo=True)
            # Explicit override keeps the endpoint correct even if a future
            # library release changes the bundled DEMO URL constant.
            self._client.FUTURES_DEMO_URL = DEMO_FUTURES_BASE_URL + "/fapi"
            self._client.FUTURES_URL = DEMO_FUTURES_BASE_URL + "/fapi"
        except Exception as exc:  # noqa: BLE001 - surface any init failure clearly
            logger.exception("Failed to initialize Binance client")
            raise BinanceClientError(f"Could not initialize Binance client: {exc}") from exc

    def place_order(self, symbol: str, side: str, order_type: str, quantity: float, price=None):
        """
        Place a MARKET or LIMIT order on Futures Testnet.

        Returns the raw order response dict from Binance on success.
        Raises BinanceClientError on any API, order, or network failure.
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": _format_api_number(quantity),
        }
        if order_type == "LIMIT":
            params["price"] = _format_api_number(price)
            params["timeInForce"] = "GTC"  # Good-Til-Canceled, required for LIMIT orders

        logger.info("Submitting order request: %s", params)

        try:
            response = self._client.futures_create_order(**params)
            logger.info("Order response: %s", response)
            return response
        except (BinanceAPIException, BinanceOrderException) as exc:
            logger.error("Binance API rejected the order: %s", exc)
            raise BinanceClientError(f"Binance API error: {exc}") from exc
        except BinanceRequestException as exc:
            logger.error("Malformed request to Binance: %s", exc)
            raise BinanceClientError(f"Request error: {exc}") from exc
        except Exception as exc:  # noqa: BLE001 - network errors, timeouts, etc.
            logger.exception("Unexpected error while placing order")
            raise BinanceClientError(f"Network or unexpected error: {exc}") from exc

    def get_order_status(self, symbol: str, order_id: int):
        """Fetch the latest status of a previously placed order."""
        try:
            response = self._client.futures_get_order(symbol=symbol, orderId=order_id)
            logger.info("Order status response: %s", response)
            return response
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to fetch order status")
            raise BinanceClientError(f"Could not fetch order status: {exc}") from exc
