"""Jalali (Solar Hijri, شمسی) dates.

Converts between the Jalali and Gregorian calendars, validates dates and
formats them with Persian month and weekday names.

>>> from datetime import date
>>> d = to_jalali(date(2025, 3, 21))
>>> d
JalaliDate(1404, 1, 1)
>>> d.strftime("%A %-d %B %Y")
'جمعه 1 فروردین 1404'
>>> d.strftime("%A %-d %B %Y", digits="fa")
'جمعه ۱ فروردین ۱۴۰۴'
>>> to_gregorian(1357, 11, 22)
datetime.date(1979, 2, 11)

Leap years follow the 33-year arithmetic rule with corrections published by
Kazimierz Borkowski (1996), the algorithm behind jalaali-js and most Jalali
libraries. It matches the official calendar for the years in use today and
is defined for the years 1 to 3177.
"""

from __future__ import annotations

import datetime as _dt
import re
from functools import cache, total_ordering
from typing import Any, Callable, Literal, overload

from persianutils._util import ensure_str
from persianutils.digits import to_arabic_digits, to_english_digits, to_persian_digits

__all__ = [
    "MAXYEAR",
    "MINYEAR",
    "MONTH_NAMES",
    "WEEKDAY_NAMES",
    "JalaliDate",
    "days_in_month",
    "is_leap_year",
    "to_gregorian",
    "to_jalali",
]

MINYEAR = 1
MAXYEAR = 3177

MONTH_NAMES = (
    "فروردین",
    "اردیبهشت",
    "خرداد",
    "تیر",
    "مرداد",
    "شهریور",
    "مهر",
    "آبان",
    "آذر",
    "دی",
    "بهمن",
    "اسفند",
)
#: Weekday names, starting with Saturday (شنبه), the first day of the Persian week.
WEEKDAY_NAMES = ("شنبه", "یکشنبه", "دوشنبه", "سه\u200cشنبه", "چهارشنبه", "پنجشنبه", "جمعه")

# Years in which the 33-year leap cycle shifts (Borkowski 1996).
_BREAKS = (
    -61,
    9,
    38,
    199,
    426,
    686,
    756,
    818,
    1111,
    1181,
    1210,
    1635,
    2060,
    2097,
    2192,
    2262,
    2324,
    2394,
    2456,
    3178,
)


def _div(a: int, b: int) -> int:
    """Integer division rounding towards zero, as in the reference algorithm."""
    quotient = abs(a) // abs(b)
    return quotient if (a < 0) == (b < 0) else -quotient


def _mod(a: int, b: int) -> int:
    return a - _div(a, b) * b


def _check_year(year: int) -> None:
    if isinstance(year, bool) or not isinstance(year, int):
        raise TypeError(f"year must be an int, not {type(year).__name__}")
    if not MINYEAR <= year <= MAXYEAR:
        raise ValueError(f"year {year} is out of range {MINYEAR}..{MAXYEAR}")


@cache
def _year_info(year: int) -> tuple[int, _dt.date]:
    """Return (years since the last leap year, Gregorian date of 1 Farvardin)."""
    gregorian_year = year + 621
    leap_jalali = -14
    previous_break = _BREAKS[0]
    jump = 0
    for current_break in _BREAKS[1:]:
        jump = current_break - previous_break
        if year < current_break:
            break
        leap_jalali += _div(jump, 33) * 8 + _div(_mod(jump, 33), 4)
        previous_break = current_break
    years_since_break = year - previous_break

    leap_jalali += _div(years_since_break, 33) * 8 + _div(_mod(years_since_break, 33) + 3, 4)
    if _mod(jump, 33) == 4 and jump - years_since_break == 4:
        leap_jalali += 1
    leap_gregorian = _div(gregorian_year, 4) - _div((_div(gregorian_year, 100) + 1) * 3, 4) - 150
    march_day = 20 + leap_jalali - leap_gregorian

    if jump - years_since_break < 6:
        years_since_break = years_since_break - jump + _div(jump + 4, 33) * 33
    leap = _mod(_mod(years_since_break + 1, 33) - 1, 4)
    if leap == -1:
        leap = 4
    return leap, _dt.date(gregorian_year, 3, march_day)


def is_leap_year(year: int) -> bool:
    """Return True if the Jalali ``year`` has 366 days (Esfand has 30 days).

    >>> is_leap_year(1403), is_leap_year(1404)
    (True, False)
    """
    _check_year(year)
    return _year_info(year)[0] == 0


def days_in_month(year: int, month: int) -> int:
    """Number of days in a Jalali month: 31, 30, or 29/30 for Esfand.

    >>> days_in_month(1403, 1), days_in_month(1403, 7), days_in_month(1404, 12)
    (31, 30, 29)
    """
    _check_year(year)
    if isinstance(month, bool) or not isinstance(month, int):
        raise TypeError(f"month must be an int, not {type(month).__name__}")
    if not 1 <= month <= 12:
        raise ValueError(f"month {month} is out of range 1..12")
    if month <= 6:
        return 31
    if month <= 11:
        return 30
    return 30 if is_leap_year(year) else 29


