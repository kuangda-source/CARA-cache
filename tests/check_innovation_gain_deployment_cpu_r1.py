"""Whole36 candidate-owned trajectory controls using the accepted CPU harness."""
import inspect
from pathlib import Path
import torch
import check_scout_parent_cpu_v22 as base
from wcomr.innovation_gain_deployment_r1 import execute as deploy


TAIL='''    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));origin=initial.fingerprint()
    root=Path(artifact_root)/('deploy_flow_'+str(flow));results={}
    sample=type(selected[0])('IG_DEPLOYMENT_CPU')
    roles=[('WC_C',None),('A_PHASE',None),('FULL',None),('DEEP',None),('DCTA',None),
           ('IG_SCALAR',(.3,.3)),('IG_BAND',(.2,.8)),('IG_ZERO',(0.,0.)),('IG_ONE',(1.,1.))]
    try:
        initial.restore()
        control=execute(inference,sample,enabled=False,context=(sample.name,'CPU_ONLY',PARENT_FINGERPRINT),
            sink=lambda _:None,copy_cap=1<<30,table_parameters=tables,previous_parameters=prior,
            runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,specs=specs,
            inference_module=inference_module,expected_shape=[1,8,2,8,8],output=root/'CONTROL_C',audit=True)
        for role,gains in roles:
            initial.restore()
            value=_deploy(inference,sample,role='IG_SCALAR' if role in ('IG_ZERO','IG_ONE') else role,gains=gains,
                feature_context=(sample.name,'CPU_ONLY',PARENT_FINGERPRINT),table_parameters=tables,previous_parameters=prior,
                runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=cal,specs=specs,
                inference_module=inference_module,expected_shape=[1,8,2,8,8],output=root/role,audit=True)
            assert value['status']=='COMPLETE' and value['solver_steps']==value['guided_pairs']==36
            hist=value['gain_deployment_history'];assert len(hist)==36
            assert all(h['teacher_calls']==0 and h['fallback_reason'] is None for h in hist)
            assert [h['step'] for h in hist if h['true_anchor_write']]==list(range(1,22))+[24,27,30,36]
            assert all(h['actual_head_calls']==(2 if h['true_anchor_write'] or role=='WC_C' else 4) for h in hist)
            results[role]=value
        def equal(a,b):
            assert torch.equal(a['final_latent'],b['final_latent'])
            assert all(torch.equal(x,y) for x,y in zip(a['guided'],b['guided']))
        equal(control,results['WC_C']);equal(results['FULL'],results['IG_ZERO']);equal(results['DEEP'],results['IG_ONE'])
        return [dict(flow=flow,status='PASS',actual_CPU_paths=10,roles=[r for r,g in roles],
            C_parent_endpoint_equal=True,FULL_IG0_trajectory_equal=True,DEEP_IG1_trajectory_equal=True,
            all36_head_counts_verified=True,all_candidates_free_running=True,teacher_calls=0,real_model=False)]
    finally:
        initial.restore();assert initial.fingerprint()==origin
'''


def run(runtime,artifact_root,body_source=None,actual_request=None):
    original=base.body
    source=body_source or inspect.getsource(original)
    prefix=source[:source.index('    initial=CompleteStateRoundtrip(')]
    namespace={**vars(base),'_deploy':deploy,'_actual_request':actual_request}
    tail=TAIL if actual_request is None else TAIL.replace("type(selected[0])('IG_DEPLOYMENT_CPU')","_actual_request('IG_DEPLOYMENT_CPU')")
    exec(compile(prefix+tail,__file__+'#accepted-small-CPU-setup','exec'),namespace)
    base.body=namespace['body']
    try:
        value=base.run(runtime,lambda p:torch.load(p,map_location='cpu',weights_only=True),artifact_root)
        return dict(status='IG_CLOSED_LOOP_CPU_PASS_NOT_MODEL_RESULT',checks=value['checks'],
                    actual_CPU_paths=sum(c['actual_CPU_paths'] for c in value['checks']),GPU_submissions=0)
    finally:base.body=original
