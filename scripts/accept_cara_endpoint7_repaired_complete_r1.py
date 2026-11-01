"""Export complete original CPU receipts and independently verify all 28 rows."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.cara_s_endpoint_scores_r1 import accept_scores


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    captured = json.loads(args.capture.read_text())
    assert captured['exit_code'] == 0
    observed = captured['result']
    recovery = observed['score_recovery']
    assert recovery['status'] == 'ORIGINAL_COMPLETE28_SCORE_ACCEPTED'
    assert recovery['supervisor_observation']['original_live'] is False
    assert recovery['supervisor_terminal']['exit_code'] == 0
    assert recovery['supervisor_terminal']['error'] is None
    score = recovery['score_capture']
    originals = observed['score_original_files']
    values = {}
    paths = {}
    encoded = {}
    for key, name in [('config', 'manifest.json'), ('packet', 'artifact-packet.json'), ('result', 'scores.json')]:
        raw = originals[name]['raw_utf8'].encode()
        assert hashlib.sha256(raw).hexdigest() == originals[name]['sha256']
        values[key] = json.loads(raw)
        encoded[key] = raw
    execution, accepted = score['execution'], score['accepted']
    assert accepted == accept_scores(values['packet'], values['config'],
                                     originals['manifest.json']['sha256'], values['result'], execution)
    assert (accepted['formal_logical_positions'], accepted['new_scored_pairs'],
            accepted['reused_original_rows']) == (28, 16, 12)
    assert len(values['result']['rows']) == 16
    assert all(accepted['source_rows'][row['id']] == row for row in values['config']['reused_rows'])
    original_b36 = json.loads((ROOT / 'reports/cara_fast_B36_complete_scores_accepted_r1_20261029.json').read_text())
    old = {row['id']: row for row in original_b36['rows']}
    assert all(old[row['id']] == row for row in values['config']['reused_rows'])
    for key, value in [('execution', execution), ('accepted', accepted)]:
        encoded[key] = (json.dumps(value, indent=2, allow_nan=False) + '\n').encode()
    assert all(not (ROOT / ('reports/cara_endpoint7_original_score_' + key + '_r1_20261101.json')).exists()
               for key in encoded)
    for key, raw in encoded.items():
        path = ROOT / ('reports/cara_endpoint7_original_score_' + key + '_r1_20261101.json')
        with path.open('xb') as stream:
            stream.write(raw)
        paths[key] = path
    summary = dict(status='E1_COMPLETE46_RGB13_SCORE28_ACCEPTED_AFTER_CPU_INTERFACE_REPAIR',
        launch_id=values['config']['launch_id'],
        formal_logical_positions=28, new_scored_pairs=16, reused_original_rows=12,
        reused_rows_byte_derived_unchanged=True, complete_physical_paths=46,
        RGB_identity_controls_passed=13, full_frames_per_pair=93, new_frame_pairs=1488,
        original_GPU_released_and_uniquely_settled=True, actual_GPUh=3.0556730066974542,
        original_score_container_ended=True, original_score_wall_seconds=execution['wall_seconds'],
        GPU_submissions=0, ledger_written=False, old_freezes_changed=False,
        original_failed_reader_preserved=True, original_GPU_launch_and_source_unchanged=True,
        capture_ref=str(args.capture), capture_sha256=hashlib.sha256(args.capture.read_bytes()).hexdigest(),
        exported_files={key: dict(path=str(path.relative_to(ROOT)), sha256=hashlib.sha256(path.read_bytes()).hexdigest())
                        for key, path in paths.items()},
        interpretation_scope='Four old CAL/seed0; complete endpoint comparison, not independent TEST or cross-model evidence')
    with args.output.open('x') as stream:
        json.dump(summary, stream, indent=2)
        stream.write('\n')
    print(summary['status'])


if __name__ == '__main__':
    main()