_PARSE_RE = re.compile(r"\s*(\d{1,4})\s*[-/.]\s*(\d{1,2})\s*[-/.]\s*(\d{1,2})\s*", re.ASCII)
_FORMAT_RE = re.compile(r"%(-?)(.?)", re.DOTALL)


@total_ordering
class JalaliDate:
    """An immutable Jalali calendar date, modelled on :class:`datetime.date`.

    >>> d = JalaliDate(1403, 12, 30)
    >>> d.to_gregorian()
    datetime.date(2025, 3, 20)
    >>> d + _dt.timedelta(days=1)
    JalaliDate(1404, 1, 1)
    >>> d.weekday(), WEEKDAY_NAMES[d.weekday()]
    (5, 'پنجشنبه')
    """

    __slots__ = ("_day", "_month", "_year")

    _year: int
    _month: int
    _day: int

    def __init__(self, year: int, month: int, day: int) -> None:
        if isinstance(day, bool) or not isinstance(day, int):
            raise TypeError(f"day must be an int, not {type(day).__name__}")
        length = days_in_month(year, month)
        if not 1 <= day <= length:
            raise ValueError(f"day {day} is out of range 1..{length} for {year}/{month}")
        object.__setattr__(self, "_year", year)
        object.__setattr__(self, "_month", month)
        object.__setattr__(self, "_day", day)

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError("JalaliDate objects are immutable")

    def __delattr__(self, name: str) -> None:
        raise AttributeError("JalaliDate objects are immutable")

    # -- construction --------------------------------------------------------

    @classmethod
    def from_gregorian(cls, value: _dt.date) -> JalaliDate:
        """Convert a :class:`datetime.date` (or ``datetime``) to a Jalali date."""
        if not isinstance(value, _dt.date):
            raise TypeError(f"expected datetime.date, got {type(value).__name__}")
        return cls.fromordinal(value.toordinal())

    @classmethod
    def fromordinal(cls, ordinal: int) -> JalaliDate:
        """Build a date from a proleptic Gregorian ordinal (see :meth:`date.toordinal`)."""
        gregorian = _dt.date.fromordinal(ordinal)
        year = gregorian.year - 621
        if year > MAXYEAR or (year >= MINYEAR and gregorian < _year_info(year)[1]):
            year -= 1
        if year < MINYEAR:
            raise ValueError(f"{gregorian} is before the first supported Jalali date")
        day_of_year = ordinal - _year_info(year)[1].toordinal()
        if day_of_year >= (366 if is_leap_year(year) else 365):
            raise ValueError(f"{gregorian} is after the last supported Jalali date")
        if day_of_year < 186:
            month, day = divmod(day_of_year, 31)
        else:
            month, day = divmod(day_of_year - 186, 30)
            month += 6
        return cls(year, month + 1, day + 1)

    @classmethod
    def today(cls) -> JalaliDate:
        """Today's date in the local time zone."""
        return cls.from_gregorian(_dt.date.today())

    @classmethod
    def parse(cls, text: str) -> JalaliDate:
        """Parse "1403-01-15", "1403/1/15" or "۱۴۰۳/۰۱/۱۵" (year, month, day).

        >>> JalaliDate.parse("۱۴۰۳/۰۱/۱۵")
        JalaliDate(1403, 1, 15)
        """
        match = _PARSE_RE.fullmatch(to_english_digits(ensure_str(text)))
        if not match:
            raise ValueError(f"not a Jalali date: {text!r}")
        year, month, day = map(int, match.groups())
        return cls(year, month, day)

    # -- accessors -----------------------------------------------------------

    @property
    def year(self) -> int:
        return self._year

    @property
    def month(self) -> int:
        return self._month

    @property
    def day(self) -> int:
        return self._day

    def to_gregorian(self) -> _dt.date:
        """The same day as a :class:`datetime.date`."""
        return _dt.date.fromordinal(self.toordinal())

    def toordinal(self) -> int:
        """Proleptic Gregorian ordinal, the same number as for the Gregorian date."""
        start = _year_info(self._year)[1].toordinal()
        month_offset = (self._month - 1) * 31 if self._month <= 7 else 186 + (self._month - 7) * 30
        return start + month_offset + self._day - 1

    def weekday(self) -> int:
        """Day of the week, Saturday (شنبه) = 0 through Friday (جمعه) = 6."""
        return (self.to_gregorian().weekday() + 2) % 7

    def day_of_year(self) -> int:
        """1 for 1 Farvardin, up to 365 or 366."""
        return self.toordinal() - _year_info(self._year)[1].toordinal() + 1

    def replace(
        self, year: int | None = None, month: int | None = None, day: int | None = None
    ) -> JalaliDate:
        """Return a copy with the given fields changed."""
        return type(self)(
            self._year if year is None else year,
            self._month if month is None else month,
            self._day if day is None else day,
        )

    # -- formatting ----------------------------------------------------------

    def isoformat(self) -> str:
        """Return the date as "YYYY-MM-DD", for example "1403-01-01"."""
        return f"{self._year:04d}-{self._month:02d}-{self._day:02d}"

    def strftime(self, format: str, *, digits: Literal["en", "fa", "ar"] = "en") -> str:
        """Format the date. Month and weekday names are in Persian.

        ``%Y`` year, ``%y`` two-digit year, ``%m`` month, ``%d`` day, ``%j`` day
        of the year, ``%B`` month name, ``%A`` weekday name, ``%%`` a percent
        sign. Write ``%-m``, ``%-d`` or ``%-j`` to drop leading zeros.
        ``digits="fa"`` writes the numbers in Persian digits.

        >>> JalaliDate(1403, 1, 5).strftime("%Y/%m/%d")
        '1403/01/05'
        >>> JalaliDate(1403, 1, 5).strftime("%-d %B", digits="fa")
        '۵ فروردین'
        """
        converters: dict[str, Callable[[str], str]] = {
            "en": str,
            "fa": to_persian_digits,
            "ar": to_arabic_digits,
        }
        convert = converters.get(digits)
        if convert is None:
            raise ValueError(f"digits must be 'en', 'fa' or 'ar', not {digits!r}")

        def number(value: int, width: int, pad: bool) -> str:
            return convert(f"{value:0{width}d}" if pad else str(value))

        def replace(match: re.Match[str]) -> str:
            no_pad, directive = match.group(1) == "-", match.group(2)
            if directive == "Y":
                return number(self._year, 4, not no_pad)
            if directive == "y":
                return number(self._year % 100, 2, not no_pad)
            if directive == "m":
                return number(self._month, 2, not no_pad)
            if directive == "d":
                return number(self._day, 2, not no_pad)
            if directive == "j":
                return number(self.day_of_year(), 3, not no_pad)
            if directive == "B" and not no_pad:
                return MONTH_NAMES[self._month - 1]
            if directive == "A" and not no_pad:
                return WEEKDAY_NAMES[self.weekday()]
            if directive == "%" and not no_pad:
                return "%"
            raise ValueError(f"unsupported format directive {match.group(0)!r}")

        return _FORMAT_RE.sub(replace, ensure_str(format))

    def __format__(self, format_spec: str) -> str:
        return self.strftime(format_spec) if format_spec else str(self)

    def __str__(self) -> str:
        return self.isoformat()

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._year}, {self._month}, {self._day})"

    # -- comparison and arithmetic -------------------------------------------

    def _key(self) -> tuple[int, int, int]:
        return (self._year, self._month, self._day)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, JalaliDate):
            return self._key() == other._key()
        return NotImplemented

    def __lt__(self, other: JalaliDate) -> bool:
        if isinstance(other, JalaliDate):
            return self._key() < other._key()
        return NotImplemented

    def __hash__(self) -> int:
        return hash(self._key())

    def __add__(self, other: _dt.timedelta) -> JalaliDate:
        if isinstance(other, _dt.timedelta):
            return type(self).fromordinal(self.toordinal() + other.days)
        return NotImplemented

    __radd__ = __add__

    @overload
    def __sub__(self, other: _dt.timedelta) -> JalaliDate: ...

    @overload
    def __sub__(self, other: JalaliDate) -> _dt.timedelta: ...

    def __sub__(self, other: _dt.timedelta | JalaliDate) -> JalaliDate | _dt.timedelta:
        if isinstance(other, _dt.timedelta):
            return type(self).fromordinal(self.toordinal() - other.days)
        if isinstance(other, JalaliDate):
            return _dt.timedelta(days=self.toordinal() - other.toordinal())
        return NotImplemented

    def __reduce__(self) -> tuple[type[JalaliDate], tuple[int, int, int]]:
        return (type(self), self._key())


