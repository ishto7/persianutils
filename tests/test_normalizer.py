from __future__ import annotations

import random
import unicodedata
from typing import Any

import pytest

import persianutils as pu

ZWNJ = "\u200c"


# --------------------------------------------------------------------------
# unify_characters
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("علي", "علی"),  # Arabic yeh
        ("موسى", "موسی"),  # alef maksura
        ("كتاب", "کتاب"),  # Arabic kaf
        ("ﺳﻼﻡ", "سلام"),  # presentation forms and the lam-alef ligature
        ("ﭘﮐﯾﮔﭼﮊ", "پکیگچژ"),  # Persian letters' presentation forms
        ("ﷲ", "الله"),
        ("﷼", "ریال"),
        ("خانۀ", "خانه\u0654"),  # ezafe written as heh + hamza above
        ("ا\u0653", "آ"),  # decomposed alef + madda becomes one letter
        ("ﹰ", "\u064b"),  # spacing form of a diacritic becomes the mark
        ("hello", "hello"),
        ("", ""),
    ],
)
def test_unify_characters(text: str, expected: str) -> None:
    assert pu.unify_characters(text) == expected


def test_unify_characters_leaves_no_presentation_forms() -> None:
    forms = "".join(chr(cp) for cp in (*range(0xFB50, 0xFE00), *range(0xFE70, 0xFF00)))
    unified = pu.unify_characters(forms)
    leftovers = {char for char in unified if "ﭐ" <= char <= "﷿" or "ﹰ" <= char <= "\ufeff"}
    # Only characters without a compatibility decomposition can remain.
    assert all(not unicodedata.decomposition(char) for char in leftovers)
    assert "ي" not in unified and "ك" not in unified


def test_unify_characters_output_is_nfc() -> None:
    text = unicodedata.normalize("NFD", "آیا مسئله\u0654 ﺁﺏ حل شد؟")
    assert unicodedata.is_normalized("NFC", pu.unify_characters(text))


# --------------------------------------------------------------------------
# remove_diacritics, remove_kashida
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("ک\u0650تاب\u064c م\u064fد\u064eر\u0650\u0651س", "کتاب مدرس"),
        ("س\u064fک\u0652ون", "سکون"),
        ("رحم\u0670ن", "رحمن"),  # superscript alef
        ("آب", "آب"),  # madda is part of the letter
        (unicodedata.normalize("NFD", "آب"), "آب"),  # even when decomposed
        ("تأثیر", "تأثیر"),
        ("خانه\u0654 من", "خانه\u0654 من"),  # the ezafe hamza stays
    ],
)
def test_remove_diacritics(text: str, expected: str) -> None:
    assert pu.remove_diacritics(text) == expected


def test_remove_kashida() -> None:
    assert pu.remove_kashida("سلـــام دنـیا") == "سلام دنیا"


# --------------------------------------------------------------------------
# fix_spacing
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("سلام   دنیا", "سلام دنیا"),
        ("  سلام  \n  دنیا  ", "سلام\nدنیا"),
        ("سلام\tدنیا", "سلام\tدنیا"),  # tabs are kept
        ("سلام\u00a0دنیا", "سلام دنیا"),  # no-break space
        ("سلام\u200fدنیا\u200e", "سلامدنیا"),  # bidi marks are dropped
        ("\ufeffسلام", "سلام"),  # byte order mark
        ("سلام ، خوبی ؟", "سلام، خوبی؟"),
        ("سلام،خوبی؟من خوبم", "سلام، خوبی؟ من خوبم"),
        ("سلام.خوبی", "سلام. خوبی"),
        ("سال ۱۴۰۳ ه.ش. و ج.ا.ا", "سال ۱۴۰۳ ه.ش. و ج.ا.ا"),  # abbreviations
        ("او گفت « سلام » و رفت", "او گفت «سلام» و رفت"),
        ("گفت:«سلام»", "گفت: «سلام»"),
        ("سلام ( دنیا )", "سلام (دنیا)"),
        ("تست(آزمایش)", "تست (آزمایش)"),
        ("صبر کن ...", "صبر کن..."),
        ("واقعا ؟!", "واقعا؟!"),
        ("۱۰درصد و عرض۶", "۱۰ درصد و عرض ۶"),
        ("قرن ۲۰ام و ۳مین بار", "قرن ۲۰ام و ۳مین بار"),  # ordinals stay joined
        ("ساعت ۱۲:۳۰ و عدد ۳.۱۴", "ساعت ۱۲:۳۰ و عدد ۳.۱۴"),
        ("خوبم :) و تو :(", "خوبم :) و تو :("),  # emoticons survive
        ("see example.com , ok ?", "see example.com , ok ?"),  # Latin is left alone
    ],
)
def test_fix_spacing(text: str, expected: str) -> None:
    assert pu.fix_spacing(text) == expected


