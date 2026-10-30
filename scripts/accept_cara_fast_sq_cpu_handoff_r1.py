"""Review published S CPU receipts from Git, without running a model or remote task."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
AUDITOR = 'scripts/audit_cara_sq_s_production_entry_cpu_r6.py'
SCOPE = 'plans/cara_next_stage_20261028/sq/S_NATIVE_ENTRY_CPU_R6.json'


def blob(revision, name):
    return subprocess.check_output(['git', 'show', revision + ':' + name], cwd=ROOT)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def review(revision):
    require(sys.version_info >= (3, 11), 'Original auditor requires Python 3.11+ for Docker nanosecond timestamps')
    revision = subprocess.check_output(['git', 'rev-parse', revision + '^{commit}'], cwd=ROOT, text=True).strip()
    source = blob(revision, AUDITOR)
    namespace = {'__file__': str(ROOT / AUDITOR), '__name__': 'published_S_CPU_auditor'}
    exec(compile(source, AUDITOR, 'exec'), namespace)
    scope = json.loads(blob(revision, SCOPE))
    evidence = {}

    def read(name):
        data = blob(revision, name)
        evidence[name] = {'sha256': digest(data), 'bytes': len(data),
            'url': 'https://github.com/kuangda-source/CARA-cache/blob/' + revision + '/' + name}
        return json.loads(data)

    read(SCOPE)
    evidence[AUDITOR] = {'sha256': digest(source), 'bytes': len(source)}
    results = {}
    for host in ('four_card', 'two_card'):
        saved = read('reports/cara_sq_s_native_entry_' + host + '_cpu_accepted_r6_20261030.json')
        capture = read(saved['capture_ref'])
        require(saved['capture_sha256'] == evidence[saved['capture_ref']]['sha256'], 'Original capture hash changed')
        require(saved['auditor_source_sha256'] == digest(source), 'Original auditor changed')
        original = saved['source_revision']
        require(blob(original, SCOPE) == blob(revision, SCOPE), 'Original CPU scope changed')
        for name, expected in scope['critical_source_sha256'].items():
            require(digest(blob(original, name)) == digest(blob(revision, name)) == expected,
                'Published production-critical source changed: ' + name)
        rebuilt = namespace['accept'](capture, scope, host, original)
        require(all(saved[key] == value for key, value in rebuilt.items()), 'Saved acceptance differs from original reader')
        results[host] = {key: value for key, value in rebuilt.items()
            if key not in ('payload_sha256', 'critical_source_sha256')}
        results[host]['critical_files_verified_against_original_and_published_commit'] = len(scope['critical_source_sha256'])
        results[host]['capture_sha256'] = saved['capture_sha256']
        results[host]['acceptance_rebuilt_exactly'] = True

    quotes = {}
    for host, filename in (('four_card', 'S_WHOLE_QUOTE_FOUR_CARD_R2.json'),
            ('two_card', 'S_WHOLE_QUOTE_TWO_CARD_OTHER_GPU_R2.json')):
        quote = read('plans/cara_next_stage_20261028/sq/' + filename)
        physical = read(quote['physical_scope_ref'])
        unsigned = {key: value for key, value in physical.items() if key != 'physical_scope_sha256'}
        physical_digest = digest(json.dumps(unsigned, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())
        require(physical_digest == physical['physical_scope_sha256'] == quote['physical_scope_sha256']
            and physical['counts'] == quote['physical_counts'], 'Quote physical scope changed')
        for name, expected in quote['source_evidence_sha256'].items():
            require(digest(blob(revision, name)) == expected, 'Quote source evidence changed: ' + name)
        require(quote['physical_counts']['new_paths'] == 10 and quote['physical_counts']['reused_OFF_paths'] == 0,
            'The complete R2 card must include all ten new paths')
        require(quote['proposed_hard_limit_frozen'] is False, 'Changed quote state requires a new review')
        quotes[host] = {key: quote[key] for key in ('forecast_complete_GPUh', 'proposed_hard_limit_GPUh',
            'proposed_hard_limit_frozen', 'physical_counts', 'physical_scope_ref', 'physical_scope_sha256')}
        quotes[host]['purpose'] = 'Acquire the complete shared S risk and raw-state support on registered FIT parents; no S-END video efficacy claim'
        quotes[host]['requires_explicit_over_4_GPUh_approval'] = True

    return dict(status='PUBLISHED_S_DUAL_HOST_NATIVE_CPU_HANDOFF_REVIEWED', observed_unix=time.time(),
        published_snapshot_revision=revision, reader_source_sha256=digest(source), evidence=evidence,
        hosts=results, proposed_complete_quotes=quotes,
        scope='Published original CPU terminal evidence only; no live GPU/resource admission or whole-card approval',
        S_risk_data_collected=False, S_method_efficacy_accepted=False, S_END_accepted=False,
        S_GPU_authorized_by_this_review=False, new_remote_calls=0, new_CPU_workers=0,
        new_GPU_submissions=0, new_reserved_GPUh=0, ledger_written=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--revision', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Preserve the existing handoff review')
    result = review(args.revision)
    result['handoff_reader_sha256'] = digest(Path(__file__).read_bytes())
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')
    print(json.dumps({'status': result['status'], 'hosts': list(result['hosts']), 'GPU_submissions': 0}))


if __name__ == '__main__':
    main()
