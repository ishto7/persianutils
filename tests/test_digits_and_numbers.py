from __future__ import annotations

import random
from decimal import Decimal
from typing import Any

import pytest

import persianutils as pu

# --------------------------------------------------------------------------
# Digits
# --------------------------------------------------------------------------


def test_digit_conversions_cover_all_digits() -> None:
    english, persian, arabic = "0123456789", "۰۱۲۳۴۵۶۷۸۹", "٠١٢٣٤٥٦٧٨٩"
    assert pu.to_persian_digits(english + arabic) == persian * 2
    assert pu.to_english_digits(persian + arabic) == english * 2
    assert pu.to_arabic_digits(english + persian) == arabic * 2


def test_to_english_digits_converts_number_separators() -> None:
    assert pu.to_english_digits("۱٬۲۳۴٫۵") == "1,234.5"
    assert float(pu.to_english_digits("۳٫۱۴")) == 3.14


def test_digit_conversions_accept_numbers() -> None:
    assert pu.to_persian_digits(1403) == "۱۴۰۳"
    assert pu.to_persian_digits(-2.5) == "-۲.۵"
    assert pu.to_arabic_digits(Decimal("12.50")) == "١٢.٥٠"
    assert pu.to_english_digits(7) == "7"


@pytest.mark.parametrize("value", [None, True, b"12", ["1"]])
def test_digit_conversions_reject_other_types(value: Any) -> None:
    for function in (pu.to_persian_digits, pu.to_english_digits, pu.to_arabic_digits):
        with pytest.raises(TypeError):
            function(value)


# --------------------------------------------------------------------------
# number_to_words
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("number", "words"),
    [
        (0, "صفر"),
        (5, "پنج"),
        (10, "ده"),
        (11, "یازده"),
        (18, "هجده"),
        (20, "بیست"),
        (21, "بیست و یک"),
        (99, "نود و نه"),
        (100, "صد"),
        (101, "صد و یک"),
        (110, "صد و ده"),
        (250, "دویست و پنجاه"),
        (500, "پانصد"),
        (1000, "هزار"),
        (1001, "هزار و یک"),
        (1100, "هزار و صد"),
        (1403, "هزار و چهارصد و سه"),
        (2000, "دو هزار"),
        (12_500, "دوازده هزار و پانصد"),
        (100_000, "صد هزار"),
        (101_000, "صد و یک هزار"),
        (1_000_000, "یک میلیون"),
        (1_001_000, "یک میلیون و هزار"),
        (2_300_005, "دو میلیون و سیصد هزار و پنج"),
        (10**9, "یک میلیارد"),
        (10**12, "یک تریلیون"),
        (-12, "منفی دوازده"),
        (Decimal("0.5"), "پنج دهم"),
        (0.05, "پنج صدم"),
        ("۳٫۱۴", "سه و چهارده صدم"),
        ("12.3456", "دوازده و سه هزار و چهارصد و پنجاه و شش ده\u200cهزارم"),
        ("0.000001", "یک میلیونم"),
        ("-0.25", "منفی بیست و پنج صدم"),
        ("1,250", "هزار و دویست و پنجاه"),
        ("۲٬۰۰۰", "دو هزار"),
        (Decimal("7.000"), "هفت"),
        (1e21, "یک سکستیلیون"),
    ],
)
def test_number_to_words(number: Any, words: str) -> None:
    assert pu.number_to_words(number) == words


@pytest.mark.parametrize(
    ("value", "error"),
    [
        (10**36, ValueError),
        (float("inf"), ValueError),
        (float("nan"), ValueError),
        ("twelve", ValueError),
        (True, TypeError),
        (None, TypeError),
    ],
)
def test_number_to_words_rejects(value: Any, error: type[Exception]) -> None:
    with pytest.raises(error):
        pu.number_to_words(value)


def test_number_to_words_handles_36_digit_numbers_exactly() -> None:
    number = 10**36 - 1
    words = pu.number_to_words(number)
    assert words.startswith("نهصد و نود و نه دسیلیون")
    assert words.endswith("نهصد و نود و نه")
    assert pu.words_to_number(words) == number


