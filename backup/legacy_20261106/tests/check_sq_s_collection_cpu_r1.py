"""Complete108-row S topology on pinned CPU sampler and tiny stand-ins.

The two sample names identify CPU fixtures. Their moments and mock files are
never scientific labels, free-running real videos, or selected S schedules.
"""
from pathlib import Path
import sys

import torch

from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.policy_generator_r1.interval_grammar import Edge,compile_policy
from wcomr.sq_risk_r1 import TARGETS,coverage
from wcomr.sq_s_collection_r1 import RAW_STEPS,execute
from wcomr.sq_s_sources_r1 import PARENTS


def body(inference,selected,wc,rf,settings,inference_module,runtime,config,flow,artifact_root,storage_factory=None):
    import check_cara_pg_production_sampling_cpu_r1 as previous
    model=inference.pipe.model;net=model.net;scheduler=model.sample_scheduler
    model.config.state_ch=8
    class Head(torch.nn.Module):
        def forward(self,x,*args,**kwargs):return x+.01*x.square()
    net.final_layer=Head().eval()
    net.unpatchify=lambda x:x[:,:,::2,::2,:].movedim(-1,1).contiguous()
    cls,_=previous.load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,wc.DataType)
    def conditions(batch):
        return tuple(cls(crossattn_emb=torch.ones(1,3,4)*(1+b+.1*(batch['prompt']==selected[1].name)),
            fps=batch['fps'],use_video_condition=torch.tensor([True])).set_video_condition(
            torch.zeros(1,8,2,8,8),0,0,num_conditional_frames=0) for b in (0,1))
    model.conditioner.get_condition_with_negative_prompt=conditions
    model.get_data_and_condition=lambda batch:(None,torch.zeros(1,8,2,8,8),None)
    profile=previous.test_profile();initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1))
    root=Path(artifact_root)/('S_collection_flow_'+str(flow));rows=[];raw_rows=[];controls=[]
    storage=storage_factory(root/'streaming',[s.name for s in selected[:2]]) if storage_factory else None
    def sink(row,raw):
        assert row['parent_roundtrip_equal'] and not row['teacher_writes_parent']
        source=row['source']
        expected=tuple(t for t in PARENTS[row['parent']] if t<row['step'])[-2:]
        assert tuple(source['source_anchor_steps'])==expected
        assert source['source_captured_before_parent_pair'] and not source['current_D_in_source']
        assert all(t<row['step'] for t in expected)
        assert not row['P1_Dense_hidden_head_replay_accepted']
        assert bool(raw)==(row['parent']=='F19-C' and row['step'] in RAW_STEPS)
        if raw:
            assert raw['parent']=='F19-C' and raw['step'] in RAW_STEPS
            assert all(tuple(a['step'] for a in pair)==expected for pair in raw['anchors'])
            def cpu_data(value):
                if isinstance(value,torch.Tensor):assert value.device.type=='cpu'
                elif isinstance(value,dict):
                    for item in value.values():cpu_data(item)
                elif isinstance(value,(tuple,list)):
                    for item in value:cpu_data(item)
                else:assert value is None or type(value) in (str,int,float,bool)
            cpu_data(raw)
            assert raw['schema']=='SQ_S_F19_RAW_CPU_DATA_R2' and raw['P2_actual_C_reference_available']
            assert len(raw['reference_C'])==2 and all(t<row['step'] for t in expected)
            assert all(a['branch']==b and tuple(a['context'])==tuple(raw['context'])
                       and a['xi']==raw['noise_grid']['xi'][a['step']-1]
                       for b,pair in enumerate(raw['anchors']) for a in pair)
            raw_rows.append(dict(prompt=row['prompt'],parent=row['parent'],step=row['step'],
                                 past_steps=list(expected),CPU_data_only=True))
        if storage:storage(row,raw)
        rows.append(row)
    common=dict(runtime=runtime,wc=wc,rf=rf,settings=settings,calibration=None,specs={},
        inference_module=inference_module,expected_shape=[1,8,2,8,8],audit=True)
    try:
        for sample in selected[:2]:
            for parent,dense in PARENTS.items():
                bounds=dense+(37,);policy=compile_policy(profile,[Edge(a,b) for a,b in zip(bounds,bounds[1:])])
                values=[]
                for enabled in (False,True):
                    initial.restore()
                    result=execute(inference,sample,parent=parent,profile=profile,policy=policy,
                        enabled=enabled,sink=sink,logical_copy_cap_bytes=128*2**20,
                        output=root/(sample.name+'-'+parent+'-'+str(enabled)),**common)
                    assert result['status']=='COMPLETE' and result['guided_pairs']==result['solver_steps']==36
                    assert [r['actual'] for r in result['semantic_history']]==policy['actions']
                    assert len(result['S_rows'])==(len(TARGETS) if enabled else 0)
                    values.append(result)
                a,b=values
                assert len(a['guided'])==len(b['guided'])==36
                assert all(torch.equal(x,y) for x,y in zip(a['guided'],b['guided']))
                assert torch.equal(a['final_latent'],b['final_latent'])
                assert Path(a['video_path']).read_bytes()==Path(b['video_path']).read_bytes()
                controls.append(dict(prompt=sample.name,parent=parent,full36_OFF_ON_equal=True))
        covered=coverage(rows,[s.name for s in selected[:2]],tuple(PARENTS))
        assert covered['complete'] and covered['present']==108
        assert sum(r['extra_Dense_teacher_pairs'] for r in rows)==56
        assert sum(r['extra_C_readout_pairs'] for r in rows)==52
        assert sum(r['extra_Dense_hidden_replay_heads'] for r in rows)==0
        assert len(raw_rows)==8 and len({(r['prompt'],r['step']) for r in raw_rows})==8
        assert all(r['actual_D_teacher_reused']==(r['planned_parent_action']=='D') for r in rows)
        storage_receipt=storage.finish() if storage else None
        if storage:storage_receipt['reload_audit']=audit_storage(storage.root,rows)
        return [dict(flow=flow,status='PASS',complete_CPU_paths=8,CPU_fixture_moment_rows=108,
            extra_Dense_teacher_pairs=56,extra_C_readout_pairs=52,raw_CPU_states=raw_rows,
            OFF_ON_controls=controls,pre_D_sources_and_same_state_prefix_checked=True,
            Dense_hidden_replay_heads=0,actual_Cosmos_weights=False,real_generated_video=False,
            S_labels_collected=0,streaming_raw_storage_accepted=False,
            CPU_streaming_storage_accepted=bool(storage),storage=storage_receipt,
            real_model_S_collector_accepted=False)]
    finally:initial.restore()


