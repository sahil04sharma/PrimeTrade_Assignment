"""
Input validation for order parameters.

Keeping validation separate from the CLI and the API client means both
layers can rely on already-sane data, and the rules are easy to unit test
in isolation.
"""

import re


class ValidationError(ValueError):
    """Raised when user-supplied order parameters fail validation."""


VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT"}
# Loose symbol check: 6-20 uppercase letters/digits, e.g. BTCUSDT, ETHUSDT
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]{5,20}$")


def validate_symbol(symbol: str) -> str:
    if not symbol:
        raise ValidationError("Symbol is required (e.g. BTCUSDT).")
    symbol = symbol.strip().upper()
    if not SYMBOL_PATTERN.match(symbol):
        raise ValidationError(
            f"'{symbol}' does not look like a valid futures symbol (e.g. BTCUSDT)."
        )
    return symbol


def validate_side(side: str) -> str:
    if not side:
        raise ValidationError("Side is required (BUY or SELL).")
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValidationError(f"Side must be one of {sorted(VALID_SIDES)}, got '{side}'.")
    return side


def validate_order_type(order_type: str) -> str:
    if not order_type:
        raise ValidationError("Order type is required (MARKET or LIMIT).")
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Order type must be one of {sorted(VALID_ORDER_TYPES)}, got '{order_type}'."
        )
    return order_type


def validate_quantity(quantity) -> float:
    try:
        quantity = float(quantity)
    except (TypeError, ValueError):
        raise ValidationError(f"Quantity must be a number, got '{quantity}'.")
    if quantity <= 0:
        raise ValidationError("Quantity must be greater than 0.")
    return quantity


def validate_price(price, order_type: str):
    """
    Price is required for LIMIT orders and must be > 0.
    For MARKET orders, price is ignored and returned as None.
    """
    if order_type == "MARKET":
        return None

    if price is None:
        raise ValidationError("Price is required for LIMIT orders.")
    try:
        price = float(price)
    except (TypeError, ValueError):
        raise ValidationError(f"Price must be a number, got '{price}'.")
    if price <= 0:
        raise ValidationError("Price must be greater than 0.")
    return price


def validate_order_params(symbol: str, side: str, order_type: str, quantity, price=None):
    """
    Run all validations and return a clean, normalized dict of parameters.
    Raises ValidationError on the first failure encountered.
    """
    clean_symbol = validate_symbol(symbol)
    clean_side = validate_side(side)
    clean_type = validate_order_type(order_type)
    clean_quantity = validate_quantity(quantity)
    clean_price = validate_price(price, clean_type)

    return {
        "symbol": clean_symbol,
        "side": clean_side,
        "order_type": clean_type,
        "quantity": clean_quantity,
        "price": clean_price,
    }