# --------------------------------------------------------------------------
# number_to_ordinal
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("number", "ordinal", "prenominal"),
    [
        (0, "صفرم", "صفرمین"),
        (1, "یکم", "یکمین"),
        (2, "دوم", "دومین"),
        (3, "سوم", "سومین"),
        (13, "سیزدهم", "سیزدهمین"),
        (23, "بیست و سوم", "بیست و سومین"),
        (30, "سی\u200cام", "سی\u200cامین"),
        (33, "سی و سوم", "سی و سومین"),
        (100, "صدم", "صدمین"),
        (1000, "هزارم", "هزارمین"),
        (1_000_000, "یک میلیونم", "یک میلیونمین"),
        ("۲۱", "بیست و یکم", "بیست و یکمین"),
    ],
)
def test_number_to_ordinal(number: Any, ordinal: str, prenominal: str) -> None:
    assert pu.number_to_ordinal(number) == ordinal
    assert pu.number_to_ordinal(number, prenominal=True) == prenominal


@pytest.mark.parametrize("value", [-1, 1.5, "2.5"])
def test_number_to_ordinal_needs_a_whole_non_negative_number(value: Any) -> None:
    with pytest.raises(ValueError):
        pu.number_to_ordinal(value)


# --------------------------------------------------------------------------
# words_to_number
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "number"),
    [
        ("صفر", 0),
        ("بیست و پنج", 25),
        ("هزار و چهارصد و سه", 1403),
        ("یک هزار", 1000),
        ("یکصد و بیست", 120),
        ("یک صد", 100),
        ("سه صد", 300),
        ("صدوبیست", 120),  # written without spaces
        ("سیصدوپنجاه", 350),
        ("دوهزار", 2000),
        ("دو میلیون و سیصد هزار و پنج", 2_300_005),
        ("هزار میلیارد", 10**12),
        ("يك ميليون", 1_000_000),  # Arabic letters
        ("هیجده", 18),  # common alternative spelling
        ("منفی هفت", -7),
        ("۲۵۰ هزار", 250_000),
        ("۲٫۵ میلیون", 2_500_000),
        ("1.5 میلیارد", 1_500_000_000),
        ("سوم", 3),
        ("بیست و سومین", 23),
        ("سی\u200cام", 30),
        ("سی ام", 30),
        ("صدمین", 100),
        ("اول", 1),
        ("نخستین", 1),
    ],
)
def test_words_to_number(text: str, number: int) -> None:
    assert pu.words_to_number(text) == number


@pytest.mark.parametrize(
    "text",
    ["", "   ", "سلام", "بیست بیست", "پنج و سه", "صد صد", "هزار هزار", "صفر هزار", "۱٫۵"],
)
def test_words_to_number_rejects(text: str) -> None:
    with pytest.raises(ValueError):
        pu.words_to_number(text)


def test_words_and_numbers_round_trip() -> None:
    rng = random.Random(1403)
    numbers = [
        *range(2001),
        *(rng.randrange(10**digits) for digits in (6, 9, 15, 24, 36) for _ in range(200)),
    ]
    for number in numbers:
        assert pu.words_to_number(pu.number_to_words(number)) == number
        assert pu.words_to_number(pu.number_to_ordinal(number)) == number
        assert pu.words_to_number(pu.number_to_ordinal(number, prenominal=True)) == number
        assert pu.words_to_number(pu.number_to_words(-number)) == -number


# --------------------------------------------------------------------------
# format_number
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("number", "options", "formatted"),
    [
        (1250000, {}, "۱٬۲۵۰٬۰۰۰"),
        (1234567.5, {}, "۱٬۲۳۴٬۵۶۷٫۵"),
        (999, {}, "۹۹۹"),
        (0, {}, "۰"),
        (-1234.5, {"digits": "en"}, "-1,234.5"),
        ("۲۵۰۰۰۰۰", {"thousands_separator": ","}, "۲,۵۰۰,۰۰۰"),
        (Decimal("1234.50"), {"digits": "ar"}, "١٬٢٣٤٫٥٠"),
        (1234.5, {"digits": "en", "thousands_separator": " ", "decimal_separator": ","}, "1 234,5"),
        (10**30, {"digits": "en"}, "1,000,000,000,000,000,000,000,000,000,000"),
    ],
)
def test_format_number(number: Any, options: dict[str, Any], formatted: str) -> None:
    assert pu.format_number(number, **options) == formatted


def test_format_number_rejects_unknown_digit_style() -> None:
    with pytest.raises(ValueError, match="digits"):
        pu.format_number(1, digits="persian")  # type: ignore[arg-type]
