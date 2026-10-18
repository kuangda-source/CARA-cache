#!/usr/bin/env python3
"""The real scout model entry, with its ordinary weights-free CPU check."""
from pathlib import Path
import sys

stage=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(stage/'src'))
from wcomr.scout_production_entry_adapter_r1 import adapt
original=stage/'scripts/run_wc_drop1_full18_r1.py'
exec(compile(adapt(original.read_text()),str(original)+'#SCOUT-EXPLICIT-ENTRY-SCOPE','exec'))
