"""Project accepted S metadata to the frozen real geometry without tensors.

This computes a prospective logical guard for every inventoried CPU boundary.
It does not measure physical RAM/VRAM, time transfers, or admit a GPU card.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re

from audit_cara_sq_s_resources_cpu_r1 import accept,require

ROOT=Path(__file__).resolve().parents[1]
BASE='reports/cara_sq_two_card_cpu_terminal_20261028.json'
SCOPE='plans/cara_next_stage_20261028/sq/S_RESOURCES_CPU_R5.json'
FEATURE_FIELDS='residual_cache|probe_residual_cache|residual_window|probe_residual_window|previous_internal_states|previous_input'


def projected_bytes(group,row,geometry,feature_width):
    path=row['path'];latent=geometry['latent_bytes']
    if group=='native':
        if re.fullmatch(r'root/('+FEATURE_FIELDS+r')/[01](?:/[012])?',path):
            return geometry['feature_elements']*feature_width
        if re.fullmatch(r'root/previous_output/[01]',path):return latent
        if path in ('root/affline_emb','root/affline_scale_log_info/t_embedding_B_T_D'):
            return geometry['embedding_bytes']
        if path=='root/crossattn_emb':return geometry['projected_cross_attention_bytes_upper_bound']
        if re.fullmatch(r'root/accumulated_rel_l1_distance/[01]',path):return 8
    elif group=='solver':
        if path in ('root/last_sample','root/model_outputs/0','root/model_outputs/1'):return latent
        if path=='root/sigmas':return 37*4
        if path=='root/timesteps':return 36*8
        if re.fullmatch(r'root/timestep_list/[01]',path):return 8
    elif group=='calibrators':
        if re.fullmatch(r'root/[01]/anchors/[01]/(probe|residual)',path):
            return geometry['feature_elements']*feature_width
    elif group=='paired_inputs':
        if path in ('root/0','root/1'):return latent
        if path=='root/2':return 8
    raise ValueError('Unregistered projection tensor: '+group+' '+path)


def project_schema(schema,geometry,feature_width):
    groups={}
    for name,report in schema['group_inventories'].items():
        if name=='conditions':
            # The declared tiny condition omits padding_mask. Include both
            # complete conditions from the accepted real B1 geometry instead.
            require({r['path'].split('/',1)[1] for r in report['tensors']}=={
                str(b)+'/'+field for b in (0,1) for field in (
                    'crossattn_emb','fps','use_video_condition','gt_frames',
                    'condition_video_input_mask_B_C_T_H_W')},'Tiny condition schema changed')
            groups[name]=geometry['two_real_conditions_bytes']
        elif name=='buffers':
            require(not report['tensors'],'Declared tiny fixture buffers changed')
            groups[name]=geometry['full2B_buffer_bytes_upper_bound']
        else:
            groups[name]=sum(projected_bytes(name,row,geometry,feature_width) for row in report['tensors'])
    require(set(groups)=={'native','solver','buffers','owner_history','readout_history',
        'calibrators','paired_inputs','conditions'},'Full eight-group projection required')
    return dict(group_logical_bytes=groups,logical_tensor_bytes=sum(groups.values()),
        logical_copy_guard_bytes=8*sum(groups.values()))


def main():
    p=argparse.ArgumentParser();p.add_argument('--two-accepted',type=Path,required=True)
    p.add_argument('--four-accepted',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();require(not args.output.exists(),'Retain original resource projection')
    evidence={};captures={};proofs={}
    def read(path):
        path=Path(path);raw=path.read_bytes();evidence[str(path)]=hashlib.sha256(raw).hexdigest()
        return json.loads(raw)
    scope=read(SCOPE)
    for host,path in (('two_card',args.two_accepted),('four_card',args.four_accepted)):
        proof=read(path);capture=read(proof['capture_ref'])
        require(proof['passed'] and proof['capture_sha256']==evidence[proof['capture_ref']],
            'Accepted original metadata capture bytes changed')
        accept(capture,scope,proof['source_revision'],host)
        captures[host]=capture['result'];proofs[host]=proof
    two,four=captures['two_card'],captures['four_card']
    require(proofs['two_card']['source_revision']==proofs['four_card']['source_revision']
        and two['schemas']==four['schemas'] and two['before_pair_boundaries']==four['before_pair_boundaries']
        and two['full2B_meta_architecture']==four['full2B_meta_architecture'],
        'Both registered hosts must share the exact original metadata inventory')
    old_capture=read(BASE)
    require(evidence[BASE]=='d3fb3c2cd64998724d218c683de12f1376206741d63cf28528be35978d2884de'
        and old_capture['container_state']['Status']=='exited'
        and old_capture['container_state']['ExitCode']==0,'Original accepted B1 schema receipt changed')
    old=old_capture['result']['saved_state_schema'];meta=two['full2B_meta_architecture']
    feature=old['current'][0]['original'];latent=old['pair_inputs']['latent']
    require(feature['shape']==[1,24,27,48,2048] and feature['dtype']=='torch.bfloat16'
        and feature['bytes']==math.prod(feature['shape'])*2
        and latent['shape']==[1,16,24,54,96] and latent['dtype']=='torch.float32',
        'Frozen original B1 feature/latent geometry changed')
    parameters={r['path']:r for r in meta['parameters']['tensors']}
    require(parameters['root/crossattn_proj.0.weight']['shape']==[1024,100352],
        'Original full2B cross-attention projection changed')
    conditions=old['pair_inputs']['conditions']
    require(len(conditions)==2 and all(c['fields']['crossattn_emb']['shape']==[1,512,100352]
        for c in conditions),'Both original real conditions required')
    geometry=dict(feature_shape=feature['shape'],feature_elements=math.prod(feature['shape']),
        original_feature_dtype=feature['dtype'],latent_shape=latent['shape'],latent_bytes=latent['bytes'],
        embedding_bytes=old['current'][0]['embedding']['bytes'],
        projected_cross_attention_bytes_upper_bound=1*512*1024*4,
        two_real_conditions_bytes=sum(v['bytes'] for c in conditions for v in c['fields'].values()
            if isinstance(v,dict) and 'bytes' in v),
        full2B_buffer_bytes_upper_bound=sum(math.prod(r['shape'])*(8 if r['dtype']=='torch.int64' else 4)
            for r in meta['buffer_schema']))
    projections={}
    for label,width in (('original_BF16_features',2),('conservative_FP32_features',4)):
        rows={key:project_schema(schema,geometry,width) for key,schema in two['schemas'].items()}
        maximum=max(v['logical_copy_guard_bytes'] for v in rows.values())
        projections[label]=dict(feature_element_bytes=width,schemas=rows,
            max_logical_copy_guard_bytes=maximum,max_logical_copy_guard_GiB=maximum/2**30,
            max_by_group_logical_bytes={g:max(row['group_logical_bytes'][g] for row in rows.values())
                for g in next(iter(rows.values()))['group_logical_bytes']})
    result=dict(status='S_COMPLETE_EIGHT_GROUP_LOGICAL_GEOMETRY_PROJECTION_NOT_PHYSICAL_PEAK_OR_GPU_QUOTE',
        evidence_sha256=evidence,source_revision=proofs['two_card']['source_revision'],
        accepted_host_inventories_equal=True,complete_boundaries_per_host=108,unique_schemas=33,
        geometry=geometry,full2B_parameter_logical_bytes=meta['parameters']['logical_tensor_bytes'],
        full2B_buffers=meta['buffer_schema'],projections=projections,
        assumptions=['The exact frozen 2B/resolution/conditioning and native field families are retained',
            'The output/solver latent is bounded by FP32; timestep/log and projected context use conservative widths',
            'Real full2B buffers keep the observed shapes, with floating buffers allowed FP32',
            'The eight-group logical counter covers references; full backing storage and transient allocations remain separate'],
        proposed_logical_guard_GiB=64,proposed_guard_frozen_in_GPU_profile=False,
        remaining=['Before any actual snapshots, inspect all actual tensor schemas and full backing storage; refuse unknown fields or cap excess',
            'Bind lifecycle, physical device/host limits, complete hashing/copy/I-O costs and both whole-card quotes',
            'Obtain separate S GPU authority and fresh admission before any real collection'],
        physical_GPU_or_RAM_peak_measured=False,whole_S_quote_frozen=False,complete_S_GPU_entry_accepted=False,
        S_real_labels=0,GPU_submissions=0,new_GPUh=0,ledger_writes=0)
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(dict(status=result['status'],max_guard_GiB={k:v['max_logical_copy_guard_GiB']
        for k,v in projections.items()},buffer_bytes_upper_bound=geometry['full2B_buffer_bytes_upper_bound'])))


if __name__=='__main__':main()
