"""Exact numerical gate outside inference clocks; no quality-model scoring."""
import hashlib
from .policy_generator_r1.shared66_collection import tensor_digest
from .rv0_video_reader import decoded_video

def verify(rows):
    import torch
    if len(rows)!=12 or any(r['status']!='COMPLETE' for r in rows):raise ValueError('All12 diagnostic paths required')
    indexed={};checks=[]
    for r in rows:
        slot=r['slot'];a=r['tensor_artifact'];path=a['path']
        with open(path,'rb') as f:
            if hashlib.sha256(f.read()).hexdigest()!=a['sha256']:raise ValueError('Diagnostic tensor changed')
        x=torch.load(path,map_location='cpu',weights_only=True)
        if len(x['guided'])!=36:raise ValueError('Missing guided states')
        video=r['result']['video_path'];h=hashlib.sha256();frames=0
        with decoded_video(video) as stream:
            for rgb,pts,base in stream:h.update(rgb.tobytes());frames+=1
        if frames!=93:raise ValueError('Incomplete decoded RGB')
        indexed[(slot['scene'],slot['role'],slot['timing_enabled'])]=dict(guided=[tensor_digest(v) for v in x['guided']],latent=tensor_digest(x['final_latent']),RGB93=h.hexdigest(),inputs_and_RNG=r['diagnostic_inputs'])
        if slot['role']=='WC_WRAPPER_ALLD_U36' and r['result']['actions']!=['DD']*36:raise ValueError('allD did not execute full blocks')
    for scene in sorted({r['slot']['scene'] for r in rows}):
        for role in ('NATIVE_U36','WC_WRAPPER_ALLD_U36','WC_README_U36'):
            if indexed[(scene,role,False)]!=indexed[(scene,role,True)]:raise ValueError('Timing changes numerical path')
        if indexed[(scene,'NATIVE_U36',True)]!=indexed[(scene,'WC_WRAPPER_ALLD_U36',True)]:raise ValueError('True Native and wrapper-allD differ')
        checks.append(dict(scene=scene,three_role_OFF_ON_equal=True,Native_allD_equal=True))
    return dict(passed=True,checks=checks,comparison='exact guided/final latent/RGB93',scores_computed=0)

from contextlib import contextmanager
@contextmanager
def capture(inference, enabled):
    from .prepared_input import RNGState,input_signatures
    witness={}
    if not enabled:
        yield witness;return
    witness['entry_rng']=RNGState().signatures();witness['first_CFG_inputs']=[]
    def observe(module,args,kwargs):
        if len(witness['first_CFG_inputs'])<2:witness['first_CFG_inputs'].append(input_signatures(args,kwargs))
    hook=inference.pipe.model.net.register_forward_pre_hook(observe,with_kwargs=True)
    try:
        yield witness
    finally:
        hook.remove();witness['exit_rng']=RNGState().signatures()
