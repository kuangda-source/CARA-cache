"""Join deterministic native CPU clocks to historical H1 scalar prefixes.

This is feature reconstruction only. Estimated H1 scores are never teachers;
receipt row IDs are not physical state snapshots, and no model is fitted.
"""
import math

from .w3_causal_trend_r1 import CausalHistory,Observation,coherent_scores

STATUS='ACTUAL_PINNED_UNIPC_KARRAS_CONTINUOUS_CLOCK_CPU_REPLAY'


def validate_clock(clock):
    if (clock.get('status')!=STATUS
            or clock.get('provenance')!='NATIVE_SCHEDULER_REPLAY_NOT_ORIGINAL_PER_RUN_SIGMA_CAPTURE'
            or clock.get('constructor_kwargs')!={'num_train_timesteps':1000,'shift':1,'use_dynamic_shifting':False}
            or clock.get('set_timesteps_kwargs')!={'num_inference_steps':35,'device':'cpu','shift':1,'use_kerras_sigma':True}
            or clock.get('num_updates')!=36 or clock.get('sigma_dtype')!='torch.float32'
            or clock.get('timestep_dtype')!='torch.int64' or clock.get('CUDA_initialized') is not False
            or any(clock.get(k)!=0 for k in ('GPU_submissions','weights_loaded','model_forwards'))
            or clock.get('budget_before_sha256')!=clock.get('budget_after_sha256')
            or not clock.get('integer_timestep_div1000_not_used_as_sigma')):
        raise ValueError('Real source-bound native scheduler CPU replay required')
    t=clock['timesteps'];s=clock['sigmas']
    if (len(t)!=36 or len(s)!=37 or s[-1]!=0
            or any(type(v) is not int for v in t)
            or any(not isinstance(v,(float,int)) or not math.isfinite(v) or v<0 for v in s)
            or any(s[i]<=s[i+1] for i in range(36))
            or all(s[i]==t[i]/1000 for i in range(36))):
        raise ValueError('Original36 continuous float32 sigmas including terminal zero required')
    return tuple(float(v) for v in s)


def replay(path,clock,*,input_sha256,window=4):
    sigmas=validate_clock(clock)
    if path['method'] not in ('H1_LOW','H1_MID','H1_HIGH') or len(path['rows'])!=36:
        raise ValueError('Complete original H1 path required')
    if ([r['step'] for r in path['rows']]!=list(range(1,37))
            or [r['scheduler_timestep'] for r in path['rows']]!=clock['timesteps']):
        raise ValueError('Every saved timestep must match actual native schedule, no interpolation')
    history=CausalHistory(path['scene'],0,window=window);output=[]
    for row in path['rows']:
        packets=row['paid_packets'];paid=len(packets)==2;source=row['source']
        if packets and (not paid or [v[0] for v in packets]!=[0,1]):
            raise ValueError('Original ordered paid branch pair or explicit missing required')
        o=Observation(path['scene'],0,row['step'],input_sha256+':'+path['id']+':'+str(row['step']),sigmas[row['step']-1],
            source,source+':'+str(row['source_birth']) if source else None,row['source_age'],row['root_floor'],
            packets[0][2] if paid else None,packets[1][2] if paid else None,
            row['local_proxy'],row['gain'],row['protected'],row['category']=='OPTIMIZER')
        fs=history.push(o)
        if any(any(n>row['step'] for n in f.prefix_steps) for f in fs.values()):raise ValueError('Future feature leakage')
        record={'step':row['step'],'pre_action_source':source,'source_birth':row['source_birth'],
            'source_age':row['source_age'],'original_reason':row['reason'],'protected':o.protected,
            'original_support':o.calibration_supported,'sigma':sigmas[row['step']-1],
            'delta_sigma':sigmas[row['step']]-sigmas[row['step']-1],
            'sigma_provenance':clock['provenance'],'original_timestep':row['scheduler_timestep'],
            'state_identity_scope':'RECEIPT_ROW_ONLY_NOT_PHYSICAL_SNAPSHOT',
            'features':{m:{'names':f.names,'values':f.values,'prefix_steps':f.prefix_steps} for m,f in fs.items()},
            'real_same_state_teacher_label':None,'teacher_estimate_or_future_action_used_as_input':False}
        if row['step']==31:
            decision=coherent_scores([-1.,-1.],o,costs={'C':1.,'A':2.,'D':3.},lam=1.)
            if decision['action']!='D' or decision['scores'] is not None:raise ValueError('D31 support fallback changed')
            record['original_D31_age7_fallback_kept']=True
        output.append(record)
    return {'id':path['id'],'scene':path['scene'],'method':path['method'],'seed':0,'window':window,
        'rows':output,'paid_pairs':sum(len(r['paid_packets'])==2 for r in path['rows']),
        'supported_rows':sum(r['category']=='OPTIMIZER' for r in path['rows']),
        'all36_native_timesteps_match':True,'real_labels_available':False,'predictor_fitted':False}
