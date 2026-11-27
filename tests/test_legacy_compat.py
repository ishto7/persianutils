"""The 1.x API must keep behaving like the published persianutils 1.0.0.

``fixtures/v1_0_0_reference.json`` was captured from the 1.0.0 wheel on PyPI
(see ``fixtures/make_v1_reference.py``). Every difference from it is listed
in this file, and each one corrects a typo in the 1.0.0 character tables.
"""

from __future__ import annotations

import ast
import importlib
import json
import random
import re
import warnings
from pathlib import Path
from typing import Any

import pytest

import persianutils as pu
from persianutils import ArabicAlphabet, PersianAlphabet, processes

FIXTURE = Path(__file__).parent / "fixtures" / "v1_0_0_reference.json"
REFERENCE: dict[str, Any] = json.loads(FIXTURE.read_text(encoding="utf-8"))

# Arabic-Indic digits that 1.0.0 left unconverted (it listed Persian digits
# instead of these in EASTERN_ARABIC_NUMERALS; only 4 and 6 were right).
MISSED_DIGITS = (0, 1, 2, 3, 5, 7, 8, 9)

# input character -> new output, for every character whose output changed.
STANDARDIZE_FIXES = {
    "ﻐ": "غ",  # GHAIN MEDIAL FORM: 1.0.0 turned it into LAM
    "ﻠ": "ل",  # LAM MEDIAL FORM: 1.0.0 left it unchanged
    **{chr(0x0660 + d): chr(0x06F0 + d) for d in MISSED_DIGITS},
}
WORD2VEC_FIXES = {
    "ﻐ": "غ",
    "ﻠ": "ل",
    **{chr(0x0660 + d): f" {PersianAlphabet.NUMERALS_WRITINGS[d]} " for d in MISSED_DIGITS},
}


def expected_table(name: str, fixes: dict[str, str]) -> dict[str, str]:
    table: dict[str, str] = dict(REFERENCE[name])
    table.update(fixes)
    return table


STANDARDIZE_TABLE = expected_table("standardize", STANDARDIZE_FIXES)
WORD2VEC_TABLE = expected_table("standardize4Word2vec", WORD2VEC_FIXES)


def reference_algorithm(text: str, table: dict[str, str]) -> str:
    """The 1.0.0 implementation: one regex alternation over escaped keys."""
    pattern = re.compile("(" + "|".join(map(re.escape, table)) + ")")
    return pattern.sub(lambda match: table[match.group()], text)


def all_code_points() -> str:
    return "".join(chr(cp) for cp in range(0x110000) if not 0xD800 <= cp <= 0xDFFF)


def test_fixes_only_touch_characters_1_0_0_mishandled() -> None:
    for char in STANDARDIZE_FIXES:
        assert REFERENCE["standardize"].get(char, char) != STANDARDIZE_FIXES[char]
    for char in WORD2VEC_FIXES:
        assert REFERENCE["standardize4Word2vec"].get(char, char) != WORD2VEC_FIXES[char]


def test_standardize_matches_1_0_0_on_every_code_point() -> None:
    text = all_code_points()
    expected = "".join(STANDARDIZE_TABLE.get(char, char) for char in text)
    assert pu.standardize(text) == expected


def test_standardize4word2vec_matches_1_0_0_on_every_code_point() -> None:
    text = all_code_points()
    expected = "".join(WORD2VEC_TABLE.get(char, char) for char in text)
    assert pu.standardize4Word2vec(text) == expected


def test_random_text_matches_1_0_0_algorithm() -> None:
    rng = random.Random(1403)
    alphabet = [
        *(WORD2VEC_TABLE.keys() - {" +"}),
        *" ++  ",
        *"سلام علیکم کتاب\u200cها abc",
    ]
    for _ in range(3000):
        text = "".join(rng.choice(alphabet) for _ in range(rng.randrange(40)))
        assert pu.standardize(text) == reference_algorithm(text, STANDARDIZE_TABLE)
        assert pu.standardize4Word2vec(text) == reference_algorithm(text, WORD2VEC_TABLE)


