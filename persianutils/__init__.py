"""persianutils: a toolkit for Persian (Farsi) text.

>>> import persianutils as pu
>>> pu.normalize("ﺍﻳﻦ ﻛﺘﺎﺏ ﻫﺎ  را ٣ بار خوانده ام .")
'این کتاب\\u200cها را ۳ بار خوانده\\u200cام.'
>>> pu.number_to_words(1404)
'هزار و چهارصد و چهار'
>>> pu.to_jalali(2025, 3, 21)
JalaliDate(1404, 1, 1)
"""

from persianutils.digits import to_arabic_digits, to_english_digits, to_persian_digits
from persianutils.jalali import JalaliDate, to_gregorian, to_jalali
from persianutils.normalizer import (
    fix_spacing,
    fix_zwnj,
    normalize,
    remove_diacritics,
    remove_kashida,
    unify_characters,
)
from persianutils.numbers import format_number, number_to_ordinal, number_to_words, words_to_number
from persianutils.processes import standardize, standardize4Word2vec
from persianutils.stopwords import STOPWORDS
from persianutils.text import (
    has_persian,
    is_persian,
    sentence_tokenize,
    slugify,
    sort_key,
    word_tokenize,
)

__version__ = "2.0.0"

__all__ = [
    "STOPWORDS",
    "JalaliDate",
    "__version__",
    "fix_spacing",
    "fix_zwnj",
    "format_number",
    "has_persian",
    "is_persian",
    "normalize",
    "number_to_ordinal",
    "number_to_words",
    "remove_diacritics",
    "remove_kashida",
    "sentence_tokenize",
    "slugify",
    "sort_key",
    "standardize",
    "standardize4Word2vec",
    "to_arabic_digits",
    "to_english_digits",
    "to_gregorian",
    "to_jalali",
    "to_persian_digits",
    "unify_characters",
    "word_tokenize",
    "words_to_number",
]
