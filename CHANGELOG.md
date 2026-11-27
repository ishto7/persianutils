# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## 1.1.0 - Unreleased

### Added

- `normalize()`: a configurable normalizer. Steps: unify Arabic and contextual-form code points,
  remove diacritics and kashida, unify digits, use Persian punctuation, fix spacing, fix
  half-spaces (ZWNJ), and optionally fold spelling variants for search. Each step is also a
  function: `unify_characters()`, `remove_diacritics()`, `remove_kashida()`, `fix_spacing()`,
  `fix_zwnj()`.
- Digit conversion: `to_persian_digits()`, `to_english_digits()`, `to_arabic_digits()`.
- Numbers: `number_to_words()`, `number_to_ordinal()`, `words_to_number()`, `format_number()`.
- Jalali calendar: `JalaliDate`, `to_jalali()`, `to_gregorian()`, and `is_leap_year()`,
  `days_in_month()`, `MONTH_NAMES`, `WEEKDAY_NAMES` in `persianutils.jalali`.
- Text tools: `word_tokenize()`, `sentence_tokenize()`, `sort_key()`, `is_persian()`,
  `has_persian()`, `slugify()`, `STOPWORDS`.
- `persianutils.characters`: alphabet, digit, diacritic and ZWNJ constants.
- Type hints and a `py.typed` marker.
- A test suite, run by CI on Python 3.9 to 3.14.

### Changed

- `standardize()` and `standardize4Word2vec()` use `str.translate` and run 3 to 7 times faster.
  Their output is unchanged apart from the fixes below.
- Packaging moved from `setup.py` to `pyproject.toml`.
- Python 3.9 or later is required. Older interpreters keep getting 1.0.0 from pip.

### Fixed

- `standardize()` and `standardize4Word2vec()` turned `ﻐ` (U+FED0, ghain medial form) into `ل`
  and left `ﻠ` (U+FEE0, lam medial form) unchanged, because `ArabicAlphabet.LAM_MEDIAL` held the
  ghain code point.
- Both functions left the Arabic-Indic digits 0, 1, 2, 3, 5, 7, 8 and 9 unconverted, because
  `ArabicAlphabet.EASTERN_ARABIC_NUMERALS` listed Persian digits instead.
- `PersianAlphabet.GAF` was `ق` (U+0642) instead of `گ` (U+06AF), so `ALPHABETIC_ORDER` ranked
  `ق` as `گ` and had no entry for `گ`.
- Importing the package no longer emits `SyntaxWarning: invalid escape sequence` on Python 3.12
  and later.

## 1.0.0 - 2023-08-21

### Changed

- Packaging updates and a contributing guide. No API changes.

## 0.1.0 to 0.1.2 - 2018-12-30

### Changed

- `standardize()` and `standardize4Word2vec()` moved into `persianutils.processes`. Both are
  still importable from `persianutils`.

## 0.0.2 and 0.0.3 - 2018-08-02

### Added

- First release: `standardize()`, `standardize4Word2vec()`, and the `PersianAlphabet` and
  `ArabicAlphabet` constants.
