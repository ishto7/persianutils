from __future__ import annotations

import copy
import pickle
from datetime import date, datetime, timedelta
from typing import Any

import pytest

import persianutils as pu
from persianutils.jalali import (
    MAXYEAR,
    MINYEAR,
    MONTH_NAMES,
    WEEKDAY_NAMES,
    JalaliDate,
    days_in_month,
    is_leap_year,
)


@pytest.mark.parametrize(
    ("jalali", "gregorian"),
    [
        ((1, 1, 1), date(622, 3, 22)),
        ((1357, 11, 22), date(1979, 2, 11)),
        ((1399, 1, 1), date(2020, 3, 20)),
        ((1399, 12, 30), date(2021, 3, 20)),
        ((1400, 1, 1), date(2021, 3, 21)),
        ((1402, 1, 1), date(2023, 3, 21)),
        ((1403, 1, 1), date(2024, 3, 20)),
        ((1403, 12, 30), date(2025, 3, 20)),
        ((1404, 1, 1), date(2025, 3, 21)),
        ((1404, 6, 31), date(2025, 9, 22)),
        ((1404, 7, 1), date(2025, 9, 23)),
        ((1405, 1, 1), date(2026, 3, 21)),
        ((1408, 12, 30), date(2030, 3, 20)),
    ],
)
def test_known_dates(jalali: tuple[int, int, int], gregorian: date) -> None:
    assert JalaliDate(*jalali).to_gregorian() == gregorian
    assert JalaliDate.from_gregorian(gregorian) == JalaliDate(*jalali)
    assert pu.to_gregorian(*jalali) == gregorian
    assert pu.to_jalali(gregorian) == JalaliDate(*jalali)


def test_leap_years() -> None:
    leap_years = [y for y in range(1350, 1425) if is_leap_year(y)]
    assert leap_years == [
        1350, 1354, 1358, 1362, 1366, 1370, 1375, 1379, 1383, 1387, 1391, 1395,
        1399, 1403, 1408, 1412, 1416, 1420, 1424,
    ]  # fmt: skip


def test_month_lengths() -> None:
    assert [days_in_month(1403, m) for m in range(1, 13)] == [31] * 6 + [30] * 6
    assert days_in_month(1404, 12) == 29


def test_every_day_round_trips_and_is_consecutive() -> None:
    day = JalaliDate(1300, 1, 1)
    gregorian = day.to_gregorian()
    while day.year < 1500:
        following = day + timedelta(days=1)
        assert following.to_gregorian() == gregorian + timedelta(days=1)
        assert JalaliDate.from_gregorian(gregorian) == day
        assert following > day
        day, gregorian = following, gregorian + timedelta(days=1)


def test_year_lengths_match_leap_years() -> None:
    for year in range(MINYEAR, MAXYEAR):
        length = (JalaliDate(year + 1, 1, 1) - JalaliDate(year, 1, 1)).days
        assert length == (366 if is_leap_year(year) else 365), year


def test_matches_jdatetime() -> None:
    jdatetime = pytest.importorskip("jdatetime")
    day = JalaliDate(1200, 1, 1).to_gregorian()
    end = JalaliDate(1600, 1, 1).to_gregorian()
    while day < end:
        ours = JalaliDate.from_gregorian(day)
        theirs = jdatetime.date.fromgregorian(date=day)
        assert (ours.year, ours.month, ours.day) == (theirs.year, theirs.month, theirs.day)
        assert ours.weekday() == theirs.weekday()
        day += timedelta(days=1)


def test_supported_range() -> None:
    first = JalaliDate(MINYEAR, 1, 1)
    last = JalaliDate(MAXYEAR, 12, days_in_month(MAXYEAR, 12))
    assert JalaliDate.from_gregorian(first.to_gregorian()) == first
    assert JalaliDate.from_gregorian(last.to_gregorian()) == last
    with pytest.raises(ValueError, match="before"):
        JalaliDate.from_gregorian(first.to_gregorian() - timedelta(days=1))
    with pytest.raises(ValueError, match="before"):
        JalaliDate.from_gregorian(date(1, 1, 1))
    with pytest.raises(ValueError, match="after"):
        JalaliDate.from_gregorian(last.to_gregorian() + timedelta(days=1))


@pytest.mark.parametrize(
    ("args", "error"),
    [
        ((0, 1, 1), ValueError),
        ((MAXYEAR + 1, 1, 1), ValueError),
        ((1403, 0, 1), ValueError),
        ((1403, 13, 1), ValueError),
        ((1403, 1, 0), ValueError),
        ((1403, 1, 32), ValueError),
        ((1403, 7, 31), ValueError),
        ((1404, 12, 30), ValueError),  # 1404 is not a leap year
        ((1403.0, 1, 1), TypeError),
        ((1403, True, 1), TypeError),
        (("1403", 1, 1), TypeError),
    ],
)
def test_invalid_dates(args: tuple[Any, ...], error: type[Exception]) -> None:
    with pytest.raises(error):
        JalaliDate(*args)


