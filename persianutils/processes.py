"""Text standardization from persianutils 1.0.

:func:`standardize` and :func:`standardize4Word2vec` keep their 1.0 output,
so search indexes and training data built with them stay valid. New code
should prefer :func:`persianutils.normalize`, which is configurable and keeps
information these functions discard (for example the Persian decimal
separator and the madda on alef).
"""

from __future__ import annotations

import re
from typing import Any

from persianutils import PersianAlphabet as alphabet
from persianutils.ArabicAlphabet import *

to_reform: list[dict[str, Any]] = [
    {
        "characters": [
            HAMZA,
            HAMZA_BELOW,
            HAMZA_ABOVE,
            HAMZA_ISOLATED,
            MINI_ALEF,
            SMALL_ALEF,
            SMALL_WAW,
            SMALL_YEH,
            KASHEEDA,
            FATHATAN,
            DAMMATAN,
            KASRATAN,
            FATHA,
            DAMMA,
            KASRA,
            SHADDA,
            SUKUN,
            alphabet.THOUSANDS,
            alphabet.DECIMAL,
        ],
        "to_be": "",
    },
    {
        "characters": [
            ALEF_MADDA,
            ALEF_WASLA,
            HAMZA_BELOW_ALEF,
            HAMZA_ABOVE_ALEF,
        ],
        "to_be": alphabet.ALEF,
    },
    {
        "characters": [
            ALEF_MAKSURA,
            YEH,
        ],
        "to_be": alphabet.YE,
    },
    {
        "characters": [KAF],
        "to_be": alphabet.KAF,
    },
    {
        "characters": [
            LAM_ALEF,
            LAM_ALEF_HAMZA_ABOVE,
            LAM_ALEF_HAMZA_BELOW,
            LAM_ALEF_MADDA_ABOVE,
        ],
        "to_be": alphabet.LAM + alphabet.ALEF,
    },
    {
        "characters": [TEH_MARBUTA],
        "to_be": alphabet.HE2,
    },
]

replacementDict: dict[str, str] = {}
for rule in to_reform:
    for character in rule["characters"]:
        replacementDict[character] = rule["to_be"]

for originalForm, shapedForms in SHAPED_FORMS.items():
    for form in shapedForms:
        replacementDict[form] = replacementDict.get(originalForm, originalForm)

replacementDict4Word2vec = replacementDict.copy()

for i in range(10):
    replacementDict[EASTERN_ARABIC_NUMERALS[i]] = alphabet.NUMERALS[i]
    replacementDict[WESTERN_ARABIC_NUMERALS[i]] = alphabet.NUMERALS[i]

for i in range(10):
    replacementDict4Word2vec[EASTERN_ARABIC_NUMERALS[i]] = f" {alphabet.NUMERALS_WRITINGS[i]} "
    replacementDict4Word2vec[WESTERN_ARABIC_NUMERALS[i]] = f" {alphabet.NUMERALS_WRITINGS[i]} "
    replacementDict4Word2vec[alphabet.NUMERALS[i]] = f" {alphabet.NUMERALS_WRITINGS[i]} "

# 1.0 wrote this literal with invalid escape sequences ("\[", "\]"), which
# Python 3.12+ reports as a SyntaxWarning. This spelling holds the same
# characters with valid escapes.
for char in "[!\"#%'()*+,-./:;<=>?@\\[\\]^_`{|}~’”“′‘\\\\]؟؛«»،٪":
    replacementDict4Word2vec[char] = " "

# 1.0 escaped this key, so it matches the two characters " +" literally
# instead of collapsing runs of spaces. That quirk is part of the 1.0 output
# and is kept on purpose.
replacementDict4Word2vec[" +"] = " "

# 1.0 matched with these regular expressions. They are no longer used, but
# stay part of the module for code that imports them.
replacementRegex4Word2vec = re.compile(
    "(" + "|".join(map(re.escape, replacementDict4Word2vec)) + ")"
)
replacementRegex = re.compile("(" + "|".join(map(re.escape, replacementDict)) + ")")

_STANDARDIZE_TABLE = str.maketrans(replacementDict)
_WORD2VEC_TABLE = str.maketrans(
    {key: value for key, value in replacementDict4Word2vec.items() if len(key) == 1}
)


def standardize(text: str) -> str:
    """Standardize Persian text the way persianutils 1.0 did.

    Replaces Arabic letters with their Persian counterparts, removes
    diacritics, kashida and hamza marks, maps alef variants (including
    "آ") to "ا", turns contextual (presentation) forms into plain letters,
    and converts Western and Arabic-Indic digits to Persian digits.

    It also removes the Arabic decimal and thousands separators ("٫", "٬"),
    so "۳٫۱۴" becomes "۳۱۴". Use :func:`persianutils.normalize` when that
    matters.

    >>> standardize("سلامٌ علیکم!")
    'سلام علیکم!'
    """
    if not isinstance(text, str):
        raise TypeError(f"expected str, got {type(text).__name__}")
    return text.translate(_STANDARDIZE_TABLE)


def standardize4Word2vec(text: str) -> str:
    """Prepare text for word-embedding training the way persianutils 1.0 did.

    Applies :func:`standardize`'s letter rules, spells every digit out as a
    separate Persian word, and replaces punctuation with spaces. Runs of
    spaces are not collapsed, so split on whitespace to get tokens.

    >>> standardize4Word2vec("سلامٌ علیکم!")
    'سلام علیکم '
    """
    if not isinstance(text, str):
        raise TypeError(f"expected str, got {type(text).__name__}")
    return text.replace(" +", " ").translate(_WORD2VEC_TABLE)
