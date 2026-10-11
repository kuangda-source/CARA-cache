"""Both flow modes: complete real sampler body with explicitly Toy CPU weights."""
import ast
import copy
import inspect
import json
from pathlib import Path
from textwrap import dedent

import torch

from wcomr import p_reference_same_state_sampling_r1 as sampling
from wcomr.p_reference_same_state_tensor_audit_r1 import audit
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.early_head_elision_sampling_r4 import native_checkpoint_head


def load(name):
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location(name, Path(__file__).with_name(name+'.py'))
    module = module_from_spec(spec); spec.loader.exec_module(module); return module


BODY = r'''    results=[]
    try:
        names=scope['sample_names'];chosen=[type(samples[0])(n) for n in names]
        local={**config,'sample_names':names,'run_id':'P_REFERENCE_SAME_STATE_CPU'}
        contexts=[(local['run_id']+':'+n,'Toy_actual_modules','actual_condition_'+n) for n in names]
        output=Path(artifact_root)/('flow_ON' if flow else 'flow_OFF')
        output.mkdir(parents=True,exist_ok=False);state={}
        def save():
            p=output/'receipt.json';tmp=p.with_suffix('.tmp')
            tmp.write_text(json.dumps(state,indent=2,allow_nan=False)+'\n');tmp.replace(p)
        batch,proof=sampling.compile_batch(scope,calibration=calibration,policy_specs=policy_specs)
        batch(inference,chosen,wc,settings,state=state,save=save,output=output,
            inference_module=inference_module,contexts=contexts,mode_setup=mode,runtime=runtime,
            config=local,rf_module=rf)
        assert state['initial_state_restored'] and all(float(b)==0 for b in net.buffers())
        assert not any(m.training for m in net.modules())
        assert original_forward_attributes==[('forward' in vars(b.mlp),vars(b.mlp).get('forward')) for b in net.blocks]
        verdict=sampling.verify_batch(state,scope)
        raw=audit(state,output,tensor_loader,local['expected_shape'])
        assert len(raw['files'])==44 and raw['actual_tensors_reloaded']==580
        assert raw['actual_direct_tensor_comparisons']==210
        refusals=[]
        for fault in ('missing_event','missing_suffix','missing_age','teacher_leak','wrong_birth','wrong_sigma','missing_readout','wrong_readout_input','wrong_source_hash','wrong_D_state_hash','missing_candidate_restore','wrong_deployed_readout','wrong_shared_alpha'):
            bad=copy.deepcopy(state);row=bad['requests'][0]['paths'][1]
            event=row['origins'][0];branch=event['branches'][2];point=branch['age_points'][0]
            if fault=='missing_event':row['origins'].pop()
            elif fault=='missing_suffix':event['branches'].pop()
            elif fault=='missing_age':branch['age_points'].pop()
            elif fault=='teacher_leak':row['collection_complete']['deployment']['teacher_calls']=1
            elif fault=='wrong_birth':point['actual_source_and_decision_history']['working_sources'][0]['created_step']+=1
            elif fault=='wrong_sigma':point['sigma_index']+=1
            elif fault=='missing_readout':point['five_reference_readouts'].pop()
            elif fault=='wrong_readout_input':point['five_reference_readouts'][0]['input_sha256']='changed'
            elif fault=='wrong_source_hash':point['five_reference_readouts'][0]['source_cache_sha256']='changed'
            elif fault=='wrong_D_state_hash':point['five_reference_readouts'][0]['true_D_full_state_sha256']='changed'
            elif fault=='missing_candidate_restore':point['serial_restore_guards'].pop()
            elif fault=='wrong_shared_alpha':point['five_reference_readouts'][0]['readout']['shared_alpha']=1
            else:point['deployed_reference_unchanged']='P_REFERENCE_SCALAR'
            try:sampling.verify_batch(bad,scope)
            except (ValueError,KeyError):refusals.append(fault)
            else:raise AssertionError('Invalid whole source-age evidence accepted: '+fault)
        target=Path(raw['files'][-1]['path']);original=target.read_bytes()
        try:
            target.write_bytes(original[:-1])
            try:audit(state,output,tensor_loader,local['expected_shape'])
            except ValueError:pass
            else:raise AssertionError('Truncated actual diagnostic tensor accepted')
        finally:target.write_bytes(original)
        results.append({'status':'PASS','flow':flow,'receipt':state,'verdict':verdict,
            'actual_tensor_audit':raw,'scope_refusals':refusals,'actual_truncation_refused':True,
            'compiler_proof':proof,'all_initial_state_and_installed_methods_restored':True,
            'explicit_Toy_weights_prepare_decode_and_synthetic_policy':True})
        return results
'''


