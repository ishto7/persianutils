import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="persianutils",
    version="1.0.0",
    author="Iman Nazari",
    author_email="imannazari@hotmail.com",
    description="Standardize your Persian text: Preprocessing, Embedding, and more!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ishto7/persianutils",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
