"""Tokenize, sort, detect and slugify Persian text.

>>> word_tokenize("کتاب‌ها را خواندم، ۳ بار!")
['کتاب\\u200cها', 'را', 'خواندم', '،', '۳', 'بار', '!']
>>> sorted(["ژاله", "زهرا", "پریا", "بهار", "آرش"], key=sort_key)
['آرش', 'بهار', 'پریا', 'زهرا', 'ژاله']
"""

from __future__ import annotations

import re
import unicodedata

from persianutils._util import ensure_str
from persianutils.characters import (
    _DIGIT,
    _MARK,
    ARABIC_DIGITS,
    ENGLISH_DIGITS,
    KASHIDA,
    PERSIAN_ALPHABET,
    PERSIAN_DIGITS,
    PERSIAN_LETTERS,
    ZWJ,
    ZWNJ,
)
from persianutils.normalizer import _unify_characters, normalize

__all__ = [
    "has_persian",
    "is_persian",
    "sentence_tokenize",
    "slugify",
    "sort_key",
    "word_tokenize",
]

# Letters accepted as Persian by is_persian(): the Persian letters plus the
# hamza forms, so text that has been through unify_characters() qualifies.
_PERSIAN_LETTERS = PERSIAN_LETTERS | frozenset("ٱ")

# --------------------------------------------------------------------------
# Detection
# --------------------------------------------------------------------------


def has_persian(text: str) -> bool:
    """Return True if the text contains at least one Persian letter.

    >>> has_persian("Hello سلام"), has_persian("Hello")
    (True, False)
    """
    return any(char in _PERSIAN_LETTERS for char in _unify_characters(ensure_str(text)))


def is_persian(text: str) -> bool:
    """Return True if every letter in the text is a Persian letter.

    Digits, punctuation, spaces, half-spaces and diacritics are ignored, and
    Arabic variants (ي ك) and presentation forms count as Persian, so the
    check suits form validation, for example of a name field. Text without
    any letters is not Persian.

    >>> is_persian("علی‌رضا محمدی"), is_persian("علي ۱۲۳"), is_persian("Ali")
    (True, True, False)
    >>> is_persian("۱۲۳"), is_persian("سلام world")
    (False, False)
    """
    found = False
    for char in _unify_characters(ensure_str(text)):
        if char in _PERSIAN_LETTERS:
            found = True
        elif char.isalpha() and char != KASHIDA:
            return False
    return found


# --------------------------------------------------------------------------
# Tokenization
# --------------------------------------------------------------------------

_WORD_CHAR = rf"(?:[^\W\d_]|[{_MARK}])"
_TOKEN_RE = re.compile(
    # Numbers, including decimals, thousands separators, dates and times.
    rf"[{_DIGIT}]+(?:[.,٫٬/:][{_DIGIT}]+)*"
    # Words; a ZWNJ (or ZWJ) inside a word keeps it one token.
    rf"|{_WORD_CHAR}+(?:[{ZWNJ}{ZWJ}]+{_WORD_CHAR}+)*"
    # Anything else that is not a space: punctuation, symbols, emoji.
    r"|[^\s\u200c\u200d]"
)
_SENTENCE_RE = re.compile(r"[^\n]+?(?:[.!?؟…]+[\"'»)\]]*(?=\s|$)|$)", re.MULTILINE)


def word_tokenize(text: str) -> list[str]:
    """Split text into words, numbers and punctuation marks.

    Words joined by a half-space (ZWNJ) stay one token, as Persian spelling
    intends ("کتاب‌ها", "می‌روم"). Numbers keep their decimal and thousands
    separators ("۱۲٫۵", "1,000", "1403/01/01").

    For best results, :func:`~persianutils.normalize` the text first.

    >>> word_tokenize("قیمت ۱٬۲۵۰ تومان است.")
    ['قیمت', '۱٬۲۵۰', 'تومان', 'است', '.']
    """
    return _TOKEN_RE.findall(ensure_str(text))


def sentence_tokenize(text: str) -> list[str]:
    """Split text into sentences at . ! ? ؟ and … followed by a space, and at line breaks.

    Abbreviations are not detected, so a period followed by a space always
    ends a sentence.

    >>> sentence_tokenize("سلام! حالت چطور است؟ من خوبم.\\nخداحافظ")
    ['سلام!', 'حالت چطور است؟', 'من خوبم.', 'خداحافظ']
    """
    return [match.strip() for match in _SENTENCE_RE.findall(ensure_str(text)) if match.strip()]