def test_weekday() -> None:
    friday = JalaliDate(1404, 1, 1)  # 21 March 2025
    assert friday.weekday() == 6
    assert WEEKDAY_NAMES[friday.weekday()] == "جمعه"
    week = [friday + timedelta(days=offset) for offset in range(1, 8)]
    assert [d.weekday() for d in week] == [0, 1, 2, 3, 4, 5, 6]


def test_today() -> None:
    assert JalaliDate.today().to_gregorian() == date.today()


def test_from_gregorian_accepts_datetime() -> None:
    assert JalaliDate.from_gregorian(datetime(2025, 3, 21, 23, 59)) == JalaliDate(1404, 1, 1)
    assert pu.to_jalali(2025, 3, 21) == JalaliDate(1404, 1, 1)
    with pytest.raises(TypeError):
        JalaliDate.from_gregorian("2025-03-21")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        pu.to_jalali(2025, 3)  # type: ignore[call-overload]
    with pytest.raises(TypeError):
        pu.to_gregorian("1404-01-01")  # type: ignore[call-overload]


@pytest.mark.parametrize(
    "text",
    ["1403-01-15", "1403/1/15", "۱۴۰۳/۰۱/۱۵", " 1403.01.15 ", "١٤٠٣-٠١-١٥"],
)
def test_parse(text: str) -> None:
    assert JalaliDate.parse(text) == JalaliDate(1403, 1, 15)


@pytest.mark.parametrize("text", ["", "1403-01", "1403-13-01", "15/01/1403", "hello"])
def test_parse_rejects(text: str) -> None:
    with pytest.raises(ValueError):
        JalaliDate.parse(text)


@pytest.mark.parametrize(
    ("fmt", "options", "expected"),
    [
        ("%Y-%m-%d", {}, "1403-01-05"),
        ("%Y/%-m/%-d", {}, "1403/1/5"),
        ("%y", {}, "03"),
        ("%j and %-j", {}, "005 and 5"),
        ("%A %-d %B %Y", {}, "یکشنبه 5 فروردین 1403"),
        ("%A %-d %B %Y", {"digits": "fa"}, "یکشنبه ۵ فروردین ۱۴۰۳"),
        ("%d/%m", {"digits": "ar"}, "٠٥/٠١"),
        ("100%%", {}, "100%"),
    ],
)
def test_strftime(fmt: str, options: dict[str, Any], expected: str) -> None:
    assert JalaliDate(1403, 1, 5).strftime(fmt, **options) == expected


@pytest.mark.parametrize("fmt", ["%H", "%-B", "%"])
def test_strftime_rejects_unknown_directives(fmt: str) -> None:
    with pytest.raises(ValueError):
        JalaliDate(1403, 1, 5).strftime(fmt)


def test_strftime_rejects_unknown_digit_style() -> None:
    with pytest.raises(ValueError, match="digits"):
        JalaliDate(1403, 1, 5).strftime("%Y", digits="persian")  # type: ignore[arg-type]


def test_names() -> None:
    assert len(MONTH_NAMES) == 12 and MONTH_NAMES[0] == "فروردین" and MONTH_NAMES[-1] == "اسفند"
    assert len(WEEKDAY_NAMES) == 7 and WEEKDAY_NAMES[0] == "شنبه"


def test_value_semantics() -> None:
    d = JalaliDate(1403, 1, 1)
    assert repr(d) == "JalaliDate(1403, 1, 1)"
    assert str(d) == d.isoformat() == "1403-01-01"
    assert f"{d}" == "1403-01-01"
    assert f"{d:%-d %B}" == "1 فروردین"
    assert d == JalaliDate(1403, 1, 1) and d != JalaliDate(1403, 1, 2)
    assert d != (1403, 1, 1)
    assert len({d, JalaliDate(1403, 1, 1)}) == 1
    assert sorted([JalaliDate(1404, 1, 1), d, JalaliDate(1403, 12, 30)])[0] == d
    assert pickle.loads(pickle.dumps(d)) == d
    assert copy.deepcopy(d) == d
    assert d.replace(day=15) == JalaliDate(1403, 1, 15)
    assert d.day_of_year() == 1 and JalaliDate(1403, 12, 30).day_of_year() == 366
    assert d.toordinal() == date(2024, 3, 20).toordinal()
    assert JalaliDate.fromordinal(d.toordinal()) == d
    with pytest.raises(AttributeError):
        d.year = 1404  # type: ignore[misc]
    with pytest.raises(AttributeError):
        del d.day


def test_arithmetic() -> None:
    d = JalaliDate(1403, 12, 30)
    assert d + timedelta(days=1) == JalaliDate(1404, 1, 1)
    assert timedelta(days=1) + d == JalaliDate(1404, 1, 1)
    assert d - timedelta(days=30) == JalaliDate(1403, 11, 30)
    assert JalaliDate(1404, 1, 1) - JalaliDate(1403, 1, 1) == timedelta(days=366)
    with pytest.raises(TypeError):
        _ = d + 1  # type: ignore[operator]
    with pytest.raises(TypeError):
        _ = d < date(2025, 3, 20)  # type: ignore[operator]
