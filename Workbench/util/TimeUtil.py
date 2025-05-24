from datetime import datetime, timezone , timedelta

def print_now():
    """Prints the current local datetime."""
    print(datetime.now())

def print_now_utc():
    """Prints the current UTC datetime."""
    print(datetime.now(timezone.utc))

def get_now():
    """Returns the current local datetime."""
    return datetime.now()

def get_now_utc():
    """Returns the current UTC datetime."""
    return datetime.now(timezone.utc)

def get_timestamp():
    """Returns the current timestamp in seconds."""
    return datetime.now().timestamp()

def get_now_utc_string():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

def get_now_hkt_string():
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")

def get_now_utc_date():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

def get_utc_date(backward_days: int = 0):
    """
    Returns the current UTC date minus the specified number of days.
    :param backward_days: Number of days to subtract from the current date.
    :return: Current UTC date minus the specified number of days.
    """
    return (datetime.now(timezone.utc) - timedelta(days=backward_days)).strftime("%Y-%m-%d")

def get_utc_now_ms():
    """
    Returns the current UTC time in milliseconds.
    :return: Current UTC time in milliseconds.
    """
    return int(datetime.now(timezone.utc).timestamp() * 1000)

def get_hkt_now_ms():
    """
    Returns the current Hong Kong Time (HKT) in milliseconds.
    :return: Current HKT time in milliseconds.
    """
    return int(datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=8))).timestamp() * 1000)

def get_latency_ms(event_ts: int) -> int:
    return event_ts - get_utc_now_ms()