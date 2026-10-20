"""Recompute every interval label from raw guided output files, on CPU only."""
import math
from pathlib import Path
import statistics
import torch

from .policy_interval_assets_r1 import cells, rounds_for, sha, PROFILE, SCENES


def load_artifact(ref,root,loader=torch.load):
    path=Path(ref['path']).resolve();root=Path(root).resolve()
    if (not path.is_relative_to(root) or path.suffix!='.pt' or path.stat().st_size!=ref['bytes']
        or sha(path)!=ref['sha256']):
        raise ValueError('Changed, missing or escaped original tensor file')
    return loader(path,map_location='cpu',weights_only=True)


def audit_cells(rows,root,expected_shape,loader=torch.load):
    if [(r['source'],r['target']) for r in rows]!=cells():
        raise ValueError('Keep every legal cell, not a favourable observed subset')
    verified=[];teachers={}
    for row in rows:
        s,t=row['source'],row['target']
        if (row['source_anchor_steps']!=[s-1,s] or row['label_basis']!='TEACHER_CONDITIONED_PROPOSAL'
            or row['free_policy_history_truth'] or row['source_shadow_writes_parent']
            or row['extra_deep_teacher_pairs'] or row['actual_parent_action']!='DD'):
            raise ValueError('Teacher source provenance or no-write boundary differs')
        raw=load_artifact(row['artifact'],root,loader)
        ref=row['actual_same_state_teacher_ref']
        if ref['path'] not in teachers:teachers[ref['path']]=load_artifact(ref,root,loader)['D']
        d=teachers[ref['path']]
        if set(raw)!={'C','Phi','A_HALF'}:
            raise ValueError('All original output coordinates required')
        for v in [d]+list(raw.values()):
            if list(v.shape)!=expected_shape or v.dtype!=torch.float32 or not torch.isfinite(v).all():
                raise ValueError('Original finite FP32 guided tensor geometry differs')
        e=raw['C'].double()-d.double();update=raw['Phi'].double()-raw['C'].double()
        actual=dict(e2=e.square().mean().item(),ed=(e*update).mean().item(),d2=update.square().mean().item(),
            actual_half_MSE=(raw['A_HALF'].double()-d.double()).square().mean().item())
        if any(actual[k]!=row['statistics'][k] for k in actual):
            raise ValueError('Independently reread raw moments differ from journal')
        if float((raw['A_HALF']-(raw['C']+.5*(raw['Phi']-raw['C']))).abs().max())>row['statistics']['FP32_fusion_absolute_bound']:
            raise ValueError('Actual alpha path does not satisfy its declared coordinate contract')
        expected=[(r,a) for r,order in rounds_for(s,t) for a in order]
        if [(r['round'],r['action']) for r in row['price_trials']]!=expected:
            raise ValueError('Missing full balanced action-price repetitions')
        for trial in row['price_trials']:
            if (not math.isfinite(trial['seconds']) or trial['seconds']<=0
                or trial['shared_prefix_included'] or trial['restore_copy_hash_write_included']):
                raise ValueError('Shared/research intervals cannot be counted as action prices')
        verified.append(dict(source=s,target=t,statistics=actual,artifact_sha256=row['artifact']['sha256']))
    return dict(status='ALL406_ORIGINAL_CELLS_RAW_RECOMPUTED',cells=verified,
        original_tensor_files=len(rows)+len(teachers),teacher_outputs_reused_without_new_deep_calls=True)


def make_generator_bundle(formal_rows,profile_identity):
    """Source-conservative per-time proposal prices; no protected-action fill."""
    observed={r['scene']:r for r in formal_rows if r['mode']=='COLLECT' and r['status'] in ('COMPLETE','VIDEO_REJECTED')}
    if set(observed)!=set(SCENES):
        return dict(status='INCOMPLETE_FIT_DOMAIN_KEEP_REGISTERED_MISSINGNESS',generator_input_ready=False)
    labels=[];C=[];half=[];one=[];D=[];shared=[];nonstep=[]
    for scene in SCENES:
        row=observed[scene]
        if [(r['source'],r['target']) for r in row['interval_cells']]!=cells():
            raise ValueError('A proposal bundle needs every original CAL cell')
        for point in row['interval_cells']:
            labels.append(dict(member=scene,source=point['source'],target=point['target'],
                **{k:point['statistics'][k] for k in ('e2','ed','d2','fusion_contract')}))
    clocks=[r for r in formal_rows if r['mode'] in ('CONTROL','COLLECT') and r['status'] in ('COMPLETE','VIDEO_REJECTED')]
    if len(clocks)!=8 or any(len(r['action_clocks'])!=36 for r in clocks):
        return dict(status='INCOMPLETE_ALL36_COMPONENT_PRICE_DOMAIN',generator_input_ready=False)
    for t in range(1,37):
        D.append(statistics.mean(r['action_clocks'][t-1]['D_action_seconds'] for r in clocks))
        shared.append(statistics.mean(r['action_clocks'][t-1]['shared_prefix_seconds'] for r in clocks))
        if t in PROFILE['protected_dense']:
            C.append(None);half.append(None);one.append(None);continue
        for action,dest in [('C',C),('A_HALF',half),('A_ONE',one)]:
            per_prompt=[]
            for scene in SCENES:
                # Keep the worst observed source at this time within each CAL.
                # Formal repetitions average within a state; CAL then equal.
                values=[statistics.mean(p['seconds'] for p in point['price_trials']
                    if p['action']==action and p['round']!='WARMUP')
                    for point in observed[scene]['interval_cells'] if point['target']==t]
                per_prompt.append(max(values))
            dest.append(statistics.mean(per_prompt))
    for r in clocks:
        if r['mode']!='CONTROL':continue
        nonstep.append(max(0.,r['core_seconds']-sum(x['whole_pair_seconds'] for x in r['action_clocks'])))
    return dict(status='COMPLETE_REAL_CAL4_INTERVAL_AND_PRICE_PROPOSAL_BUNDLE',generator_input_ready=True,
        profile=PROFILE,profile_identity=profile_identity,fit_members=list(SCENES),statistics=labels,
        label_basis='TEACHER_CONDITIONED_PROPOSAL',free_running_error_truth=False,
        costs=dict(dense_seconds=D,C_seconds=C,A_seconds_by_alpha={'0.5':half,'1.0':one},
            shared_seconds=sum(shared)+statistics.mean(nonstep),shared_per_step_seconds=shared,
            nonstep_shared_seconds=statistics.mean(nonstep),profile_identity=profile_identity,
            measurement_protocol='PAID_PREFIX_ONCE_PLUS_SEPARATE_SOURCE_EXACT_READOUT_OR_D_INTERVAL',
            evidence_kind='OBSERVED_COMPONENT_PROPOSAL_COSTS',source_reduction='MAX_SOURCE_WITHIN_PROMPT_THEN_PROMPT_EQUAL',
            nonstep_baseline='OBSERVER_OFF_ALL_D_REFERENCE_INCLUDES_REGISTERED_TRACE_OVERHEAD_NOT_CLEAN_SPEED',
            unavailable_protected_readouts=None),
        exact_deployment_latency_guarantee=False,clean_repeated_speed_result=False,
        endpoint_or_TEST_quality_result=False)
