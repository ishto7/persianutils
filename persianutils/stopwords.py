"""A list of Persian stopwords.

The list holds function words: pronouns, prepositions, conjunctions, common
auxiliary and copula verb forms, determiners, quantifiers and question words.
Content words are left out, even frequent ones, so the list is safe for
search and topic modelling. Words are spelled as :func:`persianutils.normalize`
writes them, plus common spellings without a half-space.

>>> tokens = ["من", "کتاب‌ها", "را", "در", "کتابخانه", "گذاشتم"]
>>> [token for token in tokens if token not in STOPWORDS]
['کتاب\\u200cها', 'کتابخانه', 'گذاشتم']
"""

from __future__ import annotations

__all__ = ["STOPWORDS"]

_PRONOUNS = """
من تو او وی ما شما آنها آن‌ها ایشان اینان آنان خود خودم خودت خودش خودمان خودتان
خودشان خویش خویشتن
"""

_DEMONSTRATIVES = """
این آن اینها این‌ها همین همان همین‌ها همان‌ها چنین چنان اینجا آنجا این‌جا آن‌جا
همین‌جا همان‌جا اینک
"""

_PREPOSITIONS = """
از به با در بر برای تا بی بدون جز بجز به‌جز مانند مثل میان بین پیش پس زیر روی
کنار نزد سوی طی توسط علیه ضد همراه درباره راجع نسبت طبق براساس درون بیرون
"""

_CONJUNCTIONS = """
و یا اما ولی که اگر چون چونکه زیرا چراکه سپس بلکه لیکن لکن ولیکن اگرچه هرچند گرچه
چنانچه وقتی وقتی‌که هنگامی هنگامی‌که درحالی‌که مگر یعنی بنابراین لذا همچنین نیز
هم اینکه این‌که آنکه آن‌که آنچه هرچه چنانکه
"""

_POSTPOSITIONS = "را"

_VERBS = """
است هست هستم هستی هستیم هستید هستند نیست نیستم نیستی نیستیم نیستید نیستند
بود بودم بودی بودیم بودید بودند بوده باشد باشند باشم باشی باشیم باشید
شد شده شدن شدند شود شوند شوم شوی شویم شوید می‌شود می‌شوند میشود میشوند
کرد کرده کردن کردند کند کنند کنم کنی کنیم کنید می‌کند می‌کنند میکند میکنند
دارد دارند دارم داری داریم دارید داشت داشتند داشته
خواهد خواهند خواهم خواهی خواهیم خواهید
باید نباید توان می‌توان می‌تواند می‌توانند میتوان میتواند میتوانند
"""

_DETERMINERS = """
یک هر همه چند چندین برخی بعضی هیچ دیگر دیگری دیگران تمام تمامی کل کلیه
بسیار بسیاری خیلی کمی اندکی بیش بیشتر کمتر اکثر چندان چیزی کسی هرکس
"""

_ADVERBS = """
نه بله آری فقط تنها حتی هنوز اکنون الان حالا همیشه هرگز شاید البته واقعا تقریبا
اصلا کاملا دوباره باز همچنان همواره گاهی اغلب معمولا قبلا بعدا آنگاه آن‌گاه
اینطور آنطور این‌طور آن‌طور
"""

_QUESTION_WORDS = "چه چرا کجا کی چگونه چطور آیا کدام چقدر چی"

#: Persian stopwords, as a frozenset for fast membership tests.
STOPWORDS: frozenset[str] = frozenset(
    word
    for group in (
        _PRONOUNS,
        _DEMONSTRATIVES,
        _PREPOSITIONS,
        _CONJUNCTIONS,
        _POSTPOSITIONS,
        _VERBS,
        _DETERMINERS,
        _ADVERBS,
        _QUESTION_WORDS,
    )
    for word in group.split()
)
