import re


def validate_swiss_phone(phone: str) -> bool:
    """Validate Swiss phone number format: +41xxxxxxx (9-13 digits after +41)."""
    pattern = r"^\+41\d{7,11}$"
    return bool(re.match(pattern, phone.strip()))


def validate_sender_name(name: str) -> bool:
    """Validate sender name: max 12 characters, alphanumeric."""
    name = name.strip()
    return 1 <= len(name) <= 12


def validate_message_text(text: str) -> bool:
    """Validate SMS message text: max 160 characters."""
    return 1 <= len(text) <= 160


def validate_domain(domain: str) -> bool:
    """Basic domain validation."""
    domain = domain.strip().lower()
    pattern = r"^[a-z0-9]([a-z0-9\-]{0,61}[a-z0-9])?(\.[a-z]{2,})+$"
    return bool(re.match(pattern, domain))


def validate_amount(amount_str: str) -> float | None:
    """Validate and parse a USD amount string."""
    try:
        amount = float(amount_str.strip().replace(",", "."))
        if amount <= 0:
            return None
        return round(amount, 2)
    except (ValueError, TypeError):
        return None


def validate_positive_int(value_str: str) -> int | None:
    """Validate and parse a positive integer string."""
    try:
        value = int(value_str.strip())
        if value <= 0:
            return None
        return value
    except (ValueError, TypeError):
        return None
