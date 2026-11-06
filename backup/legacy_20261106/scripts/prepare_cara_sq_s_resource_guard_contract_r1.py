"""Bind small S resource contracts to the accepted dual-host metadata receipts."""
import copy
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def main():
    import sys
    sys.path.insert(0,str(ROOT/'src'))
    from wcomr.sq_s_batch_r1 import digest,require
    def read(name):return json.loads((ROOT/name).read_text())
    def sha(name):return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    accepted='reports/cara_sq_s_resources_dual_cpu_accepted_r5_20261029.json'
    proof=read(accepted);ref=proof['accepted']['two_card']['capture_ref']
    require(sha(ref)==proof['accepted']['two_card']['capture_sha256'],'Original accepted inventory changed')
    result=read(ref)['result'];schemas=result['schemas'];meta=result['full2B_meta_architecture']
    source='reports/cara_sq_two_card_cpu_terminal_20261028.json'
    old=read(source)['result']['saved_state_schema']
    require(sha(source)=='d3fb3c2cd64998724d218c683de12f1376206741d63cf28528be35978d2884de',
        'Original real B1 geometry changed')
    registry={g:{} for g in next(iter(schemas.values()))['group_inventories']}
    for s in schemas.values():
        for group,rows in s['group_inventories'].items():
            for row in rows['tensors']:
                entry=registry[group].setdefault(row['path'],dict(shape=row['shape'],dtypes=[]))
                require(entry['shape']==row['shape'],'Unregistered variable-shape tiny tensor')
                if row['dtype'] not in entry['dtypes']:entry['dtypes'].append(row['dtype'])
    first=next(iter(schemas.values()))
    base=dict(schema='SQ_S_BEFORE_SNAPSHOT_RESOURCE_CONTRACT_R1',
        evidence_sha256={accepted:sha(accepted),source:sha(source),
            'reports/cara_sq_s_complete_resource_geometry_r1_20261029.json':sha('reports/cara_sq_s_complete_resource_geometry_r1_20261029.json')},
        native_field_names=first['native_field_names'],solver_field_names=first['solver_field_names'],
        source_identity_ref='plans/cara_next_stage_20261028/sq/S_EXECUTION_IDENTITY_R1.json',
        source_identity_sha256=sha('plans/cara_next_stage_20261028/sq/S_EXECUTION_IDENTITY_R1.json'),
        GPU_authority=False,physical_peak_established=False,whole_S_quote_frozen=False)
    tiny=dict(copy.deepcopy(base),CPU_fixture_only=True,tensor_schema=copy.deepcopy(registry),buffer_names=[],
        limits=dict(logical_copy_guard_bytes=128*2**20,backing_copy_guard_bytes=128*2**20,
            mutable_buffer_bytes=0,numpy_backing_bytes=0,live_backing_storage_bytes_by_device_kind={'cpu':16*2**20}))
    full=copy.deepcopy(registry)
    floating=['torch.bfloat16','torch.float32']
    for path,entry in full['native'].items():
        if re.match(r'root/(residual_cache|probe_residual_cache|residual_window|probe_residual_window|previous_internal_states|previous_input)/',path):
            entry.update(shape=old['current'][0]['original']['shape'],dtypes=floating)
        elif path.startswith('root/previous_output/'):
            entry.update(shape=old['pair_inputs']['latent']['shape'],dtypes=floating)
        elif path in ('root/affline_emb','root/affline_scale_log_info/t_embedding_B_T_D'):
            entry.update(shape=old['current'][0]['embedding']['shape'],dtypes=['torch.float32'])
        elif path=='root/crossattn_emb':entry.update(shape=[1,512,1024],dtypes=floating)
        elif path.startswith('root/accumulated_rel_l1_distance/'):entry.update(shape=[],dtypes=floating)
        else:raise ValueError('Unknown native family: '+path)
    for path,entry in full['solver'].items():
        if path.startswith('root/model_outputs/') or path=='root/last_sample':
            entry.update(shape=[1]+old['pair_inputs']['latent']['shape'],dtypes=['torch.float32'])
    for entry in full['calibrators'].values():entry.update(shape=old['current'][0]['original']['shape'],dtypes=floating)
    for i,key in enumerate(('noise','latent','timestep')):
        full['paired_inputs']['root/'+str(i)]=dict(shape=old['pair_inputs'][key]['shape'],dtypes=[old['pair_inputs'][key]['dtype']])
    full['conditions']={}
    for b,condition in enumerate(old['pair_inputs']['conditions']):
        for key,value in condition['fields'].items():
            if isinstance(value,dict) and 'shape' in value:
                full['conditions']['root/'+str(b)+'/'+key]=dict(shape=value['shape'],dtypes=[value['dtype']])
    full['buffers']={}
    for i,row in enumerate(meta['buffer_schema']):
        full['buffers']['root/'+str(i)]=dict(shape=row['shape'],dtypes=[row['dtype']] if row['dtype']=='torch.int64' else floating)
    real=dict(copy.deepcopy(base),CPU_fixture_only=False,tensor_schema=full,
        buffer_names=[r['name'] for r in meta['buffer_schema']],
        limits=dict(logical_copy_guard_bytes=64*2**30,backing_copy_guard_bytes=64*2**30,
            mutable_buffer_bytes=712,numpy_backing_bytes=0,
            live_backing_storage_bytes_by_device_kind={'cpu':2*2**30,'cuda':8*2**30}))
    for name,value in [('S_RESOURCE_GUARD_CPU_CONTRACT_R1.json',tiny),('S_RESOURCE_GUARD_REAL_CONTRACT_R1.json',real)]:
        value['contract_sha256']=digest(value)
        path=ROOT/'plans/cara_next_stage_20261028/sq'/name
        with path.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    path=ROOT/'tests/fixtures/sq_s_resource_guard_tiny_metadata_r1.json';path.parent.mkdir(exist_ok=True)
    fixture=max(schemas.values(),key=lambda s:s['logical_tensor_bytes'])
    with path.open('x') as f:json.dump(fixture,f,indent=2,allow_nan=False);f.write('\n')
    print('CPU-only and prospective real contracts bound; no GPU admission or quote')


if __name__=='__main__':main()
