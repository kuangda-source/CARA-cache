"""CPU-only optimistic bilinear-model diagnostic; never a bound on actual Phi."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--analysis', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    x = json.loads(a.analysis.read_text())
    assert x['status'] == 'B1_COMPLETE_LOCAL_READOUT_ANALYSIS_NOT_VIDEO_VALIDATION'
    baselines = x['saved_diagnostics']['original_readouts']
    rows = []
    for f in x['training_folds'] + [dict(training_prompts=list(baselines['A_PHASE']['by_prompt']), coefficients=x['deployment_coefficients'])]:
        c = f['coefficients']; G = np.asarray(c['G']); b = np.asarray(c['b'])
        assert np.linalg.eigvalsh(G).min() > 0
        z = np.linalg.solve(G, b)
        bound = float(c['constant'] - b @ z)
        # Relax z=(kL,kH,kL*kH) to unconstrained R^3 and drop nonnegative ridge.
        # This can only improve this surrogate, not the actual nonlinear head.
        baseline = float(np.mean([baselines['A_PHASE']['by_prompt'][q]['MSE'] for q in f['training_prompts']]))
        rows.append(dict(training_prompts=f['training_prompts'], relaxed_z=z.tolist(),
            optimistic_surrogate_MSE_lower_bound=bound, same_prompt_A_PHASE_MSE=baseline,
            surrogate_bound_worse_percent=100*(bound/baseline-1),
            linear_solve_residual=float(np.linalg.norm(G@z-b))))
    r = dict(status='CPU_BILINEAR_RELAXATION_DIAGNOSTIC_ONLY', rows=rows,
        source_analysis=str(a.analysis), source_sha256=hashlib.sha256(a.analysis.read_bytes()).hexdigest(),
        actual_Phi_bound=False, out_of_box_actual_data_available=False,
        interpretation='Supports a resource stop for this candidate alongside actual dominance; does not rule out nonlinear extrapolation or other methods.',
        new_GPU_submissions=0)
    with a.output.open('x') as f: json.dump(r, f, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps(r, indent=2))

if __name__ == '__main__': main()
