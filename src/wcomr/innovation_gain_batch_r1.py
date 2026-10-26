"""Four complete parent paths and exact saved-state B1 calibration/replay.

The same orchestration is used by the declared CPU model and real model entry.
No partial denominator, surrogate score or local error is a video-quality result.
"""
import time
from pathlib import Path

import torch

from .gpu_budget_pool_v2 import atomic_json
from .innovation_gain_assets_r1 import GainAssetStore, load_state, sha
from .innovation_gain_fit_r1 import calibration
from .policy_interval_readout_r1 import guided
from .scout_readout_v22 import STATE_STEPS


def collect(root, prompts, request, replay, *, byte_limit, check_space, save):
    root=Path(root)
    if len(prompts)!=2 or len(set(prompts))!=2:raise ValueError('Exactly two frozen CAL prompts')
    assets=GainAssetStore(root/'assets',byte_limit=byte_limit,check_space=check_space)
    state=dict(status='B1_PARENT_COLLECTION',rows=[],controls=[],replays=[],started_unix=time.time(),
               real_model_quality_claim=False)
    def checkpoint():save(state)
    checkpoint()
    for prompt in prompts:
        control=None
        for enabled in (False,True):
            row=dict(prompt=prompt,observer=enabled,status='RUNNING');state['rows'].append(row);checkpoint()
            try:
                result=request(prompt,enabled,assets.save,root/prompt/('ON' if enabled else 'OFF'))
                if result['status']!='COMPLETE' or result['guided_pairs']!=36 or result['solver_steps']!=36:
                    raise ValueError('Complete36 parent path required')
                row.update(status='COMPLETE',video_path=result['video_path'],video_sha256=sha(result['video_path']))
                if not enabled:control=result
                else:
                    if (len(control['guided'])!=36 or len(result['guided'])!=36
                            or not all(torch.equal(x,y) for x,y in zip(control['guided'],result['guided']))
                            or not torch.equal(control['final_latent'],result['final_latent'])
                            or row['video_sha256']!=sha(control['video_path'])):
                        raise ValueError('Observer changed full parent trajectory or encoded video')
                    state['controls'].append(dict(prompt=prompt,all36_guided_equal=True,
                        final_latent_equal=True,video_bytes_equal=True))
                    control=None
                del result
            except BaseException as exc:
                row.update(status='TECH_FAILED',error_type=type(exc).__name__,error=str(exc));checkpoint();raise
            checkpoint()
    fitted=calibration(assets.states,prompts,STATE_STEPS)
    state.update(status='B1_ACTUAL_SAVED_STATE_REPLAY',calibration=fitted);checkpoint()
    folds={f['held_out_prompt']:f['coefficients'] for f in fitted['folds']}
    for row in assets.states:
        check_space();payload=load_state(assets.root,row['artifact'])
        # Gate the exact restored inputs before paying for either fitted proposal.
        for gain,label in (((0.,0.),'FULL'),((1.,1.),'R4_GLOBAL')):
            value=replay(payload,gain)
            if not all(torch.equal(x.detach().cpu(),y) for x,y in zip(value['outputs'],payload['readouts'][label]['outputs'])):
                raise ValueError('Stored actual adapter endpoint changed: '+label)
            state['replays'].append(dict(prompt=row['prompt'],step=row['step'],kind='ENDPOINT',role=label,exact=True))
            del value
        teacher=guided(payload['teacher']).double()
        for kind,coefficients in (('LOPO',folds[row['prompt']]),('FINAL',fitted['final'])):
            for role in ('IG_SCALAR','IG_BAND'):
                gains=coefficients[role];value=replay(payload,gains)
                output=guided(tuple(x.detach().cpu() for x in value['outputs'])).double()
                mse=float((output-teacher).square().mean())
                if not torch.isfinite(torch.tensor(mse)):raise ValueError('Nonfinite actual replay error')
                state['replays'].append(dict(prompt=row['prompt'],step=row['step'],kind=kind,role=role,
                    gains=gains,actual_guided_MSE=mse,baseline_FULL_MSE=row['moments']['baseline_FULL_MSE'],
                    baseline_DEEP_MSE=row['moments']['baseline_DEEP_MSE']))
                del value,output
        del payload,teacher
        checkpoint()
    if len(assets.states)!=12 or len(state['replays'])!=72:raise ValueError('Incomplete B1 replay denominator')
    summary={}
    for kind in ('LOPO','FINAL'):
        summary[kind]={}
        for role in ('IG_SCALAR','IG_BAND'):
            rows=[r for r in state['replays'] if r['kind']==kind and r['role']==role]
            summary[kind][role]={prompt:{k:sum(r[k] for r in rows if r['prompt']==prompt)/6
                for k in ('actual_guided_MSE','baseline_FULL_MSE','baseline_DEEP_MSE')} for prompt in prompts}
    state.update(status='B1_LOCAL_READOUT_COMPLETE_PENDING_VIDEO_VALIDATION',ended_unix=time.time(),
        summary=summary,complete_parent_paths=4,states=12,original_readout_positions=72,
        additional_guided_replays=108,additional_head_pairs=216,stored_bytes=assets.used,
        deployment_coefficients=fitted['final'],mainline_admitted=False)
    checkpoint();atomic_json(root/'B1-results.json',state)
    return state
