import re

GRADE_RE = re.compile(r"^\s*(\d{1,2})\s*[-–]?\s*([A-Za-zА-Яа-яЁё])\s*$")


def parse_grade(raw: str) -> str | None:
    """'9a', '9-a', '9 - A' -> '9-A'"""
    m = GRADE_RE.match(raw)
    if not m:
        return None
    number = int(m.group(1))
    if not 1 <= number <= 11:
        return None
    return f"{number}-{m.group(2).upper()}"


def normalize_phone(raw: str) -> str | None:
    """'90 123 45 67', '+998901234567', '998901234567' -> '+998901234567'"""
    digits = re.sub(r"\D", "", raw)
    if len(digits) == 9:
        digits = "998" + digits
    if len(digits) == 12 and digits.startswith("998"):
        return "+" + digits
    return None