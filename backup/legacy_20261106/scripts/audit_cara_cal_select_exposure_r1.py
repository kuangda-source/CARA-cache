#!/usr/bin/env python3
"""Audit frozen SELECT identities; only read project metadata, never endpoints."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.frozen_input_exposure_r1 import Identities

SELECT = 'plans/cara_policy_generator_20261020/CAL_SELECT_INPUTS_R1_20261022.json'
CATALOG = 'reports/dataset_source_group_audit_20260930.json'
REMOTE_ROOT = '/data20t/gaokuangda/worldcache_workspace'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def accepted_p1_unused_select(ref,data,root=ROOT):
    """Exempt only the exact accepted original whose SELECT never executed."""
    original='reports/cara_PG_P1_original_terminal_codec_recovered_20261024_0035.json'
    if ref!=original:return False
    try:
        raw=(root/ref).read_bytes()
        accepted=json.loads((root/'reports/cara_PG_P1_original_terminal_accepted_20261024_0037.json').read_text())
        if (sha(raw)!=accepted['capture_sha256'] or accepted['capture_ref']!=ref
                or json.loads(raw)!=data or accepted['full_protocol_accepted'] is not True
                or accepted['launch_id']!=data['launch']['launch_id']):return False
        batch=json.loads(data['files']['runner']['raw_utf8'])['batch']
        selected=[r for r in batch['rows'] if r['split']=='CAL_SELECT']
        if (len(batch['rows'])!=64 or len(selected)!=10 or batch['status']!='BUDGET_NOT_VERIFIED'
                or batch['selection_frozen'] is not None
                or accepted['scientific']['selected_policy'] is not None):return False
        if any(r['status']!='UNUSED_REGISTERED_UPPER_BOUND' or set(r)&{'member','video_artifact','score_artifact','request_artifact'} for r in selected):return False
        ids={r['id'] for r in selected}
        if any(ids & set(data[k]) for k in ('requests','scores','artifact_checks')):return False
        return True
    except (KeyError,ValueError,TypeError,OSError):return False


def metadata_reason(ref, data):
    if accepted_p1_unused_select(ref,data):
        index=Identities(json.loads((ROOT/SELECT).read_text())['selected_sources'])
        hits,_=index.document(data)
        if hits and all(h['location'] in ('$.select_members[0]','$.select_members[1]') for h in hits):
            return 'ACCEPTED_P1_UNUSED_SELECT_IDENTITIES_ONLY_NO_REQUESTS'
    if ref == CATALOG:
        return 'ORIGINAL_BENCHMARK_CATALOG_NOT_EXECUTION'
    if ref == 'reports/wc_paper_N07_all1044_original_input_bytes_CPU_inventory_20261016.json':
        if (data['sampler_or_model_or_guardrails_run'] is False and data['Torch_imported'] is False
                and data['GPU_submissions'] == 0 and data['inspected_rows'] == 1044):
            return 'INPUT_BYTES_ONLY_NO_MODEL_OR_GUARDRAILS'
    planning = {
        'reports/cara_ordered_preparation_existing_terminal_continuation_20261022.json':
            'EXISTING_BANK24_TERMINAL_CONTINUATION_UPDATED_AND_READ_BACK',
        'reports/wc_four_card_BANK24_retry2_halfway_closed_terminal_preserved_20261022.json':
            'HALFWAY_COMPLETED_DELETED_TERMINAL_CONTEXT_UPDATED_READ_BACK',
    }
    if ref in planning and data.get('status') == planning[ref]:
        # Only a prompt-string mention is exempt. A structured identity elsewhere blocks.
        index = Identities(json.loads((ROOT / SELECT).read_text())['selected_sources'])
        hits, _ = index.document(data)
        if all('prompt' in h['location'].lower() for h in hits):
            return 'SAVED_AUTOMATION_PROMPT_ONLY'
    if (data.get('status') == 'CAL_SELECT_SCOPED_IDENTITY_AUDIT'
            and data.get('GPU_submissions') == 0 and data.get('endpoint_values_exported') is False):
        return 'PRIOR_IDENTITY_AUDIT_NOT_EXECUTION'
    return None


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError('Use a new receipt; never overwrite an exposure observation')
    start = time.time()
    frozen = json.loads((ROOT / SELECT).read_text())
    if sha((ROOT / SELECT).read_bytes()) != 'd6bb1546100499456685b7300baa985d6d891794dd5716a199efeaec0985b87e':
        raise ValueError('Original R1 SELECT identity manifest changed')
    if sha((ROOT / frozen['protocol_ref']).read_bytes()) != frozen['protocol_sha256']:
        raise ValueError('Frozen input selection rule changed')
    catalog_raw = (ROOT / CATALOG).read_bytes()
    if sha(catalog_raw) != frozen['dataset_audit_sha256']:
        raise ValueError('Frozen benchmark catalog changed')
    bindings = [(SELECT, sha((ROOT / SELECT).read_bytes()))]
    for item in frozen['local_exposure_inventory_bindings']:
        if sha((ROOT / item['ref']).read_bytes()) != item['sha256']:
            raise ValueError('Frozen exposure inventory changed: ' + item['ref'])
        bindings.append((item['ref'], item['sha256']))
    for s in frozen['selected_sources']:
        if sha((ROOT / s['source_ref']).read_bytes()) != s['source_sha256']:
            raise ValueError('Original SELECT source bytes changed')
    records = json.loads(catalog_raw)['records']
    protected = {m for s in frozen['selected_sources'] for m in s['group_members']}
    selected = [r for r in records if r['name'] in protected]
    index = Identities(selected)
    markers = [s.encode() for r in selected for s in (r['name'], r['prompt_sha256'])]
    documents, mentions, errors, blockers = [], [], [], []
    paths = sorted(p for p in (ROOT / 'reports').rglob('*')
                   if p.is_file() and str(p).endswith(('.json', '.json.gz')) and '.private.' not in p.name)
    for path in paths:
        ref = str(path.relative_to(ROOT))
        try:
            stored = path.read_bytes()
            raw = gzip.decompress(stored) if path.suffix == '.gz' else stored
            data = json.loads(raw)
            documents.append(dict(ref=ref, sha256=sha(stored), bytes=len(stored)))
            hits, _ = index.document(data)
            if hits or any(m in raw for m in markers):
                reason = metadata_reason(ref, data)
                item = dict(ref=ref, sha256=sha(stored), classification=reason or 'REVIEW_REQUIRED',
                            identity_locations=hits)
                mentions.append(item)
                if reason is None:
                    blockers.append(item)
        except Exception as e:
            errors.append(dict(ref=ref, error_type=type(e).__name__, error=str(e)))
    # Execute only the existing identity walker, in memory, through the four-card entry.
    # No deploy, GPU query, ledger mutation, or retired two-card access.
    from wc_four_card_policy_assets_r1 import ssh
    module = (ROOT / 'src/wcomr/frozen_input_exposure_r1.py').read_text()
    payload = dict(module=module, module_sha256=sha(module.encode()), records=records, root=REMOTE_ROOT)
    remote = ssh("""
