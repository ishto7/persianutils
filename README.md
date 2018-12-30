# persianutils
A \[getting] wonderfull package to preprocess your Persian text for Search, Standardizing & NLP processes


# Would it help?
Persian has a lot of duplicate characters with Arabic but with different Unicode code points. This may lead to have different writings of a word, with almost exactly the same showing. In addition to that, contextual forms of a character may also be used in text, which doesn't change the word shape but makes the same trouble mentioned above. Unfortunately, a lot of non-standard Persian keyboards don't obey these rules, which makes the problem more severe.
This package helps to make your Persian text an standard one, with original Persian characters.

# How to use:
There are two functions implemented for standardizing Persian text named "standardize" or "standardize4Word2vec"

```standardize()``` does these:
1. Replace Arabic characters with their Persian equivalent. Like ```from persianutils.ArabicAlphabet import ALEF_MAKSURA``` to ```from persianutils.PersianAlphabet import YE```
2. Remove Tanveens like ـٍ , ـَ , & etc.
3. Replace contextual forms of a character to it's original form. Like "ـتـ‎" to "ت".
4. Replace western and eastern numerals to their persian equivalent. ```2``` to ```۲```

Example:
```
import persianutils as pu
raw_text = "سلامٌ علیکم!"
processed_text = pu.standardize(raw_text)
print(processed_text)
```
That would result in:
```
سلام علیکم!
```


standardize4Word2vec() has these features:
1. Same as the standardize() #1
2. Same as the standardize() #2
3. Same as the standardize() #3
4. Replace all numerals (Eastern, Western and Persian) to their persian writings. ```2``` to ```دو```
5. Replaces all punctuation marks with single space. punctions are: ```[!"#%\'()*+,-./:;<=>?@\[\]^_`{|}~’”“′‘\\\]؟؛«»،٪```

Example:
```
import persianutils as pu
raw_text = "سلامٌ علیکم!"
processed_text = pu.standardize4Word2vec(raw_text)
print(processed_text)
```
This would result in:
```
سلام علیکم 
```

There is also a list of Persian & Arabic characters, accessible from ```persianutils.PersianAlphabet```:
```
from persianutils.PersianAlphabet import ALEF, BE, PE, TE
```
Or for Arabic:
```
from persianutils.ArabicAlphabet import ALEF_HAMZA_ABOVE_FINAL, HAMZA_ABOVE_ALEF
```
