"""Two pinned flow loops: ordinary parent, old C suffix and fresh-teacher control."""
import inspect
from pathlib import Path
from textwrap import dedent

import torch

from wcomr import clean_speed20_r1 as clean
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.math_n2_sampling_owner_r1 import MathSamplingOwner
from wcomr.pi0_readout_suffix8_r1 import pi0_readout_suffix_install
from wcomr.teacher_first_velocity_alignment_r1 import teacher_first_alignment_install
from wcomr.rv0_causal import original_decode_tails
from wcomr.mid_coverage import tree_digest


def load(name):
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location(name, Path(__file__).with_name(name+'.py'))
    module = module_from_spec(spec); spec.loader.exec_module(module)
    return module


def body(inference, selected, wc, rf, settings, inference_module, runtime,
        config, flow, artifact_root, tensor_loader):
    model = inference.pipe.model; net = model.net; scheduler = model.sample_scheduler
    gains = {n: 1. for n in range(1, 37)}
    for n in (8, 9, 10, 25, 27, 28, 29, 30, 31, 32, 33, 34, 35):
        gains[n] = 0.
    gains[26] = 1000.
    cal = Calibration('SYNTHETIC_SUFFIX8_PHASE_COVERAGE',
        {(a,n): .99 for a in range(1,36) for n in range(a+1,min(a+6,36)+1)}, gains)
    spec = {'threshold': .04, 'costs': Costs('SYNTHETIC_SUFFIX8', 1., 4., 3.),
        'partial_prior': CreationPhasePrior('SYNTHETIC_SUFFIX8', .0001, .3,
            early_creation_floor=.0001, late_creation_floor=10.),
        'working_epoch_strategy': 'WORKING_P_AGE_NONZERO_REBASE'}
    specs = {'A_CPD_BETA1_ONE_PHASE': spec}
    params = {'gamma': .5, 'fingerprint': 'SYNTHETIC_ONLY'}
    config = dict(config, paired_prefix_reserve_bytes=config.get('paired_prefix_reserve_bytes',0))
    initial = CompleteStateRoundtrip(net, scheduler, torch.zeros(1))
    fingerprint = initial.fingerprint(); net0 = net.forward; pipe0 = inference.pipe.worldcache_enabled
    decoder, writer, tails = original_decode_tails(runtime, inference_module)
    ordinary_writer = inference_module.save_img_or_video
    cells = (('D','EARLY',3), ('D','LATE',2), ('P','EARLY',2), ('P','LATE',1))
    select = load('check_pi0_readout_suffix8_sampling_cpu_r1').select
    results = []
    try:
        for index, (sample, (source, phase, target)) in enumerate(zip(selected, cells)):
            directory = Path(artifact_root)/str(flow)/str(index)
            initial.restore(); holder = {}
            common = dict(runtime=runtime, wc=wc, rf=rf, settings=settings,
                calibration=cal, specs=specs, inference_module=inference_module,
                expected_shape=config['expected_shape'], audit=True)
            def parent(*args, **kwargs):
                owner = MathSamplingOwner(*args, math_parameters=params, source_mode='P_OFF', **kwargs)
                holder['parent'] = owner
                return owner
            with clean.patched(clean, 'CurrentBirthSamplingOwner', parent):
                ordinary = clean.execute(inference, sample, 'KEEP_A_P', output=directory/'ordinary', **common)
            point = select(sample.name, holder['parent'].history, source, phase, target)
            def endpoint_writer(root):
                def save(step, label, tensors):
                    d = directory/root/label; d.mkdir(parents=True)
                    raw = d/'vectors.pt'; torch.save(tensors, raw)
                    with clean.patched(inference_module, 'save_img_or_video', ordinary_writer):
                        video = decoder(inference.pipe, tensors['final_latent'].to(model.tensor_kwargs['device']))
                        path = writer(inference, video, d/sample.name)
                    assert path is not None and Path(path).exists()
                    return {'path':str(raw), 'tensor_sha256':tree_digest(tensors),
                        'video_path':str(path), 'original_tails':tails}
                return save
            initial.restore(); old_holder = {}
            with pi0_readout_suffix_install(clean, scheduler, point, config, endpoint_writer('old_suffix'),
                    params, old_holder, runtime=runtime, reverse_order=bool(index%2)):
                original_diagnostic = clean.execute(inference, sample, 'KEEP_A_P', output=directory/'old_parent', **common)
            original_C = next(b for b in old_holder['owner'].event_records[0]['branches'] if b['first_readout']=='C')
            C_raw = tensor_loader(Path(original_C['artifact']['path']), weights_only=True, map_location='cpu')
            initial.restore(); holder = {}
            def teacher_writer(step, tensors):
                d = directory/'teacher'; d.mkdir(parents=True)
                raw = d/'vectors.pt'; torch.save(tensors, raw)
                return {'path':str(raw), 'tensor_sha256':tree_digest(tensors)}
            with teacher_first_alignment_install(clean, scheduler, point, config,
                    endpoint_writer('new_suffix'), teacher_writer, params, holder,
                    runtime=runtime, reverse_order=bool(index%2)):
                new = clean.execute(inference, sample, 'KEEP_A_P', output=directory/'new_parent', **common)
            owner = holder['owner']; event = owner.event_records[0]
            assert len(owner.event_records)==1 and owner.teacher_injections==1
            for value in (original_diagnostic, new):
                assert value['status']==ordinary['status']=='COMPLETE'
                assert value['solver_steps']==value['guided_pairs']==36
                assert value['actions']==ordinary['actions']
                assert torch.equal(value['final_latent'],ordinary['final_latent'])
                assert all(torch.equal(a,b) for a,b in zip(value['guided'],ordinary['guided']))
                assert Path(value['video_path']).read_bytes()==Path(ordinary['video_path']).read_bytes()
            n=point['chosen']['step']; by={b['label']:b for b in event['branches']}
            assert set(by)=={'C_REPLAY','TEACHER_FIRST'}
            assert len(event['serial_restores'])==4 and len(event['teacher_record']['serial_restores'])==1
            assert event['actual_teacher_pairs']==1 and event['actual_teacher_calls']==2
            assert owner.actual_pair_computations==36+2*(37-n)+1
            teacher=tensor_loader(Path(event['teacher_record']['artifact']['path']),weights_only=True,map_location='cpu')
            assert tree_digest(teacher)==event['teacher_record']['artifact']['tensor_sha256']
            assert tree_digest((teacher['noise'],teacher['actual_latent'],teacher['timestep']))==event['teacher_record']['input_sha256']
            guided_teacher=teacher['teacher_velocity'][0]+7*(teacher['teacher_velocity'][0]-teacher['teacher_velocity'][1])
            assert event['teacher_record']['history']['action']=='DD'
            assert event['teacher_record']['history']['true_D_after']==n
            for label, branch in by.items():
                raw=tensor_loader(Path(branch['artifact']['path']),weights_only=True,map_location='cpu')
                assert tree_digest(raw)==branch['artifact']['tensor_sha256']
                assert len(raw['guided'])==len(branch['actions'])==37-n
                assert branch['actions'][0]=='CC' and branch['readout_actions'][0]=='C'
                first=branch['source_policy_tail'][0]
                assert first['true_D_before']==first['true_D_after']==point['chosen']['true_D_anchor']
                assert all(not h['source_policy']['decision']['reason'].startswith('MATH_EVENT_SUFFIX_FIRST:') for h in branch['source_policy_tail'][1:])
                assert all(h['source_policy']['decision']['reason']!='MATH_EVENT_TEACHER_FIRST_OFFLINE:D' for h in branch['source_policy_tail'])
                if label=='C_REPLAY':
                    assert all(torch.equal(a,b) for a,b in zip(raw['guided'],C_raw['guided']))
                    assert torch.equal(raw['final_latent'],C_raw['final_latent'])
                    assert branch['actions']==original_C['actions']
                    assert Path(branch['artifact']['video_path']).read_bytes()==Path(original_C['artifact']['video_path']).read_bytes()
                else:
                    assert torch.equal(raw['guided'][0],guided_teacher)
                    assert branch['first_returned_velocity_sha256']==tree_digest(teacher['teacher_velocity'])
                assert tree_digest(raw['first_C_velocity'])==branch['first_C_velocity_sha256']
            assert by['C_REPLAY']['first_C_cache_state_sha256']==by['TEACHER_FIRST']['first_C_cache_state_sha256']
            assert by['C_REPLAY']['first_C_velocity_sha256']==by['TEACHER_FIRST']['first_C_velocity_sha256']
            results.append({'scene':sample.name,'point':point,'event':event,
                'ordinary_and_old_and_new_parent_complete_equal':True,
                'new_C_and_original_C_full_suffix_equal':True,
                'teacher_first_guided_raw_exact':True,'teacher_not_committed':True,
                'one_teacher_pair_and_one_velocity_injection':True,
                'actual_diagnostic_pairs':owner.actual_pair_computations})
        initial.restore()
        assert initial.fingerprint()==fingerprint and net.forward==net0 and inference.pipe.worldcache_enabled==pipe0
        return [{'flow':flow,'status':'PASS','checks':results,'complete_CPU_parents':12,
            'endpoint_suffixes':16,'four_cells':True,'ordinary_initial_state_restored':True}]
    finally:
        initial.restore(); net.forward=net0; inference.pipe.worldcache_enabled=pipe0


def run(runtime,tensor_loader,artifact_root):
    original=load('check_partial_mlp_guided_sampling_cpu_r1')
    source=dedent(inspect.getsource(original.exercise))
    start=source.index('    results=[]\n    try:'); end=source.index('\n    finally:\n',start)+1
    ns={**vars(original),'_body':body}
    replacement='    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root,tensor_loader)\n'
    exec(compile(source[:start]+replacement+source[end:],__file__+'#declared-Toy-setup','exec'),ns)
    result=load('check_full_sampling').run(runtime,exercise=lambda **kwargs:ns['exercise'](
        runtime=Path(runtime),tensor_loader=tensor_loader,artifact_root=artifact_root,**kwargs))
    assert {c['flow'] for c in result['checks']}=={False,True}
    result.update(status='TEACHER_FIRST_TWO_FLOW_FULL24_PARENTS32_ENDPOINT_SUFFIXES_CPU_PASS_NOT_GPU',
        actual_CPU_parents=24,endpoint_suffixes=32,events=8,teacher_pairs=8,
        actual_GPU_or_real_video_claim=False)
    return result
