"""Validate LoRA target topology from safetensors headers, never tensor payloads."""
import math
import re

DTYPE_BYTES={'F64':8,'F32':4,'F16':2,'BF16':2}


def validate_tensor_table(header, payload_bytes):
    entries={k:v for k,v in header.items() if k!='__metadata__'}
    if not entries:raise ValueError('Empty tensor table')
    spans=[]
    for key,e in entries.items():
        shape=e['shape'];dtype=e['dtype'];start,end=e['data_offsets']
        if dtype not in DTYPE_BYTES or not shape or any(type(x) is not int or x<=0 for x in shape):
            raise ValueError('Unsupported dtype/shape: '+key)
        if type(start) is not int or type(end) is not int or start<0 or end-start!=math.prod(shape)*DTYPE_BYTES[dtype]:
            raise ValueError('Tensor byte count mismatch: '+key)
        spans.append((start,end))
    ordered=sorted(spans)
    if ordered[0][0]!=0 or any(x[1]!=y[0] for x,y in zip(ordered,ordered[1:])) or ordered[-1][1]!=payload_bytes:
        raise ValueError('Header tensor offsets do not cover declared payload exactly')
    return entries


def audit_adapter(header, header_bytes, file_bytes, config, base, requested_weight):
    entries=validate_tensor_table(header,file_bytes-8-header_bytes)
    if (config.get('peft_type')!='LORA' or config.get('bias')!='none' or config.get('fan_in_fan_out')
            or config.get('use_rslora') or config.get('use_dora') or config.get('modules_to_save')
            or config.get('rank_pattern') or config.get('alpha_pattern')):
        raise ValueError('Not the supported ordinary linear LoRA contract')
    rank=config['r'];alpha=config['lora_alpha']
    if type(rank) is not int or rank<=0 or not math.isfinite(alpha) or alpha<=0 or not math.isfinite(requested_weight):
        raise ValueError('Invalid rank/alpha/weight')
    pairs={}
    for key,e in entries.items():
        match=re.fullmatch(r'(.+)\.lora_([AB])(?:\.default)?\.weight',key)
        if not match:raise ValueError('Unsupported adapter tensor: '+key)
        module,side=match.groups();module=module.removeprefix('base_model.model.')
        pair=pairs.setdefault(module,{})
        if side in pair:raise ValueError('Duplicate A/B mapping: '+module)
        pair[side]=e
    if set(pairs)!=set(config['target_modules']) or len(set(config['target_modules']))!=len(config['target_modules']):
        raise ValueError('Adapter config/actual target set differs')
    rows=[]
    for module,pair in sorted(pairs.items()):
        if set(pair)!={'A','B'}:raise ValueError('Incomplete LoRA pair: '+module)
        a,b=pair['A'],pair['B'];name=module+'.weight'
        if name not in base:raise ValueError('Missing base target: '+name)
        target=base[name]
        if (len(a['shape'])!=2 or len(b['shape'])!=2 or a['shape'][0]!=rank or b['shape'][1]!=rank
                or target['shape']!=[b['shape'][0],a['shape'][1]] or target['dtype'] not in DTYPE_BYTES):
            raise ValueError('LoRA/base rank or shape mismatch: '+name)
        rows.append({'target':name,'base_shape':target['shape'],'base_dtype':target['dtype'],
                     'a_shape':a['shape'],'b_shape':b['shape'],'rank':rank,'alpha':alpha,
                     'requested_weight':requested_weight,'effective_delta_scale':requested_weight*alpha/rank})
    return {'status':'HEADER_STRUCTURE_COMPATIBLE_NOT_PAYLOAD_HASH_LOAD_OR_REAL_MERGE_VALIDATION',
            'tensor_count':len(entries),'paired_target_count':len(rows),'rank':rank,'alpha':alpha,'alpha_over_rank':alpha/rank,
            'targets':rows,'scope':'Public header metadata and locally hash-verified base headers only. Finite tensor values, payload digest, actual merge/load, model/task behavior and GPU calls remain untested.'}
