from astral import Astral
import pytz


def get_timezone(city_name):
    return pytz.timezone(Astral()[city_name].timezone)


def get_today_sunset_time(city_name, today):
    return Astral()[city_name].sun(today)['sunset']


def get_today_sunrise_time(city_name, today):
    return Astral()[city_name].sun(today)['sunrise']


def get_seconds_until(earlier_time, later_time):
    tdelta = later_time - earlier_time
    return tdelta.total_seconds()

