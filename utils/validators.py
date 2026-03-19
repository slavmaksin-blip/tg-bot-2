import re


def validate_swiss_phone(phone: str) -> bool:
    pattern = r'^\+41\d{9,10}$'
    return bool(re.match(pattern, phone))


def validate_sender_name(name: str) -> bool:
    return 1 <= len(name) <= 12


def validate_sms_text(text: str) -> bool:
    return 1 <= len(text) <= 160


def validate_domain(domain: str) -> bool:
    pattern = r'^(?!-)[a-zA-Z0-9-]{1,63}(?<!-)(\.(?!-)[a-zA-Z0-9-]{1,63}(?<!-))*\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, domain))


def validate_amount(amount_str: str) -> float | None:
    try:
        amount = float(amount_str)
        if amount > 0:
            return amount
        return None
    except ValueError:
        return None
