# Contributing to PersianUtils

Bug reports, ideas and pull requests are welcome.

## Reporting bugs

Open an [issue](https://github.com/ishto7/persianutils/issues) with the input, the output you got
and the output you expected. Paste text as `print(ascii(text))` so invisible characters such as the
half-space (U+200C) survive the copy.

## Development setup

With [uv](https://docs.astral.sh/uv/):

```bash
uv run --group test pytest
```

```bash
uv run --group lint ruff check .
```

```bash
uv run --group lint ruff format .
```

```bash
uv run --group dev mypy
```

Without uv, install the package and the development tools into a virtual environment with
`python -m pip install -e . --group dev` (pip 25.1 or later), then run `pytest`, `ruff` and `mypy`
directly.

`pytest` also runs the examples in `README.md` and in the docstrings.

## Pull requests

1. Branch from `master`.
2. Add tests. For a normalization rule, also test inputs the rule must leave alone.
3. Keep the output of `standardize()` and `standardize4Word2vec()` unchanged.
   `tests/test_legacy_compat.py` compares them with the published 1.0.0; a deliberate fix must
   list the affected characters there and in `CHANGELOG.md`.
4. Update `README.md` and `CHANGELOG.md` for changes users will notice.
5. Write invisible characters in code as escapes (`"‌"`), not as literal characters.

## Releasing

1. Set `__version__` in `persianutils/__init__.py` and date the release in `CHANGELOG.md`.
2. Publish a GitHub release. The "Publish to PyPI" workflow builds the package and uploads it with
   the `PYPI_API_TOKEN` repository secret.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE).
