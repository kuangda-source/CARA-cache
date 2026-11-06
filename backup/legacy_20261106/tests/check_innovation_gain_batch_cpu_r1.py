"""Affected B1 production orchestration on accepted small CPU model paths."""
import inspect
import torch
import check_scout_parent_cpu_v22 as base
from wcomr.innovation_gain_batch_r1 import collect
from wcomr.innovation_gain_observer_r1 import execute,restore_readout_inputs
from wcomr.innovation_gain_r1 import InnovationGainKernel
from wcomr.cfg_guided_w1_forward import compile_collection
from wcomr.scout_parent_v22 import DenseObserver

TAIL='''    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));origin=initial.fingerprint()
    root=Path(artifact_root)/('batch_flow_'+str(flow));schemas={};prompts=['IG_CAL_CPU_0','IG_CAL_CPU_1']
    def request(name,enabled,sink,directory):
        initial.restore()
        sample=type(selected[0])(name)
        return _execute(inference,sample,enabled=enabled,condition_registry=schemas,
            context=(name,'CPU_ONLY',PARENT_FINGERPRINT),sink=sink,copy_cap=1<<30,
            table_parameters=tables,previous_parameters=prior,runtime=runtime,wc=wc,rf=rf,
            settings=settings,calibration=cal,specs=specs,inference_module=inference_module,
            expected_shape=[1,8,2,8,8],output=directory,audit=True)
    observer=_DenseObserver();_compile(runtime,wc,rf,observer)
    def replay(payload,gains):
        restored=_restore(payload,schemas[payload['context'][0]],'cpu')
        kernel=_Kernel(model,runtime,wc,rf,observer.warp,max_logical_copy_bytes=1<<30,gains=gains)
        return kernel.evaluate_gain(**restored)
    try:
        value=_collect(root,prompts,request,replay,byte_limit=2**30,check_space=lambda:None,save=lambda s:None)
        assert value['complete_parent_paths']==4 and value['additional_guided_replays']==108
        assert len(value['replays'])==72 and len(value['controls'])==2
        assert not value['mainline_admitted']
        return [dict(flow=flow,status='B1_BATCH_CPU_PASS',complete_paths=4,states=12,
            exact_saved_endpoint_replays=24,actual_LOPO_replays=24,actual_final_replays=24,
            additional_guided_replays=108,real_weights=False)]
    finally:initial.restore();assert initial.fingerprint()==origin
'''

def run(runtime,artifact_root,body_source,actual_request=None):
    original=base.body
    prefix=body_source[:body_source.index('    initial=CompleteStateRoundtrip(')]
    tail=TAIL if actual_request is None else TAIL.replace('type(selected[0])(name)','_actual_request(name)')
    ns={**vars(base),'_execute':execute,'_collect':collect,'_restore':restore_readout_inputs,
        '_Kernel':InnovationGainKernel,'_compile':compile_collection,'_DenseObserver':DenseObserver,
        '_actual_request':actual_request}
    exec(compile(prefix+tail,__file__+'#accepted-small-CPU-setup','exec'),ns)
    base.body=ns['body']
    try:
        v=base.run(runtime,lambda p:torch.load(p,map_location='cpu',weights_only=True),artifact_root)
        return dict(status='B1_BATCH_SOURCE_CPU_PASS_NOT_REAL_MODEL',checks=v['checks'],GPU_submissions=0)
    finally:base.body=original
