"""Character constants for Persian text.

>>> from persianutils.characters import PERSIAN_ALPHABET, ZWNJ
>>> len(PERSIAN_ALPHABET)
32
>>> "کتاب" + ZWNJ + "ها"
'کتاب\\u200cها'
"""

from __future__ import annotations

__all__ = [
    "ARABIC_DIGITS",
    "DIACRITICS",
    "ENGLISH_DIGITS",
    "KASHIDA",
    "NON_JOINING_LETTERS",
    "PERSIAN_ALPHABET",
    "PERSIAN_DIGITS",
    "PERSIAN_LETTERS",
    "PERSIAN_PUNCTUATION",
    "ZWJ",
    "ZWNJ",
]

#: Zero-width non-joiner, the Persian "half-space" (نیم‌فاصله).
ZWNJ = "\u200c"
#: Zero-width joiner.
ZWJ = "\u200d"
#: Kashida (tatweel), the stretching stroke "ـ".
KASHIDA = "\u0640"

#: The 32 letters of the Persian alphabet in dictionary order.
PERSIAN_ALPHABET = "ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی"

#: Letters found in standard Persian text: the alphabet plus آ, the hamza
#: forms, heh with hamza (ۀ) and teh marbuta (ة, in Arabic loanwords).
PERSIAN_LETTERS = frozenset(PERSIAN_ALPHABET + "آأإؤئءۀة")

PERSIAN_DIGITS = "۰۱۲۳۴۵۶۷۸۹"
#: Arabic-Indic digits (U+0660 to U+0669), common in Arabic text.
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
ENGLISH_DIGITS = "0123456789"

#: Persian punctuation and number signs: comma, semicolon, question mark,
#: guillemets, percent sign, decimal separator and thousands separator.
PERSIAN_PUNCTUATION = "،؛؟«»٪٫٬"

#: Letters that never join the letter after them, so a ZWNJ after them
#: changes nothing.
NON_JOINING_LETTERS = frozenset("ءآأؤإاةدذرزژوۀٱ")

#: Combining marks removed by :func:`persianutils.remove_diacritics`: the
#: harakat, tanwin, shadda and sukun, madda and hamza below, superscript
#: alef, and the Quranic annotation marks. Hamza above (U+0654) is not
#: included because it writes the ezafe in "هٔ".
DIACRITICS = "".join(
    chr(cp)
    for cp in [
        *range(0x0610, 0x061B),
        *range(0x064B, 0x0654),
        *range(0x0655, 0x0660),
        0x0670,
        *range(0x06D6, 0x06DD),
        *range(0x06DF, 0x06E5),
        0x06E7,
        0x06E8,
        *range(0x06EA, 0x06EE),
    ]
)

# Regular-expression character classes used across the package.
# Arabic-script letters, without kashida.
_LETTER = "\u0620-\u063f\u0641-\u064a\u066e\u066f\u0671-\u06d3\u06d5\u06ee\u06ef\u06fa-\u06fc\u06ff"
# Combining marks that may follow a letter inside a word.
_MARK = "\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06dc\u06df-\u06e4\u06e7\u06e8\u06ea-\u06ed"
_DIGIT = "0-9\u0660-\u0669\u06f0-\u06f9"