# --------------------------------------------------------------------------
# fix_zwnj
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("می روم", "می\u200cروم"),
        ("نمی دانم", "نمی\u200cدانم"),
        ("کتاب ها", "کتاب\u200cها"),
        ("کتاب های من", "کتاب\u200cهای من"),
        ("این ها و آن ها", "این\u200cها و آن\u200cها"),
        ("بزرگ تر و بزرگ ترین", "بزرگ\u200cتر و بزرگ\u200cترین"),
        ("دیوار ها", "دیوارها"),  # ر never joins, so no ZWNJ is needed
        ("خانه ای", "خانه\u200cای"),
        ("رفته اند", "رفته\u200cاند"),
        ("خسته ام", "خسته\u200cام"),
        ("خانه ی من", "خانه\u200cی من"),
        ("گفت که ای کاش", "گفت که ای کاش"),  # "که" takes no clitic
        ("جام می و ساقی", "جام می و ساقی"),  # "می" before a one-letter word
        ("خشک و تر", "خشک و تر"),  # "تر" after a one-letter word
        ("کتاب\u200c\u200cها", "کتاب\u200cها"),  # repeated ZWNJ
        ("کتاب\u200c ها", "کتاب\u200cها"),  # ZWNJ next to a space
        ("\u200cسلام\u200c", "سلام"),  # ZWNJ at the edges
        ("سلام\u200c.", "سلام."),  # ZWNJ before punctuation
        ("دیوار\u200cها", "دیوارها"),  # ZWNJ after a non-joining letter
        ("کتاب\u200cها", "کتاب\u200cها"),
        ("क\u094d\u200cष", "क\u094d\u200cष"),  # Devanagari keeps its ZWNJ
        ("میز و میروم", "میز و میروم"),  # joined words are not split
    ],
)
def test_fix_zwnj(text: str, expected: str) -> None:
    assert pu.fix_zwnj(text) == expected


# --------------------------------------------------------------------------
# normalize
# --------------------------------------------------------------------------


def test_normalize_defaults() -> None:
    assert (
        pu.normalize("ﺍﻳﻦ ﻛﺘﺎﺏ ﻫﺎ  را ٣ بار خوانده ام .")
        == "این کتاب\u200cها را ۳ بار خوانده\u200cام."
    )


@pytest.mark.parametrize(
    ("digits", "expected"),
    [
        ("fa", "عدد ۱۲۳ و ۴۵۶ و ۳٫۱۴"),
        ("en", "عدد 123 و 456 و 3.14"),
        ("ar", "عدد ١٢٣ و ٤٥٦ و ٣٫١٤"),
        (None, "عدد 123 و ٤٥٦ و ۳٫۱۴"),
    ],
)
def test_normalize_digits(digits: Any, expected: str) -> None:
    assert pu.normalize("عدد 123 و ٤٥٦ و ۳٫۱۴", digits=digits) == expected


def test_normalize_rejects_unknown_digit_style() -> None:
    with pytest.raises(ValueError, match="digits"):
        pu.normalize("۱", digits="persian")  # type: ignore[arg-type]


