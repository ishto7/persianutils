# PersianUtils
A wonderful package to preprocess your Persian text for Search, Standardizing & NLP processes.

# Why PersianUtils?
Persian has a lot of duplicate characters with Arabic but with different Unicode code points. This may lead to different writings of a word, with almost exactly the same appearance. In addition to that, contextual forms of a character may also be used in text, which doesn't change the word shape but makes the same trouble mentioned above. Unfortunately, a lot of non-standard Persian keyboards don't obey these rules, which makes the problem more severe. This package helps to make your Persian text a standard one, with original Persian characters.

# Installation
To install PersianUtils, you can use pip:
```
pip install persianutils
```

# Usage
There are two functions implemented for standardizing Persian text named "standardize" and "standardize4Word2vec".

## standardize()
This function does the following:
1. Replace Arabic characters with their Persian equivalent. Like ```from persianutils.ArabicAlphabet import ALEF_MAKSURA``` to ```from persianutils.PersianAlphabet import YE```
2. Remove Tanveens like ـٍ , ـَ , & etc.
3. Replace contextual forms of a character to its original form. Like "ـتـ‎" to "ت".
4. Replace western and eastern numerals to their Persian equivalent. ```2``` to ```۲```

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

## standardize4Word2vec()
This function has these features:
1. Same as the standardize() #1
2. Same as the standardize() #2
3. Same as the standardize() #3
4. Replace all numerals (Eastern, Western and Persian) to their Persian writings. ```2``` to ```دو```
5. Replaces all punctuation marks with single space. Punctuations are: ```[!"#%\'()*+,-./:;<=>?@\[\]^_`{|}~’”“′‘\\\]؟؛«»،٪```

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

# Persian & Arabic Characters
There is also a list of Persian & Arabic characters, accessible from ```persianutils.PersianAlphabet```:
```
from persianutils.PersianAlphabet import ALEF, BE, PE, TE
```
Or for Arabic:
```
from persianutils.ArabicAlphabet import ALEF_HAMZA_ABOVE_FINAL, HAMZA_ABOVE_ALEF
```

# Contributing
We appreciate all contributions. If you're interested in contributing, please start by reading our [Contributing Guide](CONTRIBUTING.md).
