"""Full pinned sampler tests, declared small CPU weights; no scientific scores."""
import inspect
import torch
from check_scout_parent_cpu_v22 import load
from wcomr.scout_common_long_r1 import execute, ALL_LABELS, NEW_LABEL
from wcomr.scout_cfg_common_proposal_r1 import common_long_proposal

def run(runtime, artifacts, host, sample):
    old=load('check_scout_parent_cpu_v22')
    original=old.body
    source=inspect.getsource(original)
    source=source.replace("readout_positions=36", "readout_positions=42")
    source=source.replace("payloads.append(v['step'])", "_check(v)\n                    payloads.append(v['step'])")
    def check(v):
        a=v['readouts']['A_PHASE']; new=v['readouts'][NEW_LABEL]
        assert v['readout_head_pairs']==(13 if v['step']-v['source_anchor_steps'][-1]<3 else 16)
        if v['step']-v['source_anchor_steps'][-1]<3:
            assert all(torch.equal(x,y) for x,y in zip(a['outputs'],new['outputs']))
            assert new['evaluated_components']==['A_PHASE']
        else:
            expected=common_long_proposal(C=v['readouts']['WC_C']['outputs'],
                A_component=a['component_outputs'],R4_component=v['readouts']['R4_GLOBAL']['component_outputs'],
                step=v['step'],anchor_step=v['source_anchor_steps'][-1])
            assert all(torch.equal(x,y) for x,y in zip(expected,new['outputs']))
            assert new['alpha']==.5 and len(new['state_roundtrips'])==3
        assert not new['teacher_used']
    completed=[]
    def entry(inference, old_sample, **kw):
        real=type(sample).model_validate({**sample.model_dump(), 'name':old_sample.name})
        result=execute(inference,real,timing_host=host,timing_cpu_validation=True,**kw)
        if result['status']=='COMPLETE':
            assert 0 < result['paper_denoise_decode_seconds'] <= result['full_request_seconds']
            assert not result['paper_timing']['deployment_latency_eligible']
            assert not result['candidate_free_running']
            completed.append(result['scout_enabled'])
        return result
    ns={**vars(old),'execute':entry,'LABELS':ALL_LABELS,'_check':check}
    exec(compile(source,__file__+'#affected-full-parent','exec'),ns)
    old.body=ns['body']
    result=old.run(runtime,lambda p:torch.load(p,map_location='cpu',weights_only=True),artifacts)
    assert len(completed)==8
    result.update(status='COMMON_LONG_REAL_SOURCE_CPU_PASS_NOT_GPU',readout_positions=168,
        actual_CPU_paths=8,selected_states=24,readout_labels=list(ALL_LABELS),
        short_A_exact=True,long_reference_exact=True,real_frozen_request=True,
        dual_clocks=True,teacher_free_candidate=True,scientific_gate_evaluated=False,
        candidate_free_running=False)
    return result
