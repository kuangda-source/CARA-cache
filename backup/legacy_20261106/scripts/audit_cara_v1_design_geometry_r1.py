"""Inspect frozen P1 design geometry without labels, fitting or remote access."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.cara_source_lifecycle_estimation_r1 import FAMILIES, coordinates, features


def matrix_geometry(rows, family):
    matrix = np.asarray([features(row['features'], family) for row in rows], dtype=np.float64)
    singular = np.linalg.svd(matrix, compute_uv=False)
    return dict(structural_rows_per_input=len(rows), columns=matrix.shape[1],
                rank=int(np.linalg.matrix_rank(matrix)), singular_values=singular.tolist(),
                unregularized_condition_number=float(singular[0] / singular[-1]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    plan = ROOT / 'plans/cara_next_stage_20261101/source_lifecycle'
    design_path = plan / 'V1_CALIBRATION64_DESIGN_R1.json'
    manifest_path = plan / 'V1_P1_WHOLE_MANIFEST_R1.json'
    design = json.loads(design_path.read_bytes())
    manifest = json.loads(manifest_path.read_bytes())
    parents = design['parents']
    rows = [row for parent in parents for row in parent['states']]
    triples = [(row['t'], row['a'], row['b']) for row in rows]
    for row in rows:
        assert tuple(row['features']) == coordinates(manifest['schedule']['sigmas'], row['t'], row['a'], row['b'])
    assert len(rows) == 32 and len(design['FIT']) == 2
    profile = manifest['profile']
    assert profile['horizon'] == 36 and profile['protected_dense'] == list(range(1, 8)) + [36]
    assert profile['min_C_anchors'] == 2 and profile['max_source_age'] == 28
    # Every subset of steps8..35 is legal: protected1..7 supply both sources,
    # the final D36 closes the tail, and no C interval can exceed28 updates.
    counts = {str(k): math.comb(28, k - 8) for k in manifest['D_budgets']}
    geometry = {}
    for family in FAMILIES:
        geometry[family] = dict(full_design=matrix_geometry(rows, family),
            whole_parent_training_folds={parent['id']: matrix_geometry(
                [row for other in parents if other['id'] != parent['id'] for row in other['states']], family)
                for parent in parents})
    paths = [Path(__file__), design_path, manifest_path,
             ROOT / 'src/wcomr/cara_source_lifecycle_estimation_r1.py',
             ROOT / 'src/wcomr/cara_source_lifecycle_planner_r1.py']
    result = dict(schema='CARA_V1_P1_LABEL_FREE_DESIGN_GEOMETRY_R1',
        status='PREREGISTERED_DESIGN_GEOMETRY_NOT_SCIENTIFIC_RESULTS',
        observed_at=datetime.now(timezone.utc).isoformat(), numpy_version=np.__version__,
        source_sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        scope_sha256=manifest['scope_sha256'], labels_planned=64, structural_rows_per_input=32,
        distinct_t_a_b= len(set(triples)), distinct_input_t_a_b=len(set(triples))*len(design['FIT']),
        source_triple_occurrence_histogram={str(k): v for k, v in sorted(Counter(Counter(triples).values()).items())},
        exact_stage_age_previous_gap_contrasts=design['exact_stage_age_gap_contrasts'],
        legal_full_schedule_counts=counts, feature_geometry=geometry,
        feature_rank_is_statistical_or_endpoint_evidence=False, rank_changes_frozen_design=False,
        real_labels_read=0, estimators_fitted=0, original_experiments_replayed=0,
        remote_connections=0, GPU_submissions=0, ledger_read=False, ledger_written=False)
    with Path(args.output).open('x') as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps(dict(output=args.output, distinct_t_a_b=result['distinct_t_a_b'],
                         legal_full_schedule_counts=counts, real_labels_read=0)))
