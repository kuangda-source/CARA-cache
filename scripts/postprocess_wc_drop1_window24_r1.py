#!/usr/bin/env python3
"""Full24 artifacts, all16 full-frame scores, all12 old and warm-prefix controls."""
from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / 'src'))
    from wcomr.drop1_window24_entry_adapter_r1 import adapt
    source = (root / 'scripts/postprocess_wc_drop1_full18_r1.py').read_text()
    namespace = dict(__name__='registered_window24_post', __file__=__file__)
    exec(compile(adapt(source, 'post'), __file__ + '#reversible-whole24-controls', 'exec'), namespace)
    namespace['main']()


if __name__ == '__main__':
    main()
