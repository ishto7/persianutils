"""Regenerate ``v1_0_0_reference.json`` from the published persianutils 1.0.0.

The fixture records what 1.0.0 did, so the compatibility tests can check the
current code against the real release rather than against itself.

Usage::

    pip download --no-deps --only-binary :all: persianutils==1.0.0 -d /tmp/pu100
    unzip /tmp/pu100/persianutils-1.0.0-py3-none-any.whl -d /tmp/pu100/wheel
    python tests/fixtures/make_v1_reference.py /tmp/pu100/wheel

The wheel's SHA-256 on PyPI is
4a76ea74022e463bd5ac03986ad81fd5d14aae0bfca24d08b8edc41a98373bb8.
"""

from __future__ import annotations

import json
import sys
import types
import warnings
from pathlib import Path

OUTPUT = Path(__file__).with_name("v1_0_0_reference.json")


def main(wheel_dir: str) -> None:
    sys.path.insert(0, wheel_dir)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        import persianutils
        from persianutils import ArabicAlphabet, PersianAlphabet, processes

    package_dir = Path(persianutils.__file__).resolve().parent
    if Path(wheel_dir).resolve() not in package_dir.parents:
        raise SystemExit(f"imported persianutils from {package_dir}, not from {wheel_dir}")

    data = {
        "source": "persianutils 1.0.0 wheel from PyPI",
        "standardize": processes.replacementDict,
        "standardize4Word2vec": processes.replacementDict4Word2vec,
        # repr() of every public constant, readable back with ast.literal_eval.
        "constants": {
            module.__name__: {
                name: repr(value)
                for name, value in vars(module).items()
                if not name.startswith("_")
                and not isinstance(value, types.ModuleType)
                and not callable(value)
            }
            for module in (PersianAlphabet, ArabicAlphabet)
        },
    }
    with OUTPUT.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=True, indent=1, sort_keys=True)
        handle.write("\n")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main(sys.argv[1])
