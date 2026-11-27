"""Convert digits between Persian, Arabic-Indic and English (ASCII) forms.

>>> to_persian_digits("Tel: 021-12345678")
'Tel: ۰۲۱-۱۲۳۴۵۶۷۸'
>>> to_english_digits("۱۴۰۳/۰۱/۰۱")
'1403/01/01'
>>> float(to_english_digits("۳٫۱۴"))
3.14
"""

from __future__ import annotations

from decimal import Decimal
from typing import Union

from persianutils.characters import ARABIC_DIGITS, ENGLISH_DIGITS, PERSIAN_DIGITS

__all__ = ["to_arabic_digits", "to_english_digits", "to_persian_digits"]

Number = Union[int, float, Decimal]

_TO_PERSIAN = str.maketrans(ENGLISH_DIGITS + ARABIC_DIGITS, PERSIAN_DIGITS * 2)
_TO_ARABIC = str.maketrans(ENGLISH_DIGITS + PERSIAN_DIGITS, ARABIC_DIGITS * 2)
# The Arabic decimal (٫) and thousands (٬) separators only ever appear in
# numbers, so they are converted too; that keeps the result parseable.
_TO_ENGLISH = str.maketrans(PERSIAN_DIGITS + ARABIC_DIGITS + "٫٬", ENGLISH_DIGITS * 2 + ".,")


def _as_text(value: str | Number) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        return str(value)
    raise TypeError(f"expected str or number, got {type(value).__name__}")


def to_persian_digits(value: str | Number) -> str:
    """Write English and Arabic-Indic digits as Persian digits (۰ to ۹).

    Accepts a string or a number. Only digits change; separators such as
    "." and "," are left as they are.

    >>> to_persian_digits(1403)
    '۱۴۰۳'
    >>> to_persian_digits("سال ٢٠٢٤")
    'سال ۲۰۲۴'
    """
    return _as_text(value).translate(_TO_PERSIAN)


def to_english_digits(value: str | Number) -> str:
    """Write Persian and Arabic-Indic digits as English (ASCII) digits.

    The Arabic decimal separator "٫" becomes "." and the thousands separator
    "٬" becomes ",", so the result can be parsed with ``int``, ``float`` or
    ``Decimal``.

    >>> to_english_digits("۰۹۱۲ ۳۴۵ ۶۷۸۹")
    '0912 345 6789'
    >>> to_english_digits("۱٬۲۵۰٫۵")
    '1,250.5'
    """
    return _as_text(value).translate(_TO_ENGLISH)


def to_arabic_digits(value: str | Number) -> str:
    """Write English and Persian digits as Arabic-Indic digits (٠ to ٩).

    >>> to_arabic_digits("2024")
    '٢٠٢٤'
    """
    return _as_text(value).translate(_TO_ARABIC)