@overload
def to_jalali(value: _dt.date, /) -> JalaliDate: ...


@overload
def to_jalali(year: int, month: int, day: int, /) -> JalaliDate: ...


def to_jalali(*args: Any) -> JalaliDate:
    """Convert a Gregorian date to Jalali.

    Pass a :class:`datetime.date` (or ``datetime``), or year, month and day.

    >>> to_jalali(2024, 3, 20)
    JalaliDate(1403, 1, 1)
    """
    if len(args) == 1:
        return JalaliDate.from_gregorian(args[0])
    if len(args) == 3:
        return JalaliDate.from_gregorian(_dt.date(*args))
    raise TypeError("to_jalali() takes a date, or year, month and day")


@overload
def to_gregorian(value: JalaliDate, /) -> _dt.date: ...


@overload
def to_gregorian(year: int, month: int, day: int, /) -> _dt.date: ...


def to_gregorian(*args: Any) -> _dt.date:
    """Convert a Jalali date to a :class:`datetime.date`.

    Pass a :class:`JalaliDate`, or year, month and day.

    >>> to_gregorian(1403, 1, 1)
    datetime.date(2024, 3, 20)
    """
    if len(args) == 1:
        if not isinstance(args[0], JalaliDate):
            raise TypeError(f"expected JalaliDate, got {type(args[0]).__name__}")
        return args[0].to_gregorian()
    if len(args) == 3:
        return JalaliDate(*args).to_gregorian()
    raise TypeError("to_gregorian() takes a JalaliDate, or year, month and day")
