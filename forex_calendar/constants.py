import calendar
import datetime as dt
from dataclasses import dataclass
from typing import Dict, Optional

from pytz import FixedOffset

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

# earliest available data is Jan 2017
DATA_AVAILABLE_FROM = dt.date(2007, 1, 1)


@dataclass
class Event:

    date: dt.date
    time: dt.time
    tz_offset: int
    currency: str
    impact: Optional[str]
    event: str
    eventid: int
    actual: Optional[str]
    forecast: Optional[str]
    previous: Optional[str]
    state: Optional[str]

    def __post_init__(self):
        self.impact = self.impact if self.impact else None
        self.actual = self.actual if self.actual else None
        self.forecast = self.forecast if self.forecast else None
        self.previous = self.previous if self.previous else None
        self.state = self.state if self.state else None

    @property
    def timestamp(self):
        """tz-aware version of date & time & tz_offset"""
        ts = dt.datetime.combine(self.date, self.time)
        ts = FixedOffset(60 * self.tz_offset).localize(ts)
        return ts
