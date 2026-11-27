"""Normalize Persian text.

:func:`normalize` runs every step below; each step is also available on its
own:

- :func:`unify_characters`: Arabic and presentation-form code points become
  standard Persian letters (ي→ی, ك→ک, ﻻ→لا).
- :func:`remove_diacritics` and :func:`remove_kashida`.
- digit unification (see :mod:`persianutils.digits`).
- Persian punctuation in Persian context (, ; ? → ، ؛ ؟).
- :func:`fix_spacing`: whitespace, invisible characters and spacing around
  punctuation and numbers.
- :func:`fix_zwnj`: half-spaces (ZWNJ) for prefixes and suffixes such as
  می، ها، تر and ترین, and removal of misplaced ZWNJs.

>>> normalize("ﺍﻳﻦ ﻛﺘﺎﺏ ﻫﺎ  را ٣ بار خوانده ام .")
'این کتاب\\u200cها را ۳ بار خوانده\\u200cام.'
"""

from __future__ import annotations

import re
import unicodedata
from typing import Callable, Literal

from persianutils._util import ensure_str
from persianutils.characters import _DIGIT, _LETTER, _MARK, DIACRITICS, KASHIDA, ZWNJ
from persianutils.digits import to_arabic_digits, to_english_digits, to_persian_digits

__all__ = [
    "fix_spacing",
    "fix_zwnj",
    "normalize",
    "remove_diacritics",
    "remove_kashida",
    "unify_characters",
]

DigitStyle = Literal["fa", "en", "ar"]

# --------------------------------------------------------------------------
# Character tables
# --------------------------------------------------------------------------

# Arabic code points that Persian writes with a different letter. These are
# encoding differences: the text reads the same after the change.
_ARABIC_TO_PERSIAN = {
    "\u0643": "\u06a9",  # ARABIC LETTER KAF -> KEHEH (ک)
    "\u064a": "\u06cc",  # ARABIC LETTER YEH -> FARSI YEH (ی)
    "\u0649": "\u06cc",  # ALEF MAKSURA -> FARSI YEH (ی)
    "\u06c0": "\u0647\u0654",  # HEH WITH YEH ABOVE (ۀ) -> HEH + HAMZA ABOVE (هٔ)
    "\u06c2": "\u0647\u0654",  # HEH GOAL WITH HAMZA ABOVE -> HEH + HAMZA ABOVE
    "\u06c1": "\u0647",  # HEH GOAL (Urdu) -> HEH
    "\u06be": "\u0647",  # HEH DOACHASHMEE (Urdu) -> HEH
    "\u06d5": "\u0647",  # AE (Kurdish) -> HEH
}
_ARABIC_TO_PERSIAN_TABLE = str.maketrans(_ARABIC_TO_PERSIAN)


def _presentation_forms() -> dict[int, str]:
    """Map Arabic presentation forms (U+FB50-U+FDFF, U+FE70-U+FEFF) to letters.

    Built from the Unicode compatibility decompositions, so it covers every
    isolated, initial, medial and final form and every ligature.
    """
    table: dict[int, str] = {}
    for code_point in (*range(0xFB50, 0xFE00), *range(0xFE70, 0xFF00)):
        parts = unicodedata.decomposition(chr(code_point)).split()
        if not parts or parts[0] not in ("<isolated>", "<initial>", "<medial>", "<final>"):
            continue
        chars = "".join(chr(int(code, 16)) for code in parts[1:])
        if all(unicodedata.combining(char) or char in " " + KASHIDA for char in chars):
            # A spacing or kashida-borne form of a diacritic: keep the mark only.
            chars = chars.replace(" ", "").replace(KASHIDA, "")
        table[code_point] = chars.translate(_ARABIC_TO_PERSIAN_TABLE)
    return table


_UNIFY_TABLE: dict[int, str] = {
    **{ord(key): value for key, value in _ARABIC_TO_PERSIAN.items()},
    **_presentation_forms(),
}

# Lossy folding for search and matching: spelling variants become one form.
_FOLD_TABLE = str.maketrans(
    {
        "آ": "ا",
        "أ": "ا",
        "إ": "ا",
        "ٱ": "ا",
        "ؤ": "و",
        "ئ": "ی",
        "ة": "ه",
        "ۀ": "ه",
        "\u0653": None,  # madda above; NFC would rebuild "آ" from "ا" + madda
        "\u0654": None,  # hamza above, as in "هٔ"
        "\u0655": None,  # hamza below
    }
)

