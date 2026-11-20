import hashlib
from datetime import date, datetime
from math import isnan
from decimal import Decimal, ROUND_DOWN


def _normalize(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, float):
        if isnan(value):
            return "NaN"
        epsilon = Decimal("0.000001")
        decimal_value = Decimal(str(value))
        adjusted = decimal_value + epsilon if decimal_value >= 0 else decimal_value - epsilon
        return float(adjusted.quantize(Decimal("0.01"), rounding=ROUND_DOWN))
    if isinstance(value, Decimal):
        return float(value.quantize(Decimal("0.01"), rounding=ROUND_DOWN))
    if isinstance(value, str):
        try:
            numeric = float(value)
            if value.strip() and "." in value:
                return float(Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_DOWN))
        except ValueError:
            pass
    return value


def result_hash(rows: list[tuple]) -> str:
    normalized = sorted(repr(tuple(_normalize(value) for value in row)) for row in rows)
    payload = repr(normalized).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]
