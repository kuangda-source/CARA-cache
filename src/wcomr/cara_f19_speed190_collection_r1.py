"""One complete CAL35 collection, with pre-formal equivalence and no retry."""
import copy
from pathlib import Path
import time

import torch

from .cara_fast_spec_r1 import digest
from .cara_f19_speed190_card_r1 import validate
from .cara_f19_speed190_requests_r1 import Requests
from .cara_s_endpoint_runner_r1 import observed_precision
from .full_sampling import CompleteStateRoundtrip
from .gpu_budget_pool_v2 import atomic_json,sha
from .h0_mode import establish_shared_eval,verify_shared_eval


def collect(adapter,output,before,*,save):
    card=validate(adapter.card);output=Path(output)
    if (output/'requests').exists():raise ValueError('Original CAL paths exist; recover only')
    state=dict(status='COLLECTING',scope_sha256=card['scope_sha256'],started_unix=time.time(),
        rows=[dict(slot=copy.deepcopy(s),status='NOT_REACHED') for s in card['matrix']],
        controls=[],CPU_fixture_only=adapter.cpu_validation,scientific_accepted=False)
    save(state);references={}
    try:
        for index,row in enumerate(state['rows']):
            slot=row['slot'];before(slot)
            if slot['section']=='FORMAL' and len(state['controls'])!=2:raise ValueError('Both complete equivalence gates must precede formal output')
            row['status']='RUNNING';save(state)
            result=adapter(slot,output/'requests'/slot['id'])
            if result['status']!='COMPLETE' or result['guided_pairs']!=36 or result['solver_steps']!=36:
                raise ValueError('Incomplete/rejected CAL request; denominator retained without retry')
            latent=result.pop('final_latent');guided=result.pop('guided',None)
            if slot['audit']:
                if guided is None or len(guided)!=36:raise ValueError('Full36 control output missing')
                tensors=dict(final_latent=latent,guided=guided)
                path=output/(slot['id']+'-control.pt');torch.save(tensors,path)
                result['control_tensor_artifact']=dict(path=str(path),sha256=sha(path),bytes=path.stat().st_size)
                if slot['section']=='GLOBAL_WARM':references[slot['role']]=path
                else:
                    name='NATIVE35' if slot['role']=='ALLD' else 'F19_A1'
                    reference=torch.load(references[name],map_location='cpu',weights_only=True)
                    if not torch.equal(latent,reference['final_latent']) or any(
                            not torch.equal(a,b) for a,b in zip(guided,reference['guided'])):
                        raise ValueError('Native/allD or original/OFF full36 output equivalence failed')
                    state['controls'].append(dict(reference=name,candidate=slot['role'],
                        full36_guided_and_latent_equal=True,RGB_equal_pending_release=True))
            if slot['eligible_clean_time'] and any(result[k] for k in
                    ('in_timing_guided_copies','in_timing_hashes','research_checkpoints')):
                raise ValueError('Diagnostic operations entered clean CAL timing')
            video=Path(result['video_path'])
            result['video_artifact']=dict(path=str(video),sha256=sha(video),bytes=video.stat().st_size)
            row.update(status='COMPLETE',result=result);save(state)
            del latent,guided
        state['status']='COMPLETE35_PENDING_RELEASE_SCORING'
        return state
    except BaseException as error:
        state.update(status='FAILED_NO_RETRY',error_type=type(error).__name__,error=str(error))
        raise
    finally:
        state['ended_unix']=time.time();save(state)


def collect_loaded(inference,samples,card,common,output,storage,mode_types,*,cpu_validation=False):
    model,net=inference.pipe.model,inference.pipe.model.net
    precision=observed_precision(model)
    if not cpu_validation and (precision['model_precision']!='torch.bfloat16'
            or precision['use_wan_fp32_strategy'] is not True
            or precision['conditional_frame_timestep']!=.1 or precision['outer_autocast'] is not False):
        raise ValueError('Original Cosmos production precision/conditioning required')
    versions=[(n,p,p._version,str(p.dtype)) for n,p in net.named_parameters()]
    mode=establish_shared_eval(net,mode_types)
    common['wc'].apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in card['settings'].items()})
    initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1));origin=initial.fingerprint()
    def verify():
        verify_shared_eval(net,mode)
        if any(p._version!=version or str(p.dtype)!=dtype for _,p,version,dtype in versions):raise ValueError('Model weights/precision changed')
    checks=0
    def before(slot):
        nonlocal checks
        storage.check();initial.restore()
        if initial.fingerprint()!=origin:raise ValueError('Complete request reset differs')
        verify();checks+=1
    output=Path(output)
    adapter=Requests(inference,samples,card,common,cpu_validation=cpu_validation)
    try:
        result=collect(adapter,output,before,save=lambda value:atomic_json(output/'collection.json',value))
    finally:
        initial.restore();verify()
        if initial.fingerprint()!=origin:raise ValueError('Final complete state restoration differs')
    return result,dict(request_boundary_checks=checks,precision=precision,
        model_precision_sha256=digest(precision),final_state_restored=True,CPU_fixture_only=cpu_validation)
