"""Persian numbers in words, ordinals, and formatted numbers.

>>> number_to_words(1403)
'هزار و چهارصد و سه'
>>> number_to_ordinal(23)
'بیست و سوم'
>>> words_to_number("دو میلیون و سیصد هزار")
2300000
>>> format_number(1250000)
'۱٬۲۵۰٬۰۰۰'
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from fractions import Fraction
from typing import Literal, Union

from persianutils._util import ensure_str
from persianutils.characters import ZWNJ
from persianutils.digits import to_arabic_digits, to_english_digits, to_persian_digits
from persianutils.normalizer import normalize

__all__ = ["format_number", "number_to_ordinal", "number_to_words", "words_to_number"]

Number = Union[int, float, Decimal, str]

_ONES = ("", "یک", "دو", "سه", "چهار", "پنج", "شش", "هفت", "هشت", "نه")
_TEENS = ("ده", "یازده", "دوازده", "سیزده", "چهارده", "پانزده", "شانزده", "هفده", "هجده", "نوزده")
_TENS = ("", "", "بیست", "سی", "چهل", "پنجاه", "شصت", "هفتاد", "هشتاد", "نود")
_HUNDREDS = ("", "صد", "دویست", "سیصد", "چهارصد", "پانصد", "ششصد", "هفتصد", "هشتصد", "نهصد")
_SCALES = (
    "",
    "هزار",
    "میلیون",
    "میلیارد",
    "تریلیون",
    "کوادریلیون",
    "کوینتیلیون",
    "سکستیلیون",
    "سپتیلیون",
    "اکتیلیون",
    "نونیلیون",
    "دسیلیون",
)
_LIMIT = 1000 ** len(_SCALES)  # 10**36

_AND = " و "
_NEGATIVE = "منفی"


def _to_decimal(number: Number) -> Decimal:
    if isinstance(number, bool) or not isinstance(number, (int, float, Decimal, str)):
        raise TypeError(f"expected a number or str, got {type(number).__name__}")
    if isinstance(number, int):
        return Decimal(number)
    if isinstance(number, float):
        # repr() gives the shortest string that round-trips, so 0.1 stays 0.1.
        text = repr(number)
    elif isinstance(number, str):
        text = to_english_digits(number).replace(",", "").replace("_", "").strip()
    else:
        text = str(number)
    try:
        value = Decimal(text)
    except InvalidOperation:
        raise ValueError(f"not a number: {number!r}") from None
    if not value.is_finite():
        raise ValueError(f"not a finite number: {number!r}")
    return value


def _below_thousand(number: int) -> str:
    hundreds, rest = divmod(number, 100)
    parts = [_HUNDREDS[hundreds]] if hundreds else []
    if rest >= 20:
        tens, ones = divmod(rest, 10)
        parts.append(_TENS[tens])
        if ones:
            parts.append(_ONES[ones])
    elif rest >= 10:
        parts.append(_TEENS[rest - 10])
    elif rest:
        parts.append(_ONES[rest])
    return _AND.join(parts)


def _integer_to_words(number: int) -> str:
    if number == 0:
        return "صفر"
    if number >= _LIMIT:
        raise ValueError("numbers of 10**36 and above are not supported")
    groups = []
    scale = 0
    while number:
        number, group = divmod(number, 1000)
        if group:
            if scale == 0:
                groups.append(_below_thousand(group))
            elif scale == 1 and group == 1:
                groups.append(_SCALES[1])  # "هزار", not "یک هزار"
            else:
                groups.append(f"{_below_thousand(group)} {_SCALES[scale]}")
        scale += 1
    return _AND.join(reversed(groups))


def _fraction_name(places: int) -> str:
    """Name of the unit 10**-places: دهم، صدم، هزارم، ده‌هزارم، ..."""
    if places < 3:
        return ("دهم", "صدم")[places - 1]
    prefix = ("", "ده" + ZWNJ, "صد")[places % 3]
    return prefix + _SCALES[places // 3] + "م"


def number_to_words(number: Number) -> str:
    """Spell a number out in Persian words.

    Accepts integers, decimals, floats and numeric strings (Persian or
    English digits; "," and "٬" are read as thousands separators). Decimal
    fractions are read in tenths, hundredths and so on. Numbers up to
    10**36 are supported.

    >>> number_to_words(0)
    'صفر'
    >>> number_to_words(1000)
    'هزار'
    >>> number_to_words(1001000)
    'یک میلیون و هزار'
    >>> number_to_words(-12)
    'منفی دوازده'
    >>> number_to_words("۳٫۱۴")
    'سه و چهارده صدم'
    >>> number_to_words(0.5)
    'پنج دهم'
    """
    value = _to_decimal(number)
    negative = value < 0
    # copy_abs() is exact; abs() would round to the decimal context precision.
    integer_part, _, fraction = format(value.copy_abs(), "f").partition(".")
    fraction = fraction.rstrip("0")
    if len(fraction) >= 3 * len(_SCALES):
        raise ValueError("too many decimal places")
    words = []
    if int(integer_part) or not fraction:
        words.append(_integer_to_words(int(integer_part)))
    if fraction:
        words.append(f"{_integer_to_words(int(fraction))} {_fraction_name(len(fraction))}")
    text = _AND.join(words)
    if negative and text != "صفر":
        text = f"{_NEGATIVE} {text}"
    return text


def number_to_ordinal(number: int | str, *, prenominal: bool = False) -> str:
    """Spell a whole number as a Persian ordinal: یکم، دوم، سوم، سی‌ام.

    With ``prenominal=True`` the form used before a noun is returned:
    "سومین روز" instead of "روز سوم". The words "اول", "اولین" and
    "نخستین" are common alternatives for 1, but this function always spells
    the number out, so that 1 and 21 follow the same rule.

    >>> number_to_ordinal(1)
    'یکم'
    >>> number_to_ordinal(3)
    'سوم'
    >>> number_to_ordinal(30)
    'سی\\u200cام'
    >>> number_to_ordinal(103, prenominal=True)
    'صد و سومین'
    """
    value = _to_decimal(number)
    if value != value.to_integral_value() or value < 0:
        raise ValueError(f"ordinals need a non-negative whole number, not {number!r}")
    words = _integer_to_words(int(value))
    head, _, last = words.rpartition(" ")
    if last == "سه":
        last = "سوم"
    elif last == "سی":
        last = "سی" + ZWNJ + "ام"
    else:
        last += "م"
    words = f"{head} {last}" if head else last
    return words + "ین" if prenominal else words


_WORD_VALUES: dict[str, int] = {
    **{word: value for value, word in enumerate(_ONES) if word},
    **{word: value + 10 for value, word in enumerate(_TEENS)},
    **{word: value * 10 for value, word in enumerate(_TENS) if word},
    **{word: value * 100 for value, word in enumerate(_HUNDREDS) if value > 1},
    "صفر": 0,
    "یکصد": 100,
    # Common alternative spellings.
    "هیجده": 18,
    "شیش": 6,
    "پونزده": 15,
    "شونزده": 16,
    "پونصد": 500,
}
_SCALE_VALUES: dict[str, int] = {
    "صد": 100,
    **{word: 1000**power for power, word in enumerate(_SCALES) if word},
}
_ORDINAL_ONE = frozenset({"اول", "اولین", "نخست", "نخستین"})
_KNOWN_WORDS = {**_WORD_VALUES, **_SCALE_VALUES}


def _split_joined(token: str) -> list[str] | None:
    """Split number words written without spaces, such as "صدوبیست"."""
    vocabulary = set(_KNOWN_WORDS) | {"و"}
    # best[i]: the shortest split of token[:i] into known words.
    best: list[list[str] | None] = [[]] + [None] * len(token)
    for end in range(1, len(token) + 1):
        for start in range(end):
            previous = best[start]
            if previous is not None and token[start:end] in vocabulary:
                candidate = [*previous, token[start:end]]
                current = best[end]
                if current is None or len(candidate) < len(current):
                    best[end] = candidate
    return best[len(token)]


def _strip_ordinal(token: str) -> str:
    if token in ("سوم", "سومین"):
        return "سه"
    for suffix in ("مین", "م"):
        if token.endswith(suffix) and token[: -len(suffix)] in _KNOWN_WORDS:
            return token[: -len(suffix)]
    return token


# (value, is_scale_word). Fractions keep the arithmetic exact for any size.
Token = tuple[Fraction, bool]

_IMPOSSIBLE_ORDER = "number words are in an impossible order"


def _evaluate(tokens: list[Token]) -> Fraction:
    """Value of a phrase, split at its largest scale word ("هزار", "میلیون", ...)."""
    split_at = None
    for index, (value, is_scale) in enumerate(tokens):
        if is_scale and (split_at is None or value >= tokens[split_at][0]):
            split_at = index
    if split_at is None:
        return _evaluate_small(tokens)
    scale = tokens[split_at][0]
    multiplier = _evaluate(tokens[:split_at]) if split_at else Fraction(1)
    remainder = _evaluate(tokens[split_at + 1 :]) if split_at + 1 < len(tokens) else Fraction(0)
    # "سه صد" is 300 but "صد صد" means nothing; "هزار میلیارد" is 10**12.
    largest_multiplier = 9 if scale == 100 else scale - 1
    if not 0 < multiplier <= largest_multiplier or remainder >= scale:
        raise ValueError(_IMPOSSIBLE_ORDER)
    return multiplier * scale + remainder


def _evaluate_small(tokens: list[Token]) -> Fraction:
    """Value of words below the scale words, e.g. "سیصد و بیست و پنج"."""
    total = Fraction(0)
    limit = Fraction(1000)
    for value, _ in tokens:
        if value >= limit or (value == 0 and len(tokens) > 1):
            raise ValueError(_IMPOSSIBLE_ORDER)
        total += value
        if value.denominator != 1 or value >= 1000:
            limit = Fraction(0)  # a written number such as "۲۵۰" stands alone
        elif value >= 100:
            limit = Fraction(100)
        elif value >= 20:
            limit = Fraction(10)
        else:
            limit = Fraction(0)
    return total


def words_to_number(text: str) -> int:
    """Read a number written in Persian words (or mixed with digits).

    Understands spellings with or without spaces and half-spaces, Arabic
    letter variants, "منفی" for negative numbers, ordinals ("بیست و سوم",
    "سی‌امین") and numbers written in digits next to scale words ("۲٫۵
    میلیون").

    Raises ``ValueError`` if the text is not a number, or if the number is
    not a whole number.

    >>> words_to_number("هزار و چهارصد و سه")
    1403
    >>> words_to_number("صدوبیست")
    120
    >>> words_to_number("سی‌امین")
    30
    >>> words_to_number("۲٫۵ میلیون")
    2500000
    >>> words_to_number("منفی هفت")
    -7
    """
    cleaned = normalize(ensure_str(text), digits="en", fix_zwnj=False, persian_punctuation=False)
    words = cleaned.replace(ZWNJ, " ").split()
    if not words:
        raise ValueError("empty text")

    negative = words[0] == _NEGATIVE
    if negative:
        words = words[1:]
    if len(words) == 1 and words[0] in _ORDINAL_ONE:
        return -1 if negative else 1
    if len(words) > 1 and words[-1] in ("ام", "امین") and words[-2] in _KNOWN_WORDS:
        words = words[:-1]  # "سی ام" / "سی امین"
    if words:
        words[-1] = _strip_ordinal(words[-1])

    tokens: list[Token] = []
    for word in words:
        pieces = [word] if word in _KNOWN_WORDS or word == "و" else _split_joined(word)
        if pieces is None:
            try:
                tokens.append((Fraction(_to_decimal(word)), False))
            except ValueError:
                raise ValueError(f"not a number word: {word!r}") from None
            continue
        for piece in pieces:
            if piece in _SCALE_VALUES:
                tokens.append((Fraction(_SCALE_VALUES[piece]), True))
            elif piece in _WORD_VALUES:
                tokens.append((Fraction(_WORD_VALUES[piece]), False))
    if not tokens:
        raise ValueError(f"no number found in {text!r}")

    value = _evaluate(tokens)
    if value.denominator != 1:
        raise ValueError(f"{text!r} is not a whole number")
    return -value.numerator if negative else value.numerator


def format_number(
    number: Number,
    *,
    digits: Literal["fa", "en", "ar"] = "fa",
    thousands_separator: str | None = None,
    decimal_separator: str | None = None,
) -> str:
    """Format a number with thousands separators, in Persian digits by default.

    The separators default to the Persian "٬" and "٫" for Persian and
    Arabic-Indic digits, and to "," and "." for English digits. Decimal
    places are kept as given.

    >>> format_number(1234567.5)
    '۱٬۲۳۴٬۵۶۷٫۵'
    >>> format_number("۲۵۰۰۰۰۰", thousands_separator=",")
    '۲,۵۰۰,۰۰۰'
    >>> format_number(-1234.50, digits="en")
    '-1,234.5'
    """
    if digits not in ("fa", "en", "ar"):
        raise ValueError(f"digits must be 'fa', 'en' or 'ar', not {digits!r}")
    value = _to_decimal(number)
    if thousands_separator is None:
        thousands_separator = "," if digits == "en" else "٬"
    if decimal_separator is None:
        decimal_separator = "." if digits == "en" else "٫"
    integer_part, _, fraction = format(value.copy_abs(), "f").partition(".")
    text = f"{int(integer_part):,}".replace(",", thousands_separator)
    if fraction:
        text += decimal_separator + fraction
    if value < 0:
        text = "-" + text
    if digits == "fa":
        return to_persian_digits(text)
    if digits == "ar":
        return to_arabic_digits(text)
    return text
