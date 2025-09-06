# ziweidoushu-core/calendar/lunar.py
# -*- coding: utf-8 -*-
"""
Lunar <-> Solar conversion (Vietnamese-style lunisolar calendar)

Implements:
- solar_to_lunar: Gregorian -> Vietnamese lunar date (year, month, day, leap flag)
- lunar_to_solar: Vietnamese lunar date -> Gregorian

Notes:
- Works for years roughly in [1900, 2099] (typical practical range).
- Time zone aware: pass an IANA timezone string (e.g., "Asia/Ho_Chi_Minh").
- Based on astronomical new moon approximation and sun longitude.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, date, timezone
from math import floor
from zoneinfo import ZoneInfo
from typing import Tuple

# ------------------------------
# Data models
# ------------------------------

@dataclass(frozen=True)
class LunarDate:
    year: int
    month: int
    day: int
    is_leap: bool  # True if leap month


# ------------------------------
# Helpers: time / timezone
# ------------------------------

def _tz_offset_hours(tz_str: str, d: date) -> int:
    """
    Return timezone offset in WHOLE HOURS for given IANA tz at a specific date.
    (VN/Asia typically whole hours; if DST half-hour zones are used, rounding is applied.)
    """
    # Use noon to avoid DST transitions edge cases
    dt = datetime(d.year, d.month, d.day, 12, 0, tzinfo=ZoneInfo(tz_str))
    offset = dt.utcoffset() or (dt - dt.astimezone(timezone.utc))
    return int(round(offset.total_seconds() / 3600.0))


# ------------------------------
# Core Julian Day helpers
# ------------------------------

def _jd_from_date(dd: int, mm: int, yy: int) -> int:
    a = (14 - mm) // 12
    y = yy + 4800 - a
    m = mm + 12 * a - 3
    jd = dd + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    return jd

def _jd_to_date(jd: int) -> Tuple[int, int, int]:
    a = jd + 32044
    b = (4 * a + 3) // 146097
    c = a - (b * 146097) // 4
    d = (4 * c + 3) // 1461
    e = c - (1461 * d) // 4
    m = (5 * e + 2) // 153
    day = e - (153 * m + 2) // 5 + 1
    month = m + 3 - 12 * (m // 10)
    year = b * 100 + d - 4800 + m // 10
    return day, month, year


# ------------------------------
# Astronomy approximations
# ------------------------------

def _new_moon_day(k: int, tz_offset_hours: int) -> int:
    """
    Return the Julian day number of the k-th new moon after a base epoch,
    adjusted by timezone offset (hours).
    """
    # Base on mean new moon (simple approximation adequate for calendar use)
    T = k / 1236.85
    T2 = T * T
    T3 = T2 * T
    dr = 3.141592653589793 / 180.0
    Jd1 = 2415020.75933 + 29.53058868 * k \
        + 0.0001178 * T2 - 0.000000155 * T3
    Jd1 = Jd1 + 0.00033 * _sin((166.56 + 132.87 * T - 0.009173 * T2) * dr)
    M = 359.2242 + 29.10535608 * k - 0.0000333 * T2 - 0.00000347 * T3
    Mpr = 306.0253 + 385.81691806 * k + 0.0107306 * T2 + 0.00001236 * T3
    F = 21.2964 + 390.67050646 * k - 0.0016528 * T2 - 0.00000239 * T3
    C1 = (0.1734 - 0.000393 * T) * _sin(M * dr) \
        + 0.0021 * _sin(2 * M * dr) \
        - 0.4068 * _sin(Mpr * dr) \
        + 0.0161 * _sin(2 * Mpr * dr) \
        - 0.0004 * _sin(3 * Mpr * dr) \
        + 0.0104 * _sin(2 * F * dr) \
        - 0.0051 * _sin((M + Mpr) * dr) \
        - 0.0074 * _sin((M - Mpr) * dr) \
        + 0.0004 * _sin((2 * F + M) * dr) \
        - 0.0004 * _sin((2 * F - M) * dr) \
        - 0.0006 * _sin((2 * F + Mpr) * dr) \
        + 0.0010 * _sin((2 * F - Mpr) * dr) \
        + 0.0005 * _sin((2 * M + Mpr) * dr)
    if T < -11:
        deltat = 0.001 + 0.000839 * T + 0.0002261 * T2 - 0.00000845 * T3 - 0.000000081 * T * T3
    else:
        deltat = -0.000278 + 0.000265 * T + 0.000262 * T2
    JdNew = Jd1 + C1 - deltat
    # Adjust to local midnight by timezone (convert Julian day at UTC to local day number)
    return int(floor(JdNew + 0.5 + tz_offset_hours / 24.0))

def _sun_longitude(jdn: int, tz_offset_hours: int) -> float:
    """Sun's longitude (in radians) at given JDN (approx)."""
    T = (jdn - 2451545.5 - tz_offset_hours / 24.0) / 36525
    dr = 3.141592653589793 / 180.0
    M = 357.52910 + 35999.05030 * T - 0.0001559 * T * T - 0.00000048 * T * T * T
    L0 = 280.46645 + 36000.76983 * T + 0.0003032 * T * T
    DL = (1.914600 - 0.004817 * T - 0.000014 * T * T) * _sin(dr * M) \
       + (0.019993 - 0.000101 * T) * _sin(dr * 2 * M) \
       + 0.000290 * _sin(dr * 3 * M)
    L = L0 + DL
    L = L * dr
    L = L - 2 * 3.141592653589793 * floor(L / (2 * 3.141592653589793))
    return L

