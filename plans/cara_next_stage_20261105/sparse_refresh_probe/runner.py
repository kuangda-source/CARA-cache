"""Reuse admitted sensitivity runtime loading with the sparse S1/S2 collector."""
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'src'),str(ROOT/'scripts')]
from plans.cara_next_stage_20261104.sensitivity import runner as base
from plans.cara_next_stage_20261105.sparse_refresh_probe.collector import collect_loaded
from wcomr.source_aware_phase_sampling import bind_globals

main=bind_globals(base.main,dict(HERE=HERE,collect_loaded=collect_loaded))

if __name__=='__main__':main()
