import calendar
import datetime as dt
from dataclasses import dataclass
from typing import Dict

BASE_URL = "https://www.forexfactory.com/"
READ_FIELDS = [
    "date",
    "time",
    "currency",
    "impact",
    "event",
    "actual",
    "forecast",
    "previous",
]

MONTH_MAPPING: Dict[int, str] = {
    k: v.lower() for k, v in enumerate(calendar.month_abbr) if k != 0
}


@dataclass
class Event:

    date: dt.date
    time: dt.time
    tz_offset: int
    currency: str
    impact: str
    event: str
    eventid: int
    actual: str
    forecast: str
    previous: str
    state: str