# --------------------------------------------------------------------------
# Sorting
# --------------------------------------------------------------------------

# Primary weights: آ sorts before ا, as in Persian dictionaries; hamza forms
# sort with their base letters, which the secondary weight separates.
_LETTER_WEIGHTS: dict[str, tuple[int, int]] = {"ء": (100, 0), "آ": (101, 0)}
for _index, _letter in enumerate(PERSIAN_ALPHABET):
    _LETTER_WEIGHTS[_letter] = (102 + _index, 0)
_LETTER_WEIGHTS.update(
    {
        "أ": (_LETTER_WEIGHTS["ا"][0], 1),
        "إ": (_LETTER_WEIGHTS["ا"][0], 2),
        "ٱ": (_LETTER_WEIGHTS["ا"][0], 3),
        "ؤ": (_LETTER_WEIGHTS["و"][0], 1),
        "ة": (_LETTER_WEIGHTS["ه"][0], 1),
        "ۀ": (_LETTER_WEIGHTS["ه"][0], 2),
        "ئ": (_LETTER_WEIGHTS["ی"][0], 1),
    }
)
for _digits in (ENGLISH_DIGITS, PERSIAN_DIGITS, ARABIC_DIGITS):
    for _value, _digit in enumerate(_digits):
        _LETTER_WEIGHTS[_digit] = (10 + _value, 0)

_IGNORED_IN_SORTING = frozenset(ZWNJ + ZWJ + KASHIDA)


def _weight(char: str) -> tuple[int, int]:
    weight = _LETTER_WEIGHTS.get(char)
    if weight is not None:
        return weight
    if char.isspace():
        return (1, 0)
    if char.isalpha():
        # Other scripts after Persian, case-insensitively.
        folded = char.casefold()
        return (1000 + ord(folded[0]), ord(char))
    # Punctuation and symbols before digits and letters.
    return (2, ord(char))


def sort_key(text: str) -> tuple[tuple[int, ...], tuple[int, ...], str]:
    """Key for sorting Persian strings in dictionary (alphabetical) order.

    Python's default ordering compares code points, which puts پ چ ژ گ ک ی
    after all the Arabic letters. Use this as ``key=`` instead:

    - Letters follow the Persian alphabet, with آ first.
    - Hamza forms sort with their base letters, and Arabic variants (ي ك)
      with the Persian ones; diacritics, kashida and half-spaces are ignored.
    - A space sorts before any letter, so "کتاب خانه" comes before "کتابخانه".
    - Digits of every script sort before letters, by value.

    >>> sorted(["گل", "کوه", "قلم", "یاس", "ویلا"], key=sort_key)
    ['قلم', 'کوه', 'گل', 'ویلا', 'یاس']
    """
    unified = _unify_characters(ensure_str(text))
    primary: list[int] = []
    secondary: list[int] = []
    for char in unified:
        if char in _IGNORED_IN_SORTING or unicodedata.combining(char):
            continue
        first, second = _weight(char)
        primary.append(first)
        secondary.append(second)
    return (tuple(primary), tuple(secondary), unified)


# --------------------------------------------------------------------------
# Slugs
# --------------------------------------------------------------------------

_NOT_SLUG_CHARS = re.compile(rf"[^\w\s{ZWNJ}-]")
_SLUG_SEPARATORS = re.compile(rf"[\s{ZWNJ}_-]+")


def slugify(text: str, separator: str = "-") -> str:
    """Make a URL slug that keeps Persian letters.

    The text is normalized, digits become English digits, punctuation is
    dropped, Latin letters are lowercased, and spaces and half-spaces become
    ``separator``.

    >>> slugify("آموزش پایتون: قسمت ۱۲!")
    'آموزش-پایتون-قسمت-12'
    >>> slugify("کتاب‌های Python")
    'کتاب-های-python'
    """
    text = normalize(
        ensure_str(text), digits="en", persian_punctuation=False, fix_zwnj=False
    ).lower()
    text = _NOT_SLUG_CHARS.sub("", text)
    return _SLUG_SEPARATORS.sub(separator, text).strip(separator)