def _sin(x: float) -> float:
    # Separate to keep math namespace minimal
    from math import sin
    return sin(x)


# ------------------------------
# Calendar helpers
# ------------------------------

def _lunar_month11(yy: int, tz_offset_hours: int) -> int:
    """
    JDN of 11th lunar month (which contains winter solstice) of given Gregorian year.
    """
    off = _jd_from_date(31, 12, yy) - 2415021
    k = int(off / 29.530588853)
    nm = _new_moon_day(k, tz_offset_hours)
    sun_long = _sun_longitude(nm, tz_offset_hours)
    if sun_long >= 3.141592653589793:  # >= 180°, passed winter solstice
        nm = _new_moon_day(k - 1, tz_offset_hours)
    return nm

def _leap_month_offset(a11: int, tz_offset_hours: int) -> int:
    """
    Find leap month offset after month 11. Result in [2..14] where value-1 is leap month index.
    """
    k = int(0.5 + (a11 - 2415021.076998695) / 29.530588853)
    last = 0
    i = 1
    arc = _sun_longitude(_new_moon_day(k + i, tz_offset_hours), tz_offset_hours)
    while True:
        last = arc
        i += 1
        arc = _sun_longitude(_new_moon_day(k + i, tz_offset_hours), tz_offset_hours)
        if arc == last or i >= 15:
            break
    return i - 1


# ------------------------------
# Public conversions
# ------------------------------

def solar_to_lunar(dt: datetime, tz_str: str) -> dict:
    """
    Convert a timezone-aware or naive datetime (date part used) to Vietnamese lunar date.

    Returns dict:
    {
      "lunar_year": int, "lunar_month": int, "lunar_day": int,
      "is_leap": bool
    }
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(tz_str))
    d = dt.date()
    tz_h = _tz_offset_hours(tz_str, d)

    dd, mm, yy = d.day, d.month, d.year
    day_number = _jd_from_date(dd, mm, yy)
    k = int((day_number - 2415021.076998695) / 29.530588853)
    month_start = _new_moon_day(k + 1, tz_h)
    if month_start > day_number:
        month_start = _new_moon_day(k, tz_h)

    a11 = _lunar_month11(yy, tz_h)
    b11 = _lunar_month11(yy + 1, tz_h)
    if a11 >= month_start:
        lunar_year = yy
        a11 = _lunar_month11(yy - 1, tz_h)
    else:
        lunar_year = yy + 1 if month_start >= b11 else yy

    lunar_day = day_number - month_start + 1
    diff = int((month_start - a11) / 29)
    lunar_month = diff + 11
    is_leap = False

    if b11 - a11 > 365:
        leap_month_diff = _leap_month_offset(a11, tz_h)
        if diff >= leap_month_diff:
            lunar_month = diff + 10
            if diff == leap_month_diff:
                is_leap = True

    if lunar_month > 12:
        lunar_month -= 12
    if lunar_month >= 11 and diff < 4:
        lunar_year -= 1

    return {
        "lunar_year": lunar_year,
        "lunar_month": lunar_month,
        "lunar_day": int(lunar_day),
        "is_leap": is_leap,
    }

def lunar_to_solar(lunar_year: int, lunar_month: int, lunar_day: int, is_leap: bool, tz_str: str) -> date:
    """
    Convert Vietnamese lunar date -> Gregorian date.
    Returns Python date.
    """
    # Choose an approximate Gregorian year to anchor A11
    tz_h = _tz_offset_hours(tz_str, date(lunar_year, max(1, min(12, lunar_month)), 15))
    if lunar_month < 11:
        a11 = _lunar_month11(lunar_year - 1, tz_h)
        b11 = _lunar_month11(lunar_year, tz_h)
    else:
        a11 = _lunar_month11(lunar_year, tz_h)
        b11 = _lunar_month11(lunar_year + 1, tz_h)

    k = int(0.5 + (a11 - 2415021.076998695) / 29.530588853)
    off = lunar_month - 11
    if off < 0:
        off += 12

    if b11 - a11 > 365:
        leap_off = _leap_month_offset(a11, tz_h)
        leap = leap_off - 1
        if is_leap and (off != leap):
            # Invalid leap month
            raise ValueError("Invalid leap month for the given lunar year")
        if is_leap or off >= leap_off:
            off += 1

    month_start = _new_moon_day(k + off, tz_h)
    jdn = month_start + lunar_day - 1
    dd, mm, yy = _jd_to_date(jdn)
    return date(yy, mm, dd)


# ------------------------------
# Tiny self-test (optional)
# ------------------------------

if __name__ == "__main__":
    tz = "Asia/Ho_Chi_Minh"
    # Example: solar -> lunar
    dt = datetime(1990, 5, 15, 9, 30)  # time is ignored (only date used)
    print("Solar:", dt.date())
    print("Lunar:", solar_to_lunar(dt, tz))

    # Example: lunar -> solar (non-leap)
    ld = lunar_to_solar(1990, 4, 21, False, tz)  # expecting around 1990-05-15
    print("Back to Solar:", ld)
