import time
from datetime import datetime, timedelta, UTC


def get_formatted_local_time():
    timestamp = time.time()
    local_time = time.localtime(timestamp)
    formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
    return formatted_time


def get_utc_time_with_offset(offset):
    current_utc_time = datetime.now(UTC)
    offset_time = current_utc_time + timedelta(hours=offset)
    formatted_time = offset_time.strftime("%Y-%m-%d %H:%M:%S")
    return formatted_time