_DIACRITICS_TABLE = dict.fromkeys(map(ord, DIACRITICS))

_INVISIBLE = (
    "\u00ad"  # soft hyphen
    "\u061c"  # Arabic letter mark
    "\u200b"  # zero-width space
    "\u200e\u200f"  # left-to-right and right-to-left marks
    "\u202a\u202b\u202c\u202d\u202e"  # bidi embeddings and overrides
    "\u2060"  # word joiner
    "\u2066\u2067\u2068\u2069"  # bidi isolates
    "\ufeff"  # byte order mark / zero-width no-break space
)
_SPACES = (
    "\u00a0"  # no-break space
    "\u1680"  # ogham space mark
    "\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a"  # en quad .. hair space
    "\u202f"  # narrow no-break space
    "\u205f"  # medium mathematical space
    "\u3000"  # ideographic space
)
_SPACING_TABLE: dict[int, str | None] = {
    **dict.fromkeys(map(ord, _INVISIBLE)),
    **dict.fromkeys(map(ord, _SPACES), " "),
}


def _char_class_members(char_class: str) -> frozenset[str]:
    """Expand a regex character class body like "a-cx" into its characters."""
    members: set[str] = set()
    index = 0
    while index < len(char_class):
        if index + 2 < len(char_class) and char_class[index + 1] == "-":
            first, last = ord(char_class[index]), ord(char_class[index + 2])
            members.update(chr(code_point) for code_point in range(first, last + 1))
            index += 3
        else:
            members.add(char_class[index])
            index += 1
    return frozenset(members)


_LETTERS = _char_class_members(_LETTER)
_MARKS = _char_class_members(_MARK)
# Letters that do not join the following letter (Unicode joining types R and
# U), so a ZWNJ after them has no effect.
_NON_JOINING = frozenset(
    "\u0621\u0622\u0623\u0624\u0625\u0627\u0629\u062f\u0630\u0631\u0632\u0648"
    "\u0671\u0672\u0673\u0674\u0675\u0676\u0677"
    "\u06c0\u06cd\u06cf\u06d2\u06d3\u06d5\u06ee\u06ef"
    + "".join(chr(code_point) for code_point in range(0x0688, 0x069A))
    + "".join(chr(code_point) for code_point in range(0x06C3, 0x06CC))
)
_JOINS_NEXT = (_LETTERS - _NON_JOINING) | {KASHIDA}

# --------------------------------------------------------------------------
# Regular expressions
# --------------------------------------------------------------------------

L, M, D = _LETTER, _MARK, _DIGIT

# Spacing
_MULTIPLE_SPACES = re.compile(" {2,}")
_SPACES_AT_LINE_EDGES = re.compile("^ +| +$", re.MULTILINE)
_SPACE_BEFORE_PUNCTUATION = re.compile(
    rf"(?<=[{L}{M}{D}]) +(?=[،؛؟])|(?<=[{L}{M}۰-۹٠-٩]) +(?=[.,:;!?]+(?:\s|$|[{L}«»]))"
)
_SPACE_BEFORE_CLOSER = re.compile(rf"(?<=\S) +(?=»)|(?<=[{L}{M}{D}]) +(?=[)\]}}])")
_SPACE_AFTER_OPENER = re.compile(rf"(?<=«) +(?=\S)|(?<=[(\[{{]) +(?=[{L}{D}])")
_NO_SPACE_AFTER_PUNCTUATION = re.compile(
    rf"(?<=[،؛؟!:»)\]}}])(?=[{L}«])|(?<=[{L}{M}][,;?])(?=[{L}])"
)
# A period after a word of two or more letters; "ه.ش" and "ج.ا.ا" keep theirs.
_NO_SPACE_AFTER_PERIOD = re.compile(rf"(?<=[{L}]{{2}}\.)(?=[{L}])")
_NO_SPACE_BEFORE_OPENER = re.compile(rf"(?<=[{L}{M}])(?=[«(\[{{])")
# "۱۰درصد" -> "۱۰ درصد", but ordinals such as "۲۰ام" and "۳مین" stay.
_DIGIT_THEN_LETTER = re.compile(rf"(?<=[{D}])(?=[{L}])(?!(?:ام|امین|م|مین)(?![{L}{M}]))")
_LETTER_THEN_DIGIT = re.compile(rf"(?<=[{L}{M}])(?=[{D}])")

