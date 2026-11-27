# PersianUtils

[![PyPI](https://img.shields.io/pypi/v/persianutils)](https://pypi.org/project/persianutils/)
[![Python](https://img.shields.io/pypi/pyversions/persianutils)](https://pypi.org/project/persianutils/)
[![CI](https://github.com/ishto7/persianutils/actions/workflows/ci.yml/badge.svg)](https://github.com/ishto7/persianutils/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Clean up and convert Persian (Farsi) text: normalization, half-spaces (ZWNJ), digits, numbers in
words, Jalali dates, tokenization and Persian alphabetical sorting. Pure Python, no dependencies,
typed.

## Why

The same Persian word can be stored many ways. Arabic keyboards type `ي` and `ك` instead of `ی` and
`ک`; text copied from PDFs carries contextual forms such as `ﺳﻼﻡ`; digits come in three scripts;
half-spaces are typed as spaces or not at all. The strings look alike but do not compare equal, so
search, deduplication and NLP models miss matches. PersianUtils rewrites text into one standard form
and handles the conversions Persian software needs.

## Install

```bash
pip install persianutils
```

Requires Python 3.9 or later. Python 3.6 to 3.8 users get 1.0.0, which pip selects automatically.

## Quick start

```python
>>> import persianutils as pu
>>> pu.normalize("ﺍﻳﻦ ﻛﺘﺎﺏ ﻫﺎ  را ٣ بار خوانده ام .")
'این کتاب\u200cها را ۳ بار خوانده\u200cام.'
>>> pu.number_to_words(1404)
'هزار و چهارصد و چهار'
>>> pu.words_to_number("دو میلیون و سیصد هزار")
2300000
>>> pu.to_jalali(2025, 3, 21).strftime("%A %-d %B %Y", digits="fa")
'جمعه ۱ فروردین ۱۴۰۴'
>>> pu.to_english_digits("۰۹۱۲۳۴۵۶۷۸۹")
'09123456789'

```

The examples print strings with `repr()`, so a half-space (ZWNJ, U+200C) shows as `\u200c`. Every
example in this README runs as a test.

## Normalization

`normalize()` runs the steps below in a fixed order. Each one is on by default except
`fold_variants`, and each can be turned off with a keyword argument.

| Option | Default | Effect |
| --- | --- | --- |
| `unify_characters` | `True` | Arabic code points and contextual forms become Persian letters: `ي`→`ی`, `ك`→`ک`, `ﺳﻼﻡ`→`سلام`, `ۀ`→`هٔ` |
| `remove_diacritics` | `True` | `کِتابٌ`→`کتاب`; letters such as `آ` and `أ` keep their marks |
| `remove_kashida` | `True` | `سلـــام`→`سلام` |
| `digits` | `"fa"` | `"fa"` Persian, `"en"` English (ASCII), `"ar"` Arabic-Indic, `None` unchanged |
| `persian_punctuation` | `True` | After Persian words, `,` `;` `?` become `،` `؛` `؟`; `%` after Persian digits becomes `٪` |
| `fix_spacing` | `True` | Collapses spaces, drops invisible characters (bidi marks, BOM), fixes spaces around punctuation and between numbers and words |
| `fix_zwnj` | `True` | Half-spaces: `می روم`→`می‌روم`, `کتاب ها`→`کتاب‌ها`, `بزرگ تر`→`بزرگ‌تر`, `خانه ای`→`خانه‌ای` |
| `fold_variants` | `False` | For search and matching only, since it changes spelling: `آ أ إ`→`ا`, `ؤ`→`و`, `ئ`→`ی`, `ة ۀ`→`ه` |

```python
>>> pu.normalize("علي در خانه ما ۱۲ کتاب دارد , ولي نمي خواند")
'علی در خانه ما ۱۲ کتاب دارد، ولی نمی\u200cخواند'
>>> pu.normalize("قیمت: ۱۲۵٫۵ دلار", digits="en")
'قیمت: 125.5 دلار'
>>> pu.normalize("مسأله ی تأثیر آب", fold_variants=True)
'مساله\u200cی تاثیر اب'

```

`normalize()` is idempotent: running it again changes nothing. Spacing and punctuation rules apply
only next to Persian letters, so Latin text, URLs and emoticons such as `:)` keep their spacing.
Digit conversion applies everywhere, URLs included; pass `digits=None` to keep digits as they are.

Each step is also a function:

```python
>>> pu.unify_characters("ﻋﻠﻲ ﻛﺘﺎﺏ")
'علی کتاب'
>>> pu.remove_diacritics("کِتابٌ مُدَرِّس")
'کتاب مدرس'
>>> pu.fix_spacing("سلام ،  دنیا !«  نقل قول  »")
'سلام، دنیا! «نقل قول»'
>>> pu.fix_zwnj("ما نمی دانستیم این ها بزرگ ترین دیوار ها هستند")
'ما نمی\u200cدانستیم این\u200cها بزرگ\u200cترین دیوارها هستند'

```

`fix_zwnj()` adds no half-space after letters that never join the next letter (`دیوارها`), and
leaves words already written together (`میروم`) as they are, because splitting them needs a
dictionary: `میز` (table) also starts with `می`.

## Digits

```python
>>> pu.to_persian_digits("Tel: 021-12345678")
'Tel: ۰۲۱-۱۲۳۴۵۶۷۸'
>>> pu.to_persian_digits(1403)
'۱۴۰۳'
>>> pu.to_english_digits("۱٬۲۵۰٫۵")
'1,250.5'
>>> pu.to_arabic_digits("2024")
'٢٠٢٤'

```

`to_english_digits()` also turns the Persian decimal and thousands separators (`٫` `٬`) into `.` and
`,`, so its output parses with `int()`, `float()` or `Decimal()`.

## Numbers in words

```python
>>> pu.number_to_words(1403)
'هزار و چهارصد و سه'
>>> pu.number_to_words("۱۲۵۰۰۰۰۰۰۰")
'یک میلیارد و دویست و پنجاه میلیون'
>>> pu.number_to_words(-2.75)
'منفی دو و هفتاد و پنج صدم'
>>> pu.number_to_ordinal(23)
'بیست و سوم'
>>> pu.number_to_ordinal(30, prenominal=True)
'سی\u200cامین'
>>> pu.words_to_number("بیست و سومین")
23
>>> pu.words_to_number("صدوبیست و پنج")
125
>>> pu.words_to_number("۲٫۵ میلیون")
2500000
>>> pu.format_number(1250000)
'۱٬۲۵۰٬۰۰۰'
>>> pu.format_number(1234567.891, digits="en")
'1,234,567.891'

```

`number_to_words()` handles integers below 10³⁶, negative numbers and decimal fractions.
`words_to_number()` reads words with or without spaces and half-spaces, Arabic letter variants,
ordinals, `منفی`, and digits next to scale words; it raises `ValueError` for text that is not a whole
number.

## Jalali dates

```python
>>> from datetime import date, timedelta
>>> d = pu.to_jalali(date(2025, 3, 21))
>>> d
JalaliDate(1404, 1, 1)
>>> d.strftime("%A %-d %B %Y")
'جمعه 1 فروردین 1404'
>>> d.strftime("%Y/%m/%d", digits="fa")
'۱۴۰۴/۰۱/۰۱'
>>> pu.to_gregorian(1357, 11, 22)
datetime.date(1979, 2, 11)
>>> pu.JalaliDate.parse("۱۴۰۳/۱۲/۳۰") + timedelta(days=1)
JalaliDate(1404, 1, 1)
>>> from persianutils.jalali import days_in_month, is_leap_year
>>> is_leap_year(1403), days_in_month(1404, 12)
(True, 29)

```

`JalaliDate` behaves like `datetime.date`: it is immutable and hashable, compares and sorts,
supports `timedelta` arithmetic, and has `today()`, `weekday()` (Saturday is 0), `isoformat()` and
`replace()`. `strftime()` understands `%Y %y %m %d %j %B %A %%`, and `%-m`, `%-d`, `%-j` drop the
leading zero.

Leap years follow Borkowski's 33-year rule with break years, the algorithm behind jalaali-js. The
tests check it against [jdatetime](https://github.com/slashmili/python-jalali) on every day of the
years 1200 to 1599; supported years are 1 to 3177. For times, time zones and Jalali `datetime`, use
jdatetime.

## Tokenizing, sorting and more

```python
>>> pu.word_tokenize("کتاب‌ها را خواندم، ۳ بار!")
['کتاب\u200cها', 'را', 'خواندم', '،', '۳', 'بار', '!']
>>> pu.sentence_tokenize("سلام! حالت چطور است؟ من خوبم.")
['سلام!', 'حالت چطور است؟', 'من خوبم.']
>>> sorted(["ژاله", "زهرا", "پریا", "بهار", "آرش"])
['آرش', 'بهار', 'زهرا', 'پریا', 'ژاله']
>>> sorted(["ژاله", "زهرا", "پریا", "بهار", "آرش"], key=pu.sort_key)
['آرش', 'بهار', 'پریا', 'زهرا', 'ژاله']
>>> pu.is_persian("علی‌رضا محمدی"), pu.is_persian("Ali"), pu.has_persian("Hello سلام")
(True, False, True)
>>> pu.slugify("آموزش پایتون: قسمت ۱۲!")
'آموزش-پایتون-قسمت-12'
>>> [w for w in pu.word_tokenize("من کتاب را در کتابخانه گذاشتم") if w not in pu.STOPWORDS]
['کتاب', 'کتابخانه', 'گذاشتم']

```

- `sort_key` puts Persian words in dictionary order. Plain `sorted()` compares code points, which
  places `پ چ ژ ک گ ی` after the rest of the alphabet.
- `is_persian()` checks that every letter is Persian, which suits validating a name field. Digits,
  spaces, punctuation and diacritics are ignored.
- `STOPWORDS` holds 260 function words (pronouns, prepositions, conjunctions, auxiliary verbs) in
  the spelling `normalize()` produces.
- `persianutils.characters` exports `PERSIAN_ALPHABET`, `PERSIAN_DIGITS`, `ZWNJ`, `DIACRITICS` and
  related constants.

PersianUtils does not do stemming, lemmatization or part-of-speech tagging; for those, see
[hazm](https://github.com/roshan-research/hazm).

## Compatibility with 1.0

Code written for 1.0 keeps working: `standardize()`, `standardize4Word2vec()`, and the
`persianutils.PersianAlphabet`, `persianutils.ArabicAlphabet` and `persianutils.processes` modules.

```python
>>> pu.standardize("سلامٌ علیکم!")
'سلام علیکم!'
>>> pu.standardize4Word2vec("سلامٌ علیکم!")
'سلام علیکم '

```

The test suite compares both functions with the published 1.0.0 on every Unicode code point and on
random text. They return the same output, 3 to 7 times faster, except for characters 1.0.0
mishandled because of typos in its tables:

| Input | 1.0.0 | 2.0.0 |
| --- | --- | --- |
| `ﻐ` (U+FED0, ghain medial form) | `ل` | `غ` |
| `ﻠ` (U+FEE0, lam medial form) | unchanged | `ل` |
| Arabic-Indic digits `٠ ١ ٢ ٣ ٥ ٧ ٨ ٩` | unchanged | Persian digits, as `٤` and `٦` already were |

Three constants had the same typos: `PersianAlphabet.GAF` was `ق` and is now `گ` (which also fixes
`ALPHABETIC_ORDER`), `ArabicAlphabet.LAM_MEDIAL` pointed at the ghain form, and
`ArabicAlphabet.EASTERN_ARABIC_NUMERALS` listed Persian digits.

`standardize()` discards information by design, so prefer `normalize()` for new code. Keep
`standardize()` where stored data, such as a search index, was built with it, and re-index when you
switch.

| Input | `standardize()` | `normalize()` |
| --- | --- | --- |
| `۳٫۱۴` | `۳۱۴` (decimal separator removed) | `۳٫۱۴` |
| `آب` | `اب` | `آب` (`اب` with `fold_variants=True`) |
| `جزء` | `جز` | `جزء` |
| `ﭘﮐ` (Persian contextual forms) | unchanged | `پک` |
| `کتاب ها` | unchanged | `کتاب‌ها` |

## Contributing

Bug reports and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the
development setup.

## License

[MIT](LICENSE)
