from datetime import datetime, date
import pytest

from ziweidoushu_core.calendar.lunar import solar_to_lunar, lunar_to_solar


def test_roundtrip_simple():
    """Solar -> Lunar -> Solar (non-leap)"""
    tz = "Asia/Ho_Chi_Minh"
    dt = datetime(1990, 5, 15, 9, 30)  # 15 May 1990
    lunar = solar_to_lunar(dt, tz)

    back = lunar_to_solar(
        lunar["lunar_year"],
        lunar["lunar_month"],
        lunar["lunar_day"],
        lunar["is_leap"],
        tz,
    )

    # Check round-trip correct
    assert back == dt.date()


def test_known_nonleap():
    """Check known mapping non-leap: Tết 2023 (22 Jan 2023) -> Lunar 1/1/2023"""
    tz = "Asia/Ho_Chi_Minh"
    dt = datetime(2023, 1, 22, 10, 0)  # Tết Quý Mão
    lunar = solar_to_lunar(dt, tz)

    assert lunar["lunar_year"] == 2023
    assert lunar["lunar_month"] == 1
    assert lunar["lunar_day"] == 1
    assert lunar["is_leap"] is False

    back = lunar_to_solar(2023, 1, 1, False, tz)
    assert back == date(2023, 1, 22)


def test_known_leap_month():
    """Check a date in a leap month (e.g., 2017 leap 6th month)"""
    tz = "Asia/Ho_Chi_Minh"
    dt = datetime(2017, 8, 21, 12, 0)  # 21 Aug 2017 = Lunar 30/6 nhuận/2017
    lunar = solar_to_lunar(dt, tz)

    assert lunar["lunar_year"] == 2017
    assert lunar["lunar_month"] == 6
    assert lunar["is_leap"] is True
    assert lunar["lunar_day"] == 30

    back = lunar_to_solar(2017, 6, 30, True, tz)
    assert back == dt.date()