# Persian punctuation
_LATIN_PUNCTUATION_AFTER_LETTER = re.compile(rf"(?<=[{L}{M}])( *)([,;?]+)")
_PERSIAN_PUNCTUATION_TABLE = str.maketrans(",;?", "،؛؟")
_PERCENT_AFTER_DIGIT = re.compile("(?<=[۰-۹])%")

# ZWNJ
_ZWNJ_RUNS = re.compile("\u200c{2,}")
_ZWNJ_NEXT_TO_SPACE = re.compile("[ \u200c]*(?: \u200c|\u200c )[ \u200c]*")
_ZWNJ_CHAR = re.compile("\u200c")
_WORD_START = rf"(?<![{L}{M}\u200c])"
_PREFIX_MI = re.compile(rf"{_WORD_START}(ن?می) (?=[{L}][{M}]*[{L}])")
_SUFFIX = re.compile(
    rf"([{L}][{M}]*[{L}][{M}]*) "
    r"(هایشان|هایتان|هایمان|هایم|هایت|هایش|هایی|های|ها|ترهای|ترها|ترین|تری|تر)"
    rf"(?![{L}{M}\u200c])"
)
# Clitics after a silent final heh: "خانه ای" -> "خانه‌ای", "رفته اند" -> "رفته‌اند".
_HEH_CLITIC = re.compile(
    rf"(?<![{L}{M}\u200c])([{L}{M}\u200c]*[{L}][{M}]*ه[{M}]*) "
    r"(ای|ایم|اید|اند|ام|ات|اش|ی)"
    rf"(?![{L}{M}\u200c])"
)
# Short words ending in heh that are never followed by these clitics.
_HEH_CLITIC_EXCEPTIONS = frozenset({"که", "چه", "به", "نه"})


# --------------------------------------------------------------------------
# Steps
# --------------------------------------------------------------------------


def _nfc(text: str) -> str:
    if unicodedata.is_normalized("NFC", text):
        return text
    return unicodedata.normalize("NFC", text)


def _unify_characters(text: str) -> str:
    # NFC first so decomposed sequences ("ا" + madda) become single letters
    # before the table runs, and again afterwards for expanded ligatures.
    return _nfc(_nfc(text).translate(_UNIFY_TABLE))


def _remove_diacritics(text: str) -> str:
    return _nfc(text).translate(_DIACRITICS_TABLE)


def _persian_punctuation(text: str) -> str:
    text = _LATIN_PUNCTUATION_AFTER_LETTER.sub(
        lambda match: match.group(1) + match.group(2).translate(_PERSIAN_PUNCTUATION_TABLE), text
    )
    return _PERCENT_AFTER_DIGIT.sub("٪", text)


def _clean_whitespace_characters(text: str) -> str:
    return text.translate(_SPACING_TABLE)


def _fix_spacing(text: str) -> str:
    text = _clean_whitespace_characters(text)
    text = _MULTIPLE_SPACES.sub(" ", text)
    text = _SPACE_BEFORE_PUNCTUATION.sub("", text)
    text = _SPACE_BEFORE_CLOSER.sub("", text)
    text = _SPACE_AFTER_OPENER.sub("", text)
    text = _NO_SPACE_AFTER_PUNCTUATION.sub(" ", text)
    text = _NO_SPACE_AFTER_PERIOD.sub(" ", text)
    text = _NO_SPACE_BEFORE_OPENER.sub(" ", text)
    text = _DIGIT_THEN_LETTER.sub(" ", text)
    text = _LETTER_THEN_DIGIT.sub(" ", text)
    return _SPACES_AT_LINE_EDGES.sub("", text)


def _last_letter(word: str) -> str:
    for char in reversed(word):
        if char not in _MARKS:
            return char
    return ""


def _join_suffix(match: re.Match[str]) -> str:
    stem, suffix = match.group(1), match.group(2)
    joiner = ZWNJ if _last_letter(stem) in _JOINS_NEXT else ""
    return stem + joiner + suffix


def _join_heh_clitic(match: re.Match[str]) -> str:
    word, clitic = match.group(1), match.group(2)
    if word in _HEH_CLITIC_EXCEPTIONS:
        return match.group(0)
    return word + ZWNJ + clitic


def _is_arabic_script(char: str) -> bool:
    return (
        "\u0600" <= char <= "\u06ff"  # Arabic
        or "\u0750" <= char <= "\u077f"  # Arabic Supplement
        or "\u08a0" <= char <= "\u08ff"  # Arabic Extended-A
        or "\ufb50" <= char <= "\ufdff"  # Arabic Presentation Forms-A
        or "\ufe70" <= char <= "\ufeff"  # Arabic Presentation Forms-B
    )


