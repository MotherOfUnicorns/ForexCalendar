import calendar
import datetime as dt
from collections import namedtuple
from typing import Dict, List, Optional

import requests
from bs4 import BeautifulSoup

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

WriteFields = namedtuple(
    "WriteFields",
    [
        "date",
        "time",
        "currency",
        "impact",
        "event",
        "actual",
        "forecast",
        "previous",
        "state",
    ],
)
# TODO timezone info


def _load_data_from_query(query_period: str) -> List[WriteFields]:
    # get the page and make the soup
    r = requests.get(f"{BASE_URL}calendar?{query_period}")
    data = r.text
    soup = BeautifulSoup(data, "lxml")

    # get and parse table data, ignoring details and graph
    table = soup.find("table", class_="calendar__table")

    # do not use the ".calendar__row--grey" css selector (reserved for historical data)
    trs = table.select("tr.calendar__row.calendar_row")

    results = []
    current_year = query_period.split(".")[-1]
    # TODO if the week/month spans two different years, this will not work
    prev_date = None
    prev_time = None
    # when there are multiple events in a day, only the first entry will have date info
    for tr in trs:
        try:
            row = _parse_row(tr, current_year, prev_date, prev_time)
            if row is None:
                continue
            results.append(row)
            prev_date, prev_time = row.date, row.time
        except ValueError:
            # TODO add logging here
            continue
    return results


def _parse_row(
    tr, current_year, prev_date=None, prev_time=None
) -> Optional[WriteFields]:

    if (not tr.select("td.calendar__cell.calendar__currency")[0].text.strip()) and (
        not tr.select("td.calendar__cell.calendar__event")[0].text.strip()
    ):
        # end of table
        return None

    for field in READ_FIELDS:
        data = tr.select(f"td.calendar__cell.calendar__{field}.{field}")[0]

        if field == "date":
            if not data.text.strip():
                date = prev_date
            else:
                date_str = data.select("span>span")[0].text.strip()
                date = dt.datetime.strptime(
                    f"{current_year} {date_str}", "%Y %b %d"
                ).date()
            if date is None:
                raise ValueError("no date info available")

        elif field == "time":
            if not data.text.strip():
                time = prev_time
            elif "Day" in data.text.strip():
                # time is sometimes "All Day" or "Day X" (eg. WEF Annual Meetings)
                time = dt.time(0)
            else:
                time_str = data.text.strip()
                time = dt.datetime.strptime(time_str, "%I:%M%p").time()
            if time is None:
                raise ValueError("no time info available")

        elif field == "currency":
            currency = data.text.strip()

        elif field == "impact":
            # when impact says "Non-Economic" on mouseover, the relevant
            # class name is "Holiday", thus we do not use the classname
            impact = data.find("span")["class"][0]

        elif field == "event":
            event = data.text.strip()

        elif field == "actual":
            actual = data.text.strip()
            # state = re.findall("class=\"calendar__cell calendar__actual actual\"><span class=\"(.*)\">.*</span></td>", str(data))
            if "better" in str(data):
                state = "better"
            elif "worse" in str(data):
                state = "worse"
            else:
                state = "None"

        elif field == "forecast":
            forecast = data.text.strip()
        elif field == "previous":
            previous = data.text.strip()

    results = WriteFields(
        date, time, currency, impact, event, actual, forecast, previous, state
    )
    return results


def load_monthly_data(year: int, month: int) -> List[WriteFields]:
    month_str = MONTH_MAPPING[month]
    return _load_data_from_query(f"month={month_str}.{year}")


def load_weekly_data(date) -> List[WriteFields]:
    # date of beginning of week (week starts on Sunday for ForexFactory)
    return _load_data_from_query(f"week={date:%b%d.%Y}")


def load_daily_data(date) -> List[WriteFields]:
    return _load_data_from_query(f"day={date:%b%d.%Y}")