def test_normalize_persian_punctuation() -> None:
    assert pu.normalize("سلام, خوبی? بله; ۵۰%") == "سلام، خوبی؟ بله؛ ۵۰٪"
    assert pu.normalize("hello, world?") == "hello, world?"
    assert pu.normalize("سلام, خوبی?", persian_punctuation=False) == "سلام, خوبی?"


def test_normalize_fold_variants() -> None:
    assert pu.normalize("مسأله تأثیر آب رئیس مؤمن خانۀ", fold_variants=True) == (
        "مساله تاثیر اب رییس مومن خانه"
    )
    assert pu.normalize("مسأله تأثیر آب") == "مسأله تأثیر آب"


@pytest.mark.parametrize(
    ("option", "text", "kept"),
    [
        ("unify_characters", "علي", "علي"),
        ("remove_diacritics", "ک\u0650تاب", "ک\u0650تاب"),
        ("remove_kashida", "سلـام", "سلـام"),
        ("fix_spacing", "سلام  دنیا", "سلام  دنیا"),
        ("fix_zwnj", "می روم", "می روم"),
    ],
)
def test_normalize_steps_can_be_turned_off(option: str, text: str, kept: str) -> None:
    options: dict[str, Any] = {option: False}
    assert pu.normalize(text, **options) == kept
    assert pu.normalize(text) != kept


SAMPLES = [
    "ﺍﻳﻦ ﻛﺘﺎﺏ ﻫﺎ  را ٣ بار خوانده ام .",
    "ما نمی دانستیم این ها بزرگ ترین دیوار ها هستند",
    "سلام\u200c . خوبی ؟؟ «  نقل  » ( پرانتز ) ۱۰درصد",
    "visit example.com/page2 now: https://x.y?a=1,2",
    "ک\u0650تاب\u064c م\u064fد\u064eر\u0650\u0651س و سلـــام و خانۀ ما و علي و كتاب",
    "\u200cمی\u200c روم\u200c\u200c خانه ای \u200c ها",
]


@pytest.mark.parametrize("text", SAMPLES)
def test_normalize_is_idempotent(text: str) -> None:
    once = pu.normalize(text)
    assert pu.normalize(once) == once


IDEMPOTENCE_PIECES = [
    "می", "نمی", "ها", "های", "تر", "ترین", "ای", "ام", "اند", "ی", "خانه", "کتاب",
    "دیوار", "بزرگ", "که", "و", "۱۰", "3", "٤", "،", ",", ".", "...", "؟", "?", "!",
    ":", ";", "؛", "«", "»", "(", ")", "[", "]", '"', "%", " ", "  ", "\t", "\n",
    "\u00a0", ZWNJ, "\u200f", "ﻛ", "ي", "ﻵ", "ﷲ", "ـ", "آ", "ۀ", "ة", "ا",
    "\u064e", "\u0653", "\u0654", "\u0655", "ه.ش", "abc", "क\u094d", "ष",
]  # fmt: skip


@pytest.mark.parametrize(
    "options",
    [
        {},
        {"fold_variants": True},
        {"digits": "en"},
        {"fix_zwnj": False},
        {"fix_spacing": False},
        {"persian_punctuation": False},
        {"unify_characters": False, "remove_diacritics": False},
    ],
    ids=repr,
)
def test_normalize_is_idempotent_on_random_text(options: dict[str, Any]) -> None:
    rng = random.Random(1403)
    for _ in range(1500):
        pieces = rng.choices(IDEMPOTENCE_PIECES, k=rng.randrange(1, 14))
        text = "".join(pieces)
        once = pu.normalize(text, **options)
        assert pu.normalize(once, **options) == once, pieces


@pytest.mark.parametrize(
    "function",
    [
        pu.normalize,
        pu.unify_characters,
        pu.remove_diacritics,
        pu.remove_kashida,
        pu.fix_spacing,
        pu.fix_zwnj,
    ],
)
def test_non_string_input_raises_type_error(function: Any) -> None:
    with pytest.raises(TypeError):
        function(None)
