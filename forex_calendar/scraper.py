import datetime as dt
import re
from time import sleep
from typing import List, Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from forex_calendar.constants import (
    BASE_URL,
    DATA_AVAILABLE_FROM,
    MONTH_MAPPING,
    READ_FIELDS,
    Event,
)

# TODO set logger
# TODO add license
# TODO write tests


def create_browser():
    options = Options()
    options.headless = True
    browser = webdriver.Firefox(options=options)
    return browser


def _load_data_from_query(query_period: str, sleeptime: int = 5) -> List[Event]:
    # get the page and make the soup
    url = f"{BASE_URL}calendar?{query_period}"

    browser = create_browser()
    browser.get(url)
    sleep(sleeptime)
    data = browser.page_source

    soup = BeautifulSoup(data, "lxml")

    tz_info = soup.select("div.calendar__print.calendar__print--header>div")
    tz_info = tz_info[0].text  # <div>Calendar Time Zone: GMT -5 (DST On)</div>
    tz, dst = re.findall(
        "Calendar Time Zone: GMT (?P<tz>.\d) \(DST (?P<dst>.*)\)", tz_info
    )[0]
    tz_offset = int(tz) + (1 if dst == "On" else 0)

    # get and parse table data, ignoring details and graph
    table = soup.find("table", class_="calendar__table")

    # do not use the ".calendar__row--grey" css selector (reserved for historical data)
    trs = table.select("tr.calendar__row.calendar_row")

    results = []
    current_year = int(query_period.split(".")[-1])
    prev_date = None
    prev_time = None
    # when there are multiple events in a day, only the first entry will have date info
    for tr in trs:
        try:
            row = _parse_row(tr, current_year, tz_offset, prev_date, prev_time)
            if row is None:  # end of table
                continue

            if (prev_date is not None) and (row.date < prev_date):
                # the time period spans over two years
                current_year += 1
                row.date = row.date.replace(year=current_year)

            results.append(row)
            prev_date, prev_time = row.date, row.time
        except ValueError:
            # TODO add logging here
            continue
    return results


def _parse_row(
    tr, current_year, tz_offset, prev_date=None, prev_time=None
) -> Optional[Event]:

    if (not tr.select("td.calendar__cell.calendar__currency")[0].text.strip()) and (
        not tr.select("td.calendar__cell.calendar__event")[0].text.strip()
    ):
        # end of table
        return None

    eventid = int(tr.attrs["data-eventid"])

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
                state = ""

        elif field == "forecast":
            forecast = data.text.strip()
        elif field == "previous":
            previous = data.text.strip()

    results = Event(
        date,
        time,
        tz_offset,
        currency,
        impact,
        event,
        eventid,
        actual,
        forecast,
        previous,
        state,
    )
    return results


def load_monthly_data(year: int, month: int) -> List[Event]:
    if dt.date(year, month, 1) < DATA_AVAILABLE_FROM:
        raise ValueError(
            f"No data available: earliest data is from {DATA_AVAILABLE_FROM:%Y-%m-%d}"
        )

    month_str = MONTH_MAPPING[month]
    return _load_data_from_query(f"month={month_str}.{year}")


def load_weekly_data(date) -> List[Event]:
    if date < DATA_AVAILABLE_FROM:
        raise ValueError(
            f"No data available: earliest data is from {DATA_AVAILABLE_FROM:%Y-%m-%d}"
        )
    # date of beginning of week (week starts on Sunday for ForexFactory)
    return _load_data_from_query(f"week={date:%b%d.%Y}")


def load_daily_data(date) -> List[Event]:
    if date < DATA_AVAILABLE_FROM:
        raise ValueError(
            f"No data available: earliest data is from {DATA_AVAILABLE_FROM:%Y-%m-%d}"
        )
    return _load_data_from_query(f"day={date:%b%d.%Y}")