@pytest.mark.parametrize(
    ("text", "standardized", "for_word2vec"),
    [
        # The examples from the 1.0.0 README.
        ("سلام\u064c علیکم!", "سلام علیکم!", "سلام علیکم "),
        ("2", "۲", " دو "),
        # Documented 1.0 behaviour that stays as it was.
        ("۳٫۱۴", "۳۱۴", " سه  یک  چهار "),
        ("آب أو إن", "اب او ان", "اب او ان"),
        ("a  +b + c", "a  +b + c", "a  b  c"),
        ("", "", ""),
    ],
)
def test_documented_examples(text: str, standardized: str, for_word2vec: str) -> None:
    assert pu.standardize(text) == standardized
    assert pu.standardize4Word2vec(text) == for_word2vec


@pytest.mark.parametrize("value", [None, 1, b"bytes", ["list"]])
def test_non_string_input_raises_type_error(value: Any) -> None:
    with pytest.raises(TypeError):
        pu.standardize(value)
    with pytest.raises(TypeError):
        pu.standardize4Word2vec(value)


def without_identity_entries(table: dict[str, str]) -> dict[str, str]:
    # 1.0.0's table mapped the Persian digits to themselves (a side effect of
    # the wrong EASTERN_ARABIC_NUMERALS); those no-op entries are gone now.
    return {key: value for key, value in table.items() if key != value}


def test_processes_module_tables_match_1_0_0() -> None:
    assert without_identity_entries(processes.replacementDict) == without_identity_entries(
        STANDARDIZE_TABLE
    )
    assert processes.replacementDict4Word2vec == WORD2VEC_TABLE
    assert [rule["to_be"] for rule in processes.to_reform] == ["", "ا", "ی", "ک", "لا", "ه"]


def test_processes_module_regexes_agree_with_functions() -> None:
    from persianutils.processes import replacementRegex, replacementRegex4Word2vec

    text = "ﻛﺘﺎﺏ ٤ و 5 ؟ ﻐ" + all_code_points()[0x600:0x700]
    std = replacementRegex.sub(lambda m: processes.replacementDict[m.group()], text)
    w2v = replacementRegex4Word2vec.sub(
        lambda m: processes.replacementDict4Word2vec[m.group()], text
    )
    assert std == pu.standardize(text)
    assert w2v == pu.standardize4Word2vec(text)

    namespace: dict[str, Any] = {}
    exec("from persianutils.processes import *", namespace)
    assert {"standardize", "replacementRegex", "replacementDict", "to_reform"} <= namespace.keys()


def expected_constants(module_name: str) -> dict[str, Any]:
    values = {
        name: ast.literal_eval(text) for name, text in REFERENCE["constants"][module_name].items()
    }
    if module_name == "persianutils.PersianAlphabet":
        values["GAF"] = "گ"
        values["ALPHABETIC_ORDER"] = {
            letter: position
            for position, letter in enumerate("ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی", start=1)
        }
    else:
        values["LAM_MEDIAL"] = "ﻠ"
        values["EASTERN_ARABIC_NUMERALS"] = [chr(0x0660 + d) for d in range(10)]
        values["SHAPED_FORMS"]["ل"] = ("ﻝ", "ﻟ", "ﻠ", "ﻞ")
    return values


@pytest.mark.parametrize("module", [PersianAlphabet, ArabicAlphabet], ids=lambda m: m.__name__)
def test_alphabet_constants_match_1_0_0(module: Any) -> None:
    for name, value in expected_constants(module.__name__).items():
        assert getattr(module, name) == value, name


def test_1_0_import_paths_still_work() -> None:
    import persianutils

    assert persianutils.standardize is processes.standardize
    assert persianutils.standardize4Word2vec is processes.standardize4Word2vec
    # Importing the package used to make these submodules available too.
    assert persianutils.PersianAlphabet is PersianAlphabet
    assert persianutils.ArabicAlphabet is ArabicAlphabet
    assert persianutils.processes is processes

    namespace: dict[str, Any] = {}
    exec("from persianutils.ArabicAlphabet import *", namespace)
    exec("from persianutils.PersianAlphabet import *", namespace)
    assert namespace["ALEF_MAKSURA"] == "ى"
    assert namespace["HE2"] == "ه"


def test_package_sources_compile_without_warnings() -> None:
    package_dir = Path(pu.__file__).parent
    for path in sorted(package_dir.glob("*.py")):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            compile(path.read_text(encoding="utf-8"), str(path), "exec")


def test_reimport_is_clean() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        importlib.reload(processes)
    assert pu.standardize("ك") == "ک"
