#!/usr/bin/env python3
"""One resident model, eight full warmups and sixteen full science paths."""
from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / 'src'))
    from wcomr.drop1_window24_entry_adapter_r1 import adapt
    source = (root / 'scripts/run_wc_drop1_full18_r1.py').read_text()
    namespace = dict(__name__='registered_window24_runner', __file__=__file__)
    exec(compile(adapt(source, 'runner'), __file__ + '#reversible-whole24-scope', 'exec'), namespace)
    namespace['main']()


if __name__ == '__main__':
    main()
