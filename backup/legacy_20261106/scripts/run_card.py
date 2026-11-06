#!/usr/bin/env python3
"""Minimal card reader/plan and existing read-only adapter. No GPU launch API."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
ADAPTERS={'cal66_existing_r1':'scripts/wc_four_card_cara_shared66_gpu_r1.py'}
IDENTITY_FIELDS={'model_weights','input_preprocessing','seed','solver_grid','actions','alpha','beta','readout_source','precision_runtime'}
PRESERVE={'TIMING_REPEAT','WARM','CONTROL','HISTORICAL_BRIDGE'}
def digest(raw):return hashlib.sha256(raw).hexdigest()
def execution_fingerprint(identity):
    if set(identity)!=IDENTITY_FIELDS or any(v is None for v in identity.values()):raise ValueError('Complete execution identity required')
    return digest(json.dumps(identity,sort_keys=True,separators=(',',':'),allow_nan=False).encode())
def alias_candidates(slots):
    """Suggest method aliases only, never remove registered physical slots."""
    groups={}
    for s in slots:
        if s['section']!='QUALITY':continue
        groups.setdefault(execution_fingerprint(s['identity']),[]).append(s['id'])
    return [ids for ids in groups.values() if len(ids)>1]
def file_ref(ref,root=ROOT):
    if not isinstance(ref,dict) or set(ref)!={'path','sha256'}:raise ValueError('Reference needs path and SHA')
    name=ref['path']
    if not isinstance(name,str) or not name or Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('Repository relative reference required')
    p=root/name
    if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()) or not p.is_file():raise ValueError('Regular in-repository file required')
    raw=p.read_bytes()
    if digest(raw)!=ref['sha256']:raise ValueError('Reference changed: '+name)
    return p,raw
def validate_refs(value,root=ROOT):
    if isinstance(value,dict):
        if set(value)=={'path','sha256'}:
            if value['path'] is None and value['sha256'] is None:return
            file_ref(value,root)
        else:
            for child in value.values():validate_refs(child,root)
    elif isinstance(value,list):
        for child in value:validate_refs(child,root)
def validate(card,root=ROOT):
    validate_refs(card,root)
    if card.get('version')!=1 or card.get('mode') not in ('EXPLORE','CONFIRM') or card.get('state') not in ('DRAFT','EXISTING_HANDLE'):raise ValueError('Unknown card schema/mode/state')
    if not card.get('question') or not card.get('decision_rule',{}).get('branches'):raise ValueError('Question and decision branches required')
    if card.get('authorization',{}).get('new_gpu_dispatch') is not False:raise ValueError('This reader grants no GPU authority')
    budget=card['budget']
    if budget['cumulative_cap_gpuh']!=226 or budget['deployment_absolute_seconds']!=257.7712338712067 or budget['deployment_ratio']!=.8:raise ValueError('Budget contract changed')
    if budget['acceptance']!={'point':'V_le_1','robust':'prompt_paired_bootstrap_95_upper_le_1'}:raise ValueError('Point and robust acceptance must remain distinct')
    dedupe=card['dedupe']
    if dedupe['identity']!='full_execution_fingerprint_v1' or dedupe['method_aliases_only'] is not True or set(dedupe['preserve_slots'])!=PRESERVE:raise ValueError('Physical repeats/controls may not be deduplicated')
    if not card['quality']['reuse_repeat_scores_only_after_latent_and_RGB_equal'] or not card['timing']['all_formal_requests_measured'] or not card['timing']['same_input_fresh_native']:raise ValueError('Evidence reuse/timing contract changed')
    if card['state']=='DRAFT':
        # Even draft file refs, when supplied, must be truthful.
        for r in (card['decision_rule']['contract'],card['scope']['manifest'],budget['quote']):
            if r.get('path') is not None:file_ref(r,root)
        return dict(status='DRAFT_REVIEW_ONLY',ready_for_new_GPU=False,remote_actions_allowed=False,pending=['frozen_scope_and_quote','affected_path_CPU_evidence','fresh_input_audit_if_required','explicit_GPU_authorization_and_new_adapter'],GPU_submissions=0)
    adapter=card['backend']['adapter']
    if adapter not in ADAPTERS:raise ValueError('Adapter is not allowlisted')
    _,raw=file_ref(card['backend']['bindings'],root);binding=json.loads(raw)
    if binding['adapter']!=adapter or binding['controller']!=ADAPTERS[adapter]:raise ValueError('Wrong reader binding')
    for name,h in binding['components'].items():file_ref(dict(path=name,sha256=h),root)
    if ADAPTERS[adapter] not in binding['components']:raise ValueError('Controller binding missing')
    # Exact registered scope remains authoritative; YAML is only an operational view.
    _,raw=file_ref(card['scope']['manifest'],root);manifest=json.loads(raw)
    sys.path.insert(0,str(root/'src'))
    from wcomr.policy_generator_r1.shared66_card import check_card
    check_card(manifest)
    file_ref(card['decision_rule']['contract'],root);file_ref(budget['quote'],root)
    if budget['quote']!=card['scope']['manifest']:raise ValueError('Quote must use registered whole manifest')
    _,raw=file_ref(card['backend']['launch'],root);launch=json.loads(raw)
    _,raw=file_ref(card['backend']['stage'],root);stage=json.loads(raw)
    for key in ('stage','source_revision','registration_sha256'):
        if launch[key]!=stage[key]:raise ValueError('Mixed existing handles')
    if launch['run_id']!='cara-shared-cal66-ada-r1' or launch['launch_id']!=binding['launch_id']:raise ValueError('Wrong existing launch')
    if launch['scope_counts']!=manifest['scope'] or launch['scope_counts']['total_paths']!=card['scope']['physical_paths'] or launch['scope_counts']['formal_roles']!=card['scope']['logical_roles']:raise ValueError('Denominator mismatch')
    if launch['billed_limit_GPUh']!=budget['cap_gpuh'] or launch['forecast_GPUh']!=budget['forecast_gpuh']:raise ValueError('Quote mismatch')
    post=card['post_release_cpu']
    if post!={'cpus':2,'memory_gib':8,'wall_hours':6,'cap_vcpuh':12}:raise ValueError('CPU envelope changed')
    return dict(status='EXISTING_HANDLE_READER_VALIDATED',adapter=adapter,launch_id=launch['launch_id'],stage=launch['stage'],source_revision=launch['source_revision'],physical_paths=66,ready_for_new_GPU=False,remote_actions_allowed=True,allowed_commands=['validate','plan','recover','capture','accept'],GPU_submissions=0)
def command(card,action,output,mode='terminal',capture=None,root=ROOT):
    result=validate(card,root)
    if action not in ('recover','capture','accept') or not result['remote_actions_allowed']:raise ValueError('Only existing-handle observation/acceptance supported')
    if mode not in ('admission','halfway','terminal'):raise ValueError('Invalid capture mode')
    out=Path(output).resolve()
    if not out.is_relative_to((root/'reports').resolve()) or out.exists():raise ValueError('New reports receipt required')
    args=[sys.executable,str(root/ADAPTERS[result['adapter']])]
    if action=='recover':args+=['recover','--stage-ref',str(root/card['backend']['stage']['path'])]
    elif action=='capture':args+=['capture','--launch-ref',str(root/card['backend']['launch']['path']),'--mode',mode]
    else:
        cp=Path(capture).resolve() if capture else None
        if cp is None or not cp.is_relative_to((root/'reports').resolve()):raise ValueError('Original capture required')
        saved=json.loads(cp.read_bytes());launch=saved.get('launch',{})
        if launch.get('launch_id')!=result['launch_id']:raise ValueError('Capture belongs to another launch')
        args+=['accept-gpu','--capture',str(cp)]
    return args+['--output',str(out)]
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--card',type=Path,required=True)
    p.add_argument('--command',choices=['validate','plan','recover','capture','accept'],default='validate')
    p.add_argument('--output',type=Path);p.add_argument('--capture',type=Path);p.add_argument('--mode',choices=['admission','halfway','terminal'],default='terminal');a=p.parse_args()
    card=yaml.safe_load(a.card.read_text());v=validate(card)
    if a.command in ('validate','plan'):
        v.update(card_ref=str(a.card),card_sha256=digest(a.card.read_bytes()),server_contacted=False,ledger_written=False)
        if a.command=='plan':v['steps']=['validate immutable references','use existing recover/capture when requested','independent original acceptor after completion'];v['new_dispatch_supported']=False
        if a.output:
            with a.output.open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
        print(json.dumps(v,ensure_ascii=False));return
    if a.output is None:p.error('--output required for observation')
    args=command(card,a.command,a.output,a.mode,a.capture);subprocess.run(args,check=True,cwd=ROOT)
    if a.command=='accept' and not json.loads(a.output.read_text()).get('full_protocol_accepted'):raise SystemExit(2)
if __name__=='__main__':main()
