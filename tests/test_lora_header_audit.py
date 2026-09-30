"""Structural compatibility cannot silently ignore bad targets/LoRA variants."""
import copy
import json
from pathlib import Path
import pytest
from wcomr.lora_header_audit import audit_adapter,validate_tensor_table


def inputs():
    h={'base_model.model.layer.lora_A.weight':{'dtype':'F32','shape':[2,3],'data_offsets':[0,24]},
       'base_model.model.layer.lora_B.weight':{'dtype':'F32','shape':[4,2],'data_offsets':[24,56]}}
    c={'peft_type':'LORA','bias':'none','r':2,'lora_alpha':4,'target_modules':['layer'],'fan_in_fan_out':False}
    b={'layer.weight':{'shape':[4,3],'dtype':'BF16'}}
    return h,c,b


def test_rank_alpha_mapping_and_byte_topology_are_checked_not_assumed():
    h,c,b=inputs();r=audit_adapter(h,100,164,c,b,.5)
    assert r['paired_target_count']==1 and r['targets'][0]['effective_delta_scale']==1
    assert r['alpha_over_rank']==2 and r['status'].startswith('HEADER_STRUCTURE')


@pytest.mark.parametrize('bad',['missing_base','shape','rank','target_set','missing_b','unknown_key','offset','payload','rslora','dora','alpha_pattern','nonfinite_alpha'])
def test_incompatible_or_unsupported_structure_is_not_ready(bad):
    h,c,b=inputs();size=164
    if bad=='missing_base':b={}
    elif bad=='shape':b['layer.weight']['shape']=[3,4]
    elif bad=='rank':c['r']=3
    elif bad=='target_set':c['target_modules']=['other']
    elif bad=='missing_b':h.pop('base_model.model.layer.lora_B.weight');size=132
    elif bad=='unknown_key':h={'other':next(iter(h.values()))};size=132
    elif bad=='offset':h['base_model.model.layer.lora_B.weight']['data_offsets']=[20,52]
    elif bad=='payload':size+=1
    elif bad=='rslora':c['use_rslora']=True
    elif bad=='dora':c['use_dora']=True
    elif bad=='alpha_pattern':c['alpha_pattern']={'layer':1}
    elif bad=='nonfinite_alpha':c['lora_alpha']=float('nan')
    with pytest.raises(ValueError):audit_adapter(h,100,size,c,b,.5)


def test_real_pinned_header_inputs_all_targets_and_index_cover_original_base():
    root=Path(__file__).resolve().parents[1];p=json.loads((root/'manifests/l0_lora_header_audit_20261001.json').read_text());base={}
    index=json.loads((root/p['base_index']['path']).read_text())['weight_map']
    for row in p['base_headers']:
        entries=validate_tensor_table(json.loads((root/row['path']).read_text()),row['file_bytes']-8-row['header_bytes'])
        assert not set(base)&set(entries)
        assert all(index[k]==row['filename'] for k in entries);base.update(entries)
    assert len(base)==825 and set(base)==set(index)
    for row in p['adapters']:
        h=json.loads((root/row['header_path']).read_text());c=json.loads((root/row['config_path']).read_text())
        r=audit_adapter(h,row['header_bytes'],row['file_bytes'],c,base,row['requested_weight'])
        assert r['tensor_count']==600 and r['paired_target_count']==300 and r['alpha_over_rank']==1
