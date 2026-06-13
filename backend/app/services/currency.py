from decimal import Decimal

# Fixed conversion rate for this project.
# In production you'd call an FX API (e.g., Open Exchange Rates).
# Using a fixed rate is a deliberate decision documented in DECISIONS.md.
USD_TO_INR = Decimal("83.50")

SUPPORTED_CURRENCIES = {"INR", "USD"}


def convert_to_inr(amount: Decimal, currency: str) -> Decimal:
    """
    Convert any supported currency amount to INR.
    
    Args:
        amount: The original amount
        currency: The source currency code (INR or USD)
    
    Returns:
        The equivalent amount in INR, rounded to 2 decimal places.
    
    Raises:
        ValueError: If the currency is not supported.
    """
    currency = currency.upper()
    if currency not in SUPPORTED_CURRENCIES:
        raise ValueError(f"Unsupported currency: {currency}. Supported: {SUPPORTED_CURRENCIES}")

    if currency == "INR":
        return round(amount, 2)
    elif currency == "USD":
        return round(amount * USD_TO_INR, 2)
