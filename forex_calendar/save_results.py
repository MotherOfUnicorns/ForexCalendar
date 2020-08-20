from typing import Optional, List
from forex_calendar.constants import Event
from dataclasses import astuple, asdict, fields
import json

import datetime as dt
import csv


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (dt.datetime, dt.date, dt.time)):
        return obj.isoformat()

    raise TypeError("Type %s not serializable" % type(obj))


def _auto_file_name(results: List[Event]) -> str:
    filename = f"forex_calendar_{results[0].date:%Y%m%d}_{results[-1].date:%Y%m%d}"
    return filename


def save_as_csv(results: List[Event], filename: Optional[str] = None, mode="w"):
    if filename is None:
        filename = f"{_auto_file_name(results)}.csv"

    output = [astuple(r) for r in results]
    with open(filename, mode) as f:
        csvwriter = csv.writer(f)
        if mode == "w":
            header = [field.name for field in fields(results[0])]
            csvwriter.writerow(header)

        output = [astuple(r) for r in results]
        csvwriter.writerows(output)

    return


def save_as_json(
    results: List[Event], filename: Optional[str] = None, mode="w"
) -> None:
    if filename is None:
        filename = f"{_auto_file_name(results)}.json"

    output = json.dumps([asdict(r) for r in results], default=json_serial)
    with open(filename, mode) as f:
        f.write(output)

    return
