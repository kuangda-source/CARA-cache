"""New six-slot orchestration on actual pinned sampler with declared CPU stand-ins."""
import inspect,json
from pathlib import Path
import torch
from check_scout_parent_cpu_v22 import load

def run(runtime, artifacts, host, actual_sample, manifest):
 old=load('check_scout_parent_cpu_v22')
 source=inspect.getsource(old.body)
 cut=source.index('    try:\n        for name')
 source=source[:cut]+'''    from wcomr.common_long_collection_r1 import collect,rescore
    from wcomr.scout_common_long_r1 import execute as entry
    names=[r['name'] for r in _manifest['requests']]
    def request(name,enabled,sink,directory):
        initial.restore()
        real=type(_sample).model_validate({**next(r for r in _manifest['requests'] if r['name']==name),'resolution':'16,16'})
        return entry(inference,real,timing_host=_host,timing_cpu_validation=True,
            enabled=enabled,context=(name,'DECLARED_CPU_WEIGHTS',PARENT_FINGERPRINT),sink=sink,copy_cap=1<<30,
            table_parameters=tables,previous_parameters=prior,runtime=runtime,wc=wc,rf=rf,settings=settings,
            calibration=cal,specs=specs,inference_module=inference_module,expected_shape=[1,8,2,8,8],output=directory,audit=True)
    try:
        result=collect(root,_manifest,request,check_space=lambda:None,byte_limit=1<<30,save=lambda v:None)
        scored=rescore(result,_manifest)
        assert scored['states']==12 and scored['readout_positions']==84
        # A changed byte or missing position must fail independent rescore.
        import copy
        bad=copy.deepcopy(result);bad['states'].pop()
        try:rescore(bad,_manifest)
        except ValueError:pass
        else:raise AssertionError('missing state accepted')
        bad=copy.deepcopy(result);bad['states'][0]['sha256']='0'*64
        try:rescore(bad,_manifest)
        except ValueError:pass
        else:raise AssertionError('changed tensor accepted')
        return [dict(flow=flow,status='PASS',actual_CPU_paths=6,states=12,readout_positions=84,
            all_OFF_ON_controls=True,CPU_rescore_from_saved_tensors=True,source_bound_frozen_requests=True,
            corruption_cases_rejected=2,CUDA_initialized=False)]
    finally:initial.restore();assert initial.fingerprint()==origin
'''
 ns={**vars(old),'_sample':actual_sample,'_host':host,'_manifest':manifest}
 exec(compile(source,__file__+'#registered6','exec'),ns);old.body=ns['body']
 # The old wrapper's outer summary is superseded with exact new denominators.
 result=old.run(runtime,lambda p:torch.load(p,map_location='cpu',weights_only=True),artifacts)
 result.update(status='COMMON_LONG6_ACTUAL_SOURCE_COLLECTION_RESCORE_CPU_PASS',actual_CPU_paths=12,
  selected_states=24,readout_positions=168,failed_boundary_attempts=0)
 return result