def _keep_or_drop_zwnj(match: re.Match[str]) -> str:
    text, index = match.string, match.start()
    before = index - 1
    while before >= 0 and unicodedata.combining(text[before]):
        before -= 1
    previous = text[before] if before >= 0 else ""
    following = text[index + 1] if index + 1 < len(text) else ""
    if previous in _JOINS_NEXT and following in _LETTERS:
        return ZWNJ
    if (
        previous.isalpha()
        and following.isalpha()
        and not _is_arabic_script(previous)
        and not _is_arabic_script(following)
    ):
        # Between letters of another script (ZWNJ matters in Indic scripts,
        # for example): not ours to judge.
        return ZWNJ
    return ""


def _fix_zwnj(text: str) -> str:
    text = _ZWNJ_RUNS.sub(ZWNJ, text)
    text = _ZWNJ_NEXT_TO_SPACE.sub(" ", text)
    # Drop misplaced ZWNJs first, so the affix rules see clean word edges.
    # The rules below only add ZWNJs where they are needed.
    text = _ZWNJ_CHAR.sub(_keep_or_drop_zwnj, text)
    # Repeat until stable: in "بزرگ تر ها" the second suffix can only join
    # once the first has.
    for _ in range(8):
        joined = _PREFIX_MI.sub("\\1" + ZWNJ, text)
        joined = _SUFFIX.sub(_join_suffix, joined)
        joined = _HEH_CLITIC.sub(_join_heh_clitic, joined)
        if joined == text:
            break
        text = joined
    return text


# --------------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------------


def unify_characters(text: str) -> str:
    """Replace Arabic and compatibility code points with standard Persian ones.

    - Arabic yeh and alef maksura (ي ى) become Persian yeh (ی), and Arabic
      kaf (ك) becomes Persian kaf (ک).
    - Contextual forms and ligatures (ﺳ ﻼ ﷲ) become plain letters, so text
      copied from PDFs and old software becomes searchable.
    - "ۀ" is written as "هٔ" (heh + hamza above), so both spellings of the
      ezafe match.
    - The text is put in Unicode NFC form, so a decomposed "آ" (alef +
      madda) becomes one character.

    Only the encoding changes: the text reads the same afterwards.

    >>> unify_characters("علي كتاب")
    'علی کتاب'
    >>> unify_characters("ﺳﻼﻡ")
    'سلام'
    """
    return _unify_characters(ensure_str(text))


def remove_diacritics(text: str) -> str:
    """Remove harakat, tanwin, shadda, sukun and other combining marks.

    Letters that include a mark, such as "آ" and "أ", are kept. The hamza
    above heh in "هٔ" is kept as well, because it marks the ezafe.

    >>> remove_diacritics("کِتابٌ مُدَرِّس")
    'کتاب مدرس'
    """
    return _remove_diacritics(ensure_str(text))


def remove_kashida(text: str) -> str:
    """Remove kashida (tatweel), the stretching stroke in "سلـــام".

    >>> remove_kashida("سلـــام")
    'سلام'
    """
    return ensure_str(text).replace(KASHIDA, "")


def fix_spacing(text: str) -> str:
    """Clean up whitespace and the spacing around punctuation and numbers.

    - Removes invisible characters (bidi marks, zero-width spaces, byte
      order marks) and turns no-break and other Unicode spaces into spaces.
    - Collapses runs of spaces and trims spaces at line ends. Tabs and line
      breaks are kept.
    - In Persian text, removes the space before punctuation and closing
      brackets, adds one after punctuation, and keeps guillemets tight
      around the quotation: "سلام ، خوبی ؟" → "سلام، خوبی؟".
    - Separates numbers from words they touch ("۱۰درصد" → "۱۰ درصد") but
      keeps ordinals such as "۲۰ام" together.

    Latin text is left alone, so URLs, code and emoticons survive.

    >>> fix_spacing("سلام ،  دنیا !«  نقل قول  »")
    'سلام، دنیا! «نقل قول»'
    """
    return _fix_spacing(ensure_str(text))


