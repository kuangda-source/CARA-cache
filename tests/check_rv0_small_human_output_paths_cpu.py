"""Real filesystem symlinks and escapes using a completed receipt as CPU input."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); root = args.root.resolve()
    sys.path.insert(0, str(root/'src'))
    from wcomr.rv0_small_human_evaluation import evaluation_plan
    raw = gzip.decompress((root/'reports/wc_w3_small_human_runner_20261005.json.gz').read_bytes())
    original = json.loads(raw)
    original_config = json.loads((root/'configs/wc_w3_small_human_approved_r1_20261005.json').read_text())
    refused = []; passed = []
    def reject(name, receipt, config):
        try:
            evaluation_plan(receipt, config)
        except ValueError:
            refused.append(name)
        else:
            raise AssertionError('Output provenance escape accepted: '+name)
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp); real = directory/'canonical'; real.mkdir()
        link = directory/'project-link'; link.symlink_to(real, target_is_directory=True)
        for project in [real, link]:
            config = copy.deepcopy(original_config); config['expected_project_root'] = str(project)
            receipt = copy.deepcopy(original); receipt['scope'] = config
            row = receipt['requests'][0]
            output = project/'outputs'/config['run_id']/'diagnostic'; output.mkdir(parents=True, exist_ok=True)
            items = [row['artifact'], *[d['artifact'] for d in row['decoded_children']]]
            for index, item in enumerate(items):
                item['path'] = str(output/('video-'+str(index)+'.mp4'))
                Path(item['path']).touch()
            plan = evaluation_plan(receipt, config)
            assert len(plan['files']) == 4 and len(plan['pairs']) == 2
            passed.append('canonical_project' if project == real else 'symlink_project')
        broken = copy.deepcopy(receipt)
        broken['requests'][0]['decoded_children'][1]['artifact']['path'] = str(output/'..'/'outside.mp4')
        reject('parent_escape', broken, config)
        escaped = output/'escaped.mp4'; escaped.symlink_to(directory/'outside.mp4')
        broken = copy.deepcopy(receipt); broken['requests'][0]['decoded_children'][1]['artifact']['path'] = str(escaped)
        reject('symlink_escape', broken, config)
        broken = copy.deepcopy(receipt); broken['requests'][0]['decoded_children'][1]['artifact']['path'] = str(output)+'-other/video.mp4'
        reject('prefix_collision', broken, config)
        alias = output/'alias.mp4'; alias.symlink_to(output/'video-0.mp4')
        broken = copy.deepcopy(receipt); broken['requests'][0]['decoded_children'][1]['artifact']['path'] = str(alias)
        reject('canonical_duplicate_artifact', broken, config)
        broken = copy.deepcopy(receipt); broken['requests'][0]['decoded_children'][1]['artifact']['path'] = str(project/'outputs'/'other-run'/'diagnostic'/'video.mp4')
        reject('other_run', broken, config)
        broken = copy.deepcopy(receipt); broken['requests'][0]['historical_WC_encoded_bridge_pass'] = False
        reject('missing_historical_bridge', broken, config)
        broken = copy.deepcopy(receipt); broken['requests'][0]['decoded_children'].pop()
        reject('missing_child_encoding', broken, config)
    assert 'torch' not in sys.modules
    result = {'status': 'HUMAN_CANONICAL_ROOT_AND_SYMLINK_ESCAPE_CPU_CONTROLS_PASS_NOT_GPU',
        'CPU_fixture': True, 'passed_cases': passed, 'refusal_count': len(refused), 'refusals': refused,
        'input_real_receipt_sha256': hashlib.sha256(raw).hexdigest(),
        'GPU_submissions': 0, 'no_Torch_import': True,
        'source_sha256': {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [Path(__file__).resolve(), root/'src/wcomr/rv0_small_human_evaluation.py']}}
    if args.output.exists():
        raise ValueError('Preserve original CPU check identity')
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'source_sha256'}))


if __name__ == '__main__':
    main()
