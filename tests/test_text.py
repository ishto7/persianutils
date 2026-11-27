from __future__ import annotations

import random
from importlib import metadata
from pathlib import Path

import pytest

import persianutils as pu
from persianutils.characters import PERSIAN_ALPHABET

ZWNJ = "\u200c"

# --------------------------------------------------------------------------
# Detection
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "persian", "contains_persian"),
    [
        ("سلام", True, True),
        ("علی\u200cرضا محمدی", True, True),
        ("علي", True, True),  # Arabic yeh still counts
        ("ﺳﻼﻡ", True, True),  # presentation forms too
        ("ک\u0650تاب\u064c", True, True),  # diacritics are ignored
        ("سلـــام", True, True),  # kashida is ignored
        ("سلام ۱۲۳!", True, True),
        ("Hello سلام", False, True),
        ("Hello", False, False),
        ("۱۲۳", False, False),
        ("", False, False),
        ("مرحبا", True, True),  # the script cannot tell Arabic from Persian
    ],
)
def test_detection(text: str, persian: bool, contains_persian: bool) -> None:
    assert pu.is_persian(text) is persian
    assert pu.has_persian(text) is contains_persian


# --------------------------------------------------------------------------
# Tokenization
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "tokens"),
    [
        ("کتاب\u200cها را خواندم، ۳ بار!", ["کتاب\u200cها", "را", "خواندم", "،", "۳", "بار", "!"]),
        ("قیمت ۱٬۲۵۰٫۵ تومان", ["قیمت", "۱٬۲۵۰٫۵", "تومان"]),
        ("تاریخ 1403/01/01 ساعت 12:30", ["تاریخ", "1403/01/01", "ساعت", "12:30"]),
        ("«سلام»؟", ["«", "سلام", "»", "؟"]),
        (
            "ک\u0650تاب\u064c م\u064fد\u064eر\u0650\u0651س",
            ["ک\u0650تاب\u064c", "م\u064fد\u064eر\u0650\u0651س"],
        ),  # diacritics stay in the word
        ("iPhone 15 خریدم", ["iPhone", "15", "خریدم"]),
        ("  \n ", []),
        ("می\u200c روم", ["می", "روم"]),  # a stray ZWNJ next to a space is dropped
    ],
)
def test_word_tokenize(text: str, tokens: list[str]) -> None:
    assert pu.word_tokenize(text) == tokens


@pytest.mark.parametrize(
    ("text", "sentences"),
    [
        (
            "سلام! حالت چطور است؟ من خوبم.\nخداحافظ",
            ["سلام!", "حالت چطور است؟", "من خوبم.", "خداحافظ"],
        ),
        ("عدد ۳.۱۴ است. بله", ["عدد ۳.۱۴ است.", "بله"]),
        ("او گفت «بیا.» و رفت.", ["او گفت «بیا.»", "و رفت."]),
        ("صبر کن… باشه", ["صبر کن…", "باشه"]),
        ("بدون نقطه", ["بدون نقطه"]),
        ("", []),
    ],
)
def test_sentence_tokenize(text: str, sentences: list[str]) -> None:
    assert pu.sentence_tokenize(text) == sentences


# --------------------------------------------------------------------------
# Sorting
# --------------------------------------------------------------------------


def test_sort_key_follows_the_persian_alphabet() -> None:
    letters = list("آ" + PERSIAN_ALPHABET)
    shuffled = letters[:]
    random.Random(1).shuffle(shuffled)
    assert sorted(shuffled, key=pu.sort_key) == letters
    # Plain sorting gets it wrong: پ چ ژ ک گ ی are outside the Arabic block.
    assert sorted(shuffled) != letters


@pytest.mark.parametrize(
    "ordered",
    [
        ["آب", "اب", "باد"],  # آ before ا
        ["کتاب خانه", "کتابخانه"],  # a space sorts first
        ["10 سیب", "۲ سیب", "سیب"],  # digits before letters, compared digit by digit
        ["علي", "علیرضا"],  # Arabic yeh sorts as ی
        ["ک\u0650تاب", "کتابها"],  # diacritics are ignored
        ["سلام", "hello"],  # Persian before Latin
        ["مسیر", "مسیله", "مسئله"],  # ئ sorts with ی, just after it
    ],
)
def test_sort_key_orders(ordered: list[str]) -> None:
    assert sorted(reversed(ordered), key=pu.sort_key) == ordered


def test_sort_key_is_a_total_order_on_variants() -> None:
    words = ["کتاب", "كتاب", "کتاب", "ﻛﺘﺎﺏ"]
    assert sorted(words, key=pu.sort_key) == sorted(sorted(words, key=pu.sort_key), key=pu.sort_key)


# --------------------------------------------------------------------------
# Slugs
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "slug"),
    [
        ("آموزش پایتون: قسمت ۱۲!", "آموزش-پایتون-قسمت-12"),
        ("کتاب\u200cهای Python", "کتاب-های-python"),
        ("  سلام   دنیا  ", "سلام-دنیا"),
        ("علي و كتاب", "علی-و-کتاب"),
        ("«نقل قول» — تست", "نقل-قول-تست"),
        ("---", ""),
    ],
)
def test_slugify(text: str, slug: str) -> None:
    assert pu.slugify(text) == slug


def test_slugify_separator() -> None:
    assert pu.slugify("سلام دنیا", separator="_") == "سلام_دنیا"


# --------------------------------------------------------------------------
# Stopwords
# --------------------------------------------------------------------------


def test_stopwords() -> None:
    assert {"و", "در", "به", "از", "که", "را", "است", "این", "آن", "می\u200cشود"} <= pu.STOPWORDS
    assert "کتاب" not in pu.STOPWORDS
    # Spelled the way normalize() writes words, so normalized tokens match.
    for word in pu.STOPWORDS:
        assert pu.normalize(word) == word, word


# --------------------------------------------------------------------------
# Package surface
# --------------------------------------------------------------------------


def test_public_api_is_importable() -> None:
    for name in pu.__all__:
        assert hasattr(pu, name), name


def test_version_matches_installed_metadata() -> None:
    assert metadata.version("persianutils") == pu.__version__


def test_package_is_typed() -> None:
    assert (Path(pu.__file__).parent / "py.typed").is_file()


@pytest.mark.parametrize(
    "function",
    [
        pu.is_persian,
        pu.has_persian,
        pu.word_tokenize,
        pu.sentence_tokenize,
        pu.sort_key,
        pu.slugify,
    ],
)
def test_non_string_input_raises_type_error(function: object) -> None:
    with pytest.raises(TypeError):
        function(None)  # type: ignore[operator]