import hashlib,json,sys
p=json.loads(sys.stdin.buffer.readline())
assert hashlib.sha256(p['module'].encode()).hexdigest()==p['module_sha256']
ns={'__name__':'identity_only_in_memory'}
exec(compile(p['module'],'IDENTITY_ONLY_SOURCE','exec'),ns)
v=ns['collect_outputs'](p['root'],p['records'])
v.update(module_sha256=p['module_sha256'],project_root=p['root'])
print(json.dumps(v,allow_nan=False))
""", payload)
    if 'identity_hits' not in remote or 'documents' not in remote or 'read_errors' not in remote:
        remote = dict(original_unknown=remote, identity_hits={}, documents=[],
                      read_errors=[dict(kind='FOURCARD_IDENTITY_INVENTORY_UNKNOWN')])
    remote_selected = {k: v for k, v in remote['identity_hits'].items() if k in protected}
    scoped_clear = not (blockers or errors or remote_selected or remote['read_errors'])
    value = dict(status='CAL_SELECT_SCOPED_IDENTITY_AUDIT', started_unix=start, observed_unix=time.time(),
        source_revision=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        script_sha256=sha(Path(__file__).read_bytes()), frozen_bindings=dict(bindings),
        selected_names=sorted(protected), local_documents=documents, local_mentions=mentions,
        local_read_errors=errors, local_unclassified_mentions=blockers, remote=remote,
        selected_remote_identity_hits=remote_selected, scoped_no_execution_evidence=scoped_clear,
        scope='LOCAL_REPORTS_JSON_AND_GZIP_PLUS_FOURCARD_PROJECT_OUTPUT_METADATA',
        limitations=['Retired two-card server not contacted; only its saved local receipts covered',
                    'No assertion about unrecorded or out-of-project executions',
                    'Reaudit before first SELECT endpoint if new execution metadata has appeared'],
        final_TEST_independence_proven=False, endpoint_values_exported=False,
        videos_or_tensors_decoded=False, GPU_submissions=0, ledger_written=False)
    with args.output.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps(dict(receipt=str(args.output), scoped_clear=scoped_clear,
        local_documents=len(documents), local_mentions=len(mentions), local_errors=len(errors),
        remote_documents=len(remote['documents']), remote_errors=len(remote['read_errors']),
        selected_remote_hits=len(remote_selected), unclassified=[x['ref'] for x in blockers])))
    if not scoped_clear:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