def audit_storage(root,expected_rows):
    import hashlib,json
    root=Path(root);manifest=json.loads((root/'manifest.json').read_text())
    original={(r['prompt'],r['parent'],r['step']):r for r in expected_rows}
    refs=[r['artifact'] for r in manifest['rows']+manifest['raw_states']+manifest['anchors']]
    assert len(refs)==140 and not list(root.glob('*.partial'))
    for ref in refs:
        path=root/ref['name']
        assert path.stat().st_size==ref['bytes'] and hashlib.sha256(path.read_bytes()).hexdigest()==ref['sha256']
    for record in manifest['rows']:
        value=json.loads((root/record['artifact']['name']).read_text())
        expected=original[(record['prompt'],record['parent'],record['step'])]
        assert value['moments']==expected['moments'] and value['source']==expected['source']
    # Only this tiny, source-bound test accepts torch.load. No real checkpoint
    # or external path is read by the production storage writer.
    def load(ref):return _tiny_tensor_loader(root/ref['name'],map_location='cpu',weights_only=True)
    for record in manifest['raw_states']:
        value=load(record['artifact']);expected=original[(record['prompt'],record['parent'],record['step'])]
        assert value['noise_grid_sha256']==expected['noise_grid_sha256']
        assert value['xi']==expected['xi'] and value['sigma']==expected['sigma']
        assert value['P2_actual_C_reference_available'] and len(value['reference_C'])==len(value['teacher'])==2
        for branch,pair in enumerate(value['anchor_refs']):
            anchors=[load(ref) for ref in pair]
            assert [a['step'] for a in anchors]==expected['source']['source_anchor_steps']
            assert all(a['branch']==branch and tuple(a['context'])==tuple(value['context']) for a in anchors)
    return dict(files_SHA_and_bytes_reloaded=140,measured_rows_reloaded=108,raw_states_reloaded=8,
        unique_anchors_reloaded=24,actual_C_reference_and_noise_grid_retained=True,
        real_Cosmos_weights_loaded=False)


_tiny_tensor_loader=None


def run(runtime,artifact_root):
    runtime=Path(runtime)
    sys.path[:0]=[str(runtime),str(runtime/'packages/cosmos-oss'),str(runtime/'packages/cosmos-cuda')]
    import check_cara_pg_production_sampling_cpu_r1 as previous
    original=previous.body;previous.body=body
    try:return previous.run(runtime,artifact_root)
    finally:previous.body=original
