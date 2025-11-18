# app/services/utils.py
from datetime import date, datetime


def parse_input_date(date_str: str | None) -> date:

    today = date.today()

    if not date_str:
        return today

    raw = date_str.strip()

    try:
        return datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        pass

    cleaned = raw.replace(" ", "")
    for fmt in ("%d.%m.%Y", "%d.%m.%Y."):
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            pass

    if cleaned.endswith("."):
        cleaned_no_dot = cleaned[:-1]
    else:
        cleaned_no_dot = cleaned

    try:
        dt = datetime.strptime(cleaned_no_dot, "%d.%m").date()
        return dt.replace(year=today.year)
    except ValueError:
        pass

    raise ValueError("unrecognized")