def run(runtime, tensor_loader, artifact_root):
    root = Path(__file__).resolve().parents[1]
    scope = json.loads((root/'manifests/wc_p_reference_same_state_complete_scope_r1_20261011.json').read_text())
    gains = {s: (1. if s in (12, 13, 25, 27) else 1000.) for s in range(1, 37)}
    calibration = Calibration('SYNTHETIC_FROZEN_EVENT_CPU_ONLY',
        {(a, s): 1. for a in range(1, 36) for s in range(a+1, 37)}, gains)
    spec = {'threshold': 2., 'costs': Costs('SYNTHETIC_P_CHEAPEST', 3., 4., 1.),
        'partial_prior': CreationPhasePrior('SYNTHETIC_POSITIVE_FLOOR', .005, .3,
            early_creation_floor=.005, late_creation_floor=.02),
        'working_epoch_strategy': scope['working_epoch_strategy']}
    original = load('check_partial_mlp_guided_sampling_cpu_r1')
    source = dedent(inspect.getsource(original.exercise)); start = source.index('    results=[]\n')
    end = source.index('    finally:\n        inference.pipe._get_data_batch_input=original_prepare', start)
    old = source[start:end]; changed = source[:start]+BODY+source[end:]
    identity='net.final_layer=DeclaredIdentityHead().eval()'
    native='net.final_layer=_native_head(runtime,8,1,1,8,use_adaln_lora=True,adaln_lora_dim=4,use_wan_fp32_strategy=True).eval()'
    old_emb='net.t_embedder=lambda t:((t.float()/1000).unsqueeze(-1).expand(*t.shape,8),None)'
    new_emb='net.t_embedder=lambda t:((t.float()/1000).unsqueeze(-1).expand(*t.shape,8),.02*torch.ones(*t.shape,24))'
    assert changed.count(identity)==changed.count(old_emb)==1
    changed=changed.replace(identity,native).replace(old_emb,new_emb)
    inverse=changed.replace(native,identity).replace(new_emb,old_emb).replace(BODY,old)
    assert inverse == source and ast.dump(ast.parse(inverse)) == ast.dump(ast.parse(source))
    namespace = {**original.exercise.__globals__, 'sampling': sampling, 'scope': scope,
        'calibration': calibration, 'policy_specs': {scope['method']: spec}, 'audit': audit, '_native_head':native_checkpoint_head}
    exec(compile(changed, __file__+'#whole-CPU-exercise', 'exec'), namespace)
    value = load('check_full_sampling').run(runtime, exercise=lambda **kw: namespace['exercise'](
        runtime=Path(runtime), tensor_loader=tensor_loader, artifact_root=artifact_root, **kw))
    checks = value['checks']
    assert len(checks) == 2 and {c['flow'] for c in checks} == {False, True}
    assert not torch.cuda.is_initialized()
    return {'checks': checks, 'full_parent_paths': 8, 'events': 8, 'suffixes': 32,
        'same_state_age_points': 48, 'actual_pair_computations': 688, 'actual_CFG_calls': 1376,
        'actual_tensors_reloaded': 1160, 'actual_files_reloaded': 88,
        'actual_direct_tensor_comparisons': 420, 'scope_refusals': 26,
        'actual_truncation_refusals': 2, 'fixture_inverse_bytes_and_AST_equal': True,
        'real_GPU_model_or_video_or_quality_claim': False, 'GPU_submissions': 0}
