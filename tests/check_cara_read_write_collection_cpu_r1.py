"""Exercise the full14 request collector with explicit tiny CPU model boundaries."""
import inspect
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from textwrap import dedent
from typing import ClassVar, Optional

import torch

from wcomr.cara_read_write_collection_r1 import Requests, collect
from wcomr.cara_read_write_plan_r1 import build
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.wc_time_collection_r1 import atomic

from check_cara_read_write_suffix_cpu_r1 import ROOT, load, pinned_modules
import check_cara_read_write_point_cpu_r1 as point


@dataclass(frozen=True)
class TinyArguments:
    """Declared local immutable fixture; target Linux uses actual Cosmos class."""
    name: str
    prompt: str
    num_steps: int = 35
    seed: int = 0
    guidance: int = 7
    num_output_frames: int = 93
    num_input_frames: int = 0
    input_path: Optional[str] = None
    negative_prompt: str = 'negative'
    resolution: str = '16,16'
    enable_autoregressive: bool = False
    model_config: ClassVar[dict] = {'frozen': True}

    def __post_init__(self):
        if type(self.seed) is not int or type(self.num_steps) is not int or self.num_steps <= 0:
            raise ValueError('Explicit valid seed/update count required')

    def model_dump(self, **kwargs):
        return asdict(self)

    def model_dump_json(self):
        return json.dumps(asdict(self))

    @classmethod
    def model_validate(cls, values):
        return cls(**values)


@torch.no_grad()
def collect_body(inference, selected, wc, rf, settings, inference_module, runtime, config, flow, artifact_root,
                 *, actual_arguments=False):
    model, net = inference.pipe.model, inference.pipe.model.net
    parent = json.loads((ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_text())
    card = build(parent)
    if actual_arguments:
        from cosmos_predict2.config import InferenceArguments
        samples = {row['name']: InferenceArguments.model_validate({**{k:v for k,v in row.items() if k!='partition'},
                   'resolution':'16,16'}) for row in card['inputs']}
    else:
        samples = {name: TinyArguments(name=name, prompt=name) for name in card['FIT']}
    # The generated ordinary-source setup above supplies small8-channel input,
    # real Block bodies and source-exact conditions, not real Cosmos weights.
    initial = CompleteStateRoundtrip(net, model.sample_scheduler, torch.zeros(1))
    original = initial.fingerprint()
    def native(self, *args, **kwargs):
        threshold = self.worldcache_rel_l1_thresh
        self.worldcache_rel_l1_thresh = -1.
        try:
            return wc.worldcache_mini_train_dit_forward(self, *args, **kwargs)
        finally:
            self.worldcache_rel_l1_thresh = threshold
    common = dict(runtime=runtime, wc=wc, rf=rf, inference_module=inference_module,
                  expected_shape=[1,8,2,8,8], CPU_native=native)
    context = dict(scope_sha256=card['scope_sha256'], host='two_card', CPU_fixture_only=True,
                   launch_id='EXPLICIT_TINY_CPU_ONLY', source_revision='CPU_SOURCE_ONLY', admission_sha256='CPU_NO_GPU')
    adapter = Requests(inference=inference, samples=samples, card=card, common=common,
        context=context, cpu_validation=True, logical_copy_cap_bytes=1 << 30, CPU_storage_cap_bytes=1 << 30)
    output = Path(artifact_root)/('collection_flow_'+str(flow))
    output.mkdir(parents=True, exist_ok=False)
    state_file = output/'collection.json'
    try:
        state = collect(adapter, output/'requests', before_request=lambda slot: initial.restore(),
                        save=lambda value: atomic(state_file, value))
        assert len(state['rows']) == 14 and state['physical_model_pairs'] == 512
        assert state['scientific_score_pairs'] == 8 and not state['scientific_accepted']
        for member in card['FIT']:
            rows = {r['slot']['role']:r for r in state['rows'] if r['slot']['member']==member}
            assert set(rows) == set(card['roles'])
            # Real encoded-video identity is accepted after release. These
            # fixture writers are deterministic JSON and labelled accordingly.
            assert rows['RW00']['result']['video_artifact']['sha256'] == rows['UNIFORM19_C']['result']['video_artifact']['sha256']
            assert rows['RW11']['result']['video_artifact']['sha256'] == rows['D8_CONTROL']['result']['video_artifact']['sha256']
        try:
            adapter(card['physical_matrix'][0], output/'duplicate')
        except ValueError:
            pass
        else:
            raise AssertionError('A repeated request was accepted')
        initial.restore()
        assert initial.fingerprint() == original
        return [dict(status='FULL14_READ_WRITE_COLLECTION_TINY_CPU_PASS', flow=flow,
            complete_paths=14, scientific_outputs=8, logical_updates=504, physical_model_pairs=512,
            physical_CFG_calls=1024, ordinary_guarded_Native_C_D8_and_all_four_corners=True,
            actual_Cosmos_argument_class=actual_arguments,
            effective_flow_enabled=card['settings']['worldcache_flow_enabled'],
            caller_reset_and_duplicate_refusal=True, complete_artifacts_and_metadata=True,
            actual_Cosmos_weights=False, real_encoded_video=False, scientific_scores_read=False)]
    finally:
        initial.restore()


def run(runtime, artifact_root, *, actual_modules=False):
    # Reuse just the accepted point fixture's8-channel setup, then replace its
    # exercise with the complete registered two-member matrix.
    template = dedent(inspect.getsource(point.body.__wrapped__))
    start = template.index('    initial = CompleteStateRoundtrip(')
    template = template[:start]+'    return _collect_body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'
    def configured_body(*args):
        return collect_body(*args, actual_arguments=actual_modules)
    namespace = {**vars(point), '_collect_body':configured_body}
    exec(compile(template, __file__+'#point-tiny-model-setup', 'exec'), namespace)
    old = load('check_partial_mlp_guided_sampling_cpu_r1')
    source = dedent(inspect.getsource(old.exercise))
    if not actual_modules:
        imports = ('    from cosmos_predict2._src.predict2.inference import worldcache_utils as wc\n'
                   '    from cosmos_predict2._src.predict2.models import video2world_model_rectified_flow as rf\n')
        assert source.count(imports) == 1
        source = source.replace(imports, "    wc, rf = _pinned_modules(runtime, unused['wc'])\n")
    start = source.index('    results=[]\n    try:')
    end = source.index('\n    finally:\n', start)+1
    source = source[:start]+'    try:\n        return _body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root)\n'+source[end:]
    outer = {**vars(old), '_body':namespace['body'], '_pinned_modules':pinned_modules}
    exec(compile(source, __file__+'#existing-module-setup', 'exec'), outer)
    return load('check_full_sampling').run(runtime, exercise=lambda **kwargs: outer['exercise'](
        runtime=Path(runtime), tensor_loader=None, artifact_root=artifact_root, **kwargs))
