"""Export registered B36 panels only after rebuilding complete accepted analysis."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from analyze_cara_fast_r1 import ratio_interval
from wcomr.cara_fast_b36_figures_r1 import verify_analysis, export_report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--analysis', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--receipt-root', type=Path, default=ROOT)
    args = parser.parse_args()
    analysis, sha = verify_analysis(args.analysis, receipt_root=args.receipt_root)
    statistics = json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/PAPER_RESULTS_MANIFEST.json').read_bytes())['statistics']
    assert statistics == dict(unit='prompt', frame_count_not_independent_n=True, prompt_equal=True,
        repeats='average within prompt first', bootstrap_samples=20000, bootstrap_seed=20261028,
        quantile='higher', interval='two-sided95 exploratory')
    result = export_report(analysis, args.output_dir, ratio_interval)
    result.update(analysis_sha256=sha, analysis_path=str(args.analysis), bootstrap=statistics,
        source_sha256={name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in (
            'src/wcomr/cara_fast_b36_figures_r1.py', 'scripts/render_cara_fast_b36_figures_r1.py',
            'scripts/analyze_cara_fast_r1.py')})
    with (args.output_dir/'report.json').open('x') as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
        handle.write('\n')
    print(json.dumps(dict(status=result['status'], figure_panels=4, GPU_submissions=0)))


if __name__ == '__main__':
    main()
