"""
Shared date formatting utilities used across the project.
"""
from datetime import datetime, timedelta

def date_fmt(target_date: datetime = None) -> dict:
    """Return a dict of common date format strings for the given date (default: today)."""
    if target_date is None:
        target_date = datetime.today()

    return {
        'a': target_date.strftime('%m%d%Y'),    # mmddyyyy
        'b': target_date.strftime('%Y.%m.%d'),  # yyyy.mm.dd
        'c': target_date.strftime('%#m.%#d.%y'),  # m.d.yy
        'd': target_date.strftime('%#m.%#d.%Y'),  # m.d.yyyy
        'e': target_date.strftime('%m.%d.%Y'),  # mm.dd.yyyy
        'f': target_date.strftime('%m-%d-%Y'),  # mm-dd-yyyy
        'g': target_date.strftime('%#m/%#d/%Y'),  # m/d/yyyy
        'h': target_date.strftime('%m/%d/%Y'),  # mm/dd/yyyy
    }

def today_str(fmt_key: str = 'f') -> str:
    """Return today's date in the specified format key."""
    return date_fmt()[fmt_key]


def recent_dates_str(days_back: int = 1, fmt_key: str = 'f') -> list:
    """Return a list of date strings from today back N days.

    Example: recent_dates_str(3, 'g') → ['4/24/2026', '4/23/2026', '4/22/2026']
    """
    today = datetime.today()
    return [
        date_fmt(today - timedelta(days=i))[fmt_key]
        for i in range(days_back)
    ]