def fix_zwnj(text: str) -> str:
    """Fix half-spaces (ZWNJ, نیم‌فاصله).

    - Joins the verb prefixes "می" and "نمی" to the verb: "می روم" →
      "می‌روم".
    - Joins plural, comparative and superlative suffixes: "کتاب ها" →
      "کتاب‌ها", "بزرگ تر" → "بزرگ‌تر", "بهترین ها" → "بهترین‌ها".
    - Joins clitics after a silent heh: "خانه ای" → "خانه‌ای", "رفته اند"
      → "رفته‌اند", "خانه ی" → "خانه‌ی".
    - Removes ZWNJs that do nothing: repeated ones, ones next to spaces or
      punctuation, and ones after letters that never join (ا د ذ ر ز ژ و).

    Words that are already written together without a ZWNJ ("میروم") are
    left as they are, because telling "میز" (table) from a verb needs a
    dictionary.

    >>> fix_zwnj("ما نمی دانستیم این ها بزرگ ترین دیوار ها هستند")
    'ما نمی\\u200cدانستیم این\\u200cها بزرگ\\u200cترین دیوارها هستند'
    """
    return _fix_zwnj(ensure_str(text))


_DIGIT_CONVERTERS: dict[str, Callable[[str], str]] = {
    "fa": to_persian_digits,
    "en": to_english_digits,
    "ar": to_arabic_digits,
}


def normalize(
    text: str,
    *,
    unify_characters: bool = True,
    remove_diacritics: bool = True,
    remove_kashida: bool = True,
    digits: DigitStyle | None = "fa",
    persian_punctuation: bool = True,
    fix_spacing: bool = True,
    fix_zwnj: bool = True,
    fold_variants: bool = False,
) -> str:
    """Normalize Persian text for display, search or NLP.

    Every step is on by default except ``fold_variants``. Turn steps off
    with keyword arguments.

    Args:
        text: The text to normalize.
        unify_characters: Replace Arabic and presentation-form code points
            with standard Persian letters. See :func:`unify_characters`.
        remove_diacritics: Remove harakat, tanwin and other marks. See
            :func:`remove_diacritics`.
        remove_kashida: Remove the stretching stroke "ـ".
        digits: ``"fa"`` for Persian digits, ``"en"`` for English (ASCII)
            digits, ``"ar"`` for Arabic-Indic digits, or ``None`` to leave
            digits alone.
        persian_punctuation: After Persian letters, write "," ";" "?" as
            "،" "؛" "؟", and write "%" after Persian digits as "٪".
        fix_spacing: Clean up whitespace and punctuation spacing. See
            :func:`fix_spacing`.
        fix_zwnj: Fix half-spaces. See :func:`fix_zwnj`.
        fold_variants: Also merge spelling variants, for search and
            matching: آ أ إ ٱ → ا, ؤ → و, ئ → ی, ة and ۀ → ه, and hamza
            marks are dropped. This loses information, so it is off by
            default.

    >>> normalize("كتابهاي  من ، شماره 3 .")
    'کتابهای من، شماره ۳.'
    >>> normalize("مسأله ی تأثیر آب", fold_variants=True)
    'مساله\\u200cی تاثیر اب'
    >>> normalize("قیمت: ۱۲۵٫۵ دلار", digits="en")
    'قیمت: 125.5 دلار'
    """
    ensure_str(text)
    if digits is not None and digits not in _DIGIT_CONVERTERS:
        raise ValueError(f"digits must be 'fa', 'en', 'ar' or None, not {digits!r}")
    compose = unify_characters or remove_diacritics
    if fix_spacing:
        # Invisible characters can sit between a letter and its marks.
        text = _clean_whitespace_characters(text)
    if unify_characters:
        text = _unify_characters(text)
    if fold_variants:
        text = text.translate(_FOLD_TABLE)
    if remove_diacritics:
        text = _remove_diacritics(text)
    if remove_kashida:
        text = text.replace(KASHIDA, "")
    if digits is not None:
        text = _DIGIT_CONVERTERS[digits](text)
    if compose:
        # Removing kashida can leave marks that compose ("و" + kashida + hamza).
        text = _nfc(text)
    # Spacing runs before and after the half-space and punctuation steps:
    # they need single spaces and no invisible characters, and they can
    # expose more spacing to fix (dropping the ZWNJ from "سلام" + ZWNJ + " ."
    # leaves "سلام .").
    if fix_spacing:
        text = _fix_spacing(text)
    if fix_zwnj:
        text = _fix_zwnj(text)
        if compose:
            text = _nfc(text)  # a dropped ZWNJ can leave a letter next to its mark
    if persian_punctuation:
        text = _persian_punctuation(text)
    if fix_spacing and (fix_zwnj or persian_punctuation):
        text = _fix_spacing(text)
    return text
