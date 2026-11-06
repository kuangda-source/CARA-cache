"""Collect the unique CPU audit handle, accepting only a complete nine-pair result."""
import hashlib
import json
from pathlib import Path

from cara_two_card_transport_r1 import ssh

ROOT = Path(__file__).resolve().parents[1]
REMOTE = r'''
import hashlib,json,sys,time
from pathlib import Path
launch=json.load(sys.stdin);s=Path(launch['stage'])
raw=(s/'result.json').read_bytes();r=json.loads(raw)
out=dict(status=r['status'],completed=len(r['rows']),elapsed=time.time()-r['started_unix'])
if r['status']!='RUNNING':
    out.update(result=r,result_sha256=hashlib.sha256(raw).hexdigest(),
        scope=json.loads((s/'scope.json').read_text()),
        source_hashes={k:hashlib.sha256((s/k).read_bytes()).hexdigest() for k in launch['source_hashes']},
        log=(s/'CPU.log').read_text(),
        process_stat=Path('/proc/'+str(launch['pid'])+'/stat').read_text() if Path('/proc/'+str(launch['pid'])+'/stat').exists() else None)
print(json.dumps(out))
'''


def main():
    launch = json.loads((ROOT / 'reports/wc_native_lpips_rescore_launch_20261027.json').read_text())
    out = ssh(REMOTE, launch)
    if out['status'] == 'RUNNING':
        print(json.dumps(out))
        return
    r = out['result']
    assert r['status'] == 'COMPLETE_ORIGINAL_ALEX_REPRODUCED_AND_OFFICIAL_PIQ_RESCORED', r.get('error')
    assert r['exit_code'] == 0 and not r['CUDA_initialized']
    assert r['GPU_submissions'] == 0 and r['new_generation'] == 0
    assert len(r['rows']) == len(out['scope']['pairs']) == 9
    assert [x['variant'] for x in r['rows']] == ['wc006'] * 7 + ['wc008'] * 2
    assert out['source_hashes'] == launch['source_hashes']
    assert hashlib.sha256((ROOT / 'scripts/audit_wc_native_lpips_rescore_r1.py').read_bytes()).hexdigest() == r['worker_sha256']
    assert all(r['controls'].values())
    for row, pair in zip(r['rows'], out['scope']['pairs']):
        assert row['scene'] == pair['scene'] and row['variant'] == pair['variant']
        assert row['reference'] == pair['reference'] and row['candidate'] == pair['candidate']
        assert row['frames'] == 93 and row['PTS_equal'] and row['all_RGB_reader_equal']
        assert len(row['alex']) == len(row['piq_vgg']) == len(pair['historical_frame_distances']) == 93
        assert max(abs(a-b) for a,b in zip(row['alex'],pair['historical_frame_distances'])) < 1e-6
        for key in ('alex', 'piq_vgg'):
            assert abs(sum(row[key])/93-row[key+'_mean']) < 1e-12
    unique = {row[k]['path']: row[k]['sha256'] for row in r['rows'] for k in ('reference','candidate')}
    assert len(unique) == 16
    old = json.loads((ROOT / 'reports/wc_native_lpips_original_asset_preflight_20261027.json').read_text())
    assert all(old['files'][p]['sha256'] == h and old['files'][p]['matches'] for p,h in unique.items())
    accepted = dict(status='ACCEPTED_NINE_PAIRS_837_FRAMES_CPU_ONLY',
                    remote_result_sha256=out['result_sha256'],
                    source_hashes=out['source_hashes'], unique_original_videos=16,
                    full_frame_pairs=837, result=r,
                    WC006_Alex_mean=sum(x['alex_mean'] for x in r['rows'][:7])/7,
                    WC006_PIQ_VGG_mean=sum(x['piq_vgg_mean'] for x in r['rows'][:7])/7,
                    max_original_frame_difference=max(x['max_frame_abs_diff_from_historical'] for x in r['rows']),
                    evaluation_standards_changed=False, paper_exact_generation_reproduced=False)
    path = ROOT / 'reports/wc_native_lpips_official_rescore_accepted_20261027.json'
    path.write_text(json.dumps(accepted, indent=2, ensure_ascii=False)+'\n')
    (ROOT / 'reports/wc_native_lpips_rescore_terminal_20261027.json').write_text(json.dumps(out, indent=2)+'\n')
    print(json.dumps({k:v for k,v in accepted.items() if k not in ('result','source_hashes')},indent=2))


if __name__ == '__main__':
    main()
