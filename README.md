# persianutils
A package to preprocess your Persian text for Word2Vec embedding
# How to use:
Just use the two implemented function named "standardize" or "standardize4Word2vec"
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

Or just make charachters standard by ```standatdize()```:
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
