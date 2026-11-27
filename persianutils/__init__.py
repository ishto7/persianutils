"""persianutils: a toolkit for Persian (Farsi) text.

>>> import persianutils as pu
>>> pu.normalize("ﺍﻳﻦ ﻛﺘﺎﺏ ﻫﺎ  را ٣ بار خوانده ام .")
'این کتاب\\u200cها را ۳ بار خوانده\\u200cام.'
"""

from persianutils.digits import to_arabic_digits, to_english_digits, to_persian_digits
from persianutils.normalizer import (
    fix_spacing,
    fix_zwnj,
    normalize,
    remove_diacritics,
    remove_kashida,
    unify_characters,
)
from persianutils.processes import standardize, standardize4Word2vec

__version__ = "1.1.0"

__all__ = [
    "__version__",
    "fix_spacing",
    "fix_zwnj",
    "normalize",
    "remove_diacritics",
    "remove_kashida",
    "standardize",
    "standardize4Word2vec",
    "to_arabic_digits",
    "to_english_digits",
    "to_persian_digits",
    "unify_characters",
]
