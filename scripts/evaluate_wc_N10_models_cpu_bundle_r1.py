#!/usr/bin/env python3
"""Run all five CPU model probes once; retain every failed role and original file."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parent))
from evaluate_wc_N10_metric_model_cpu_r1 import ROLES,WEIGHTS,MUSIQ_SOURCE_SHA,sha

CLASSES=dict(DINO='vision_transformer.VisionTransformer',AMT_S='networks.AMT-S.Model',
    RAFT_THINGS='vbench.third_party.RAFT.core.raft.RAFT',ViCLIP='vbench.third_party.ViCLIP.viclip.ViCLIP',
    MUSIQ_SPAQ='pyiqa.archs.musiq_arch.MUSIQ')
INPUTS=dict(DINO=[2,3,224,224],AMT_S=[1,3,432,768],RAFT_THINGS=[1,3,432,768],
            ViCLIP=[1,8,3,224,224],MUSIQ_SPAQ=[1,3,288,512])
OUTPUTS=dict(DINO={'features':[2,768]},AMT_S={'interpolated_frame':[1,3,432,768]},
    RAFT_THINGS={'coarse_flow':[1,2,54,96],'full_flow':[1,2,432,768]},
    ViCLIP={'video_features':[1,768],'text_features':[1,768]},MUSIQ_SPAQ={'synthetic_scalar_output':None})
PASS='N10_ALL_FIVE_REAL_MODEL_CPU_PROBES_ACCEPTED_NOT_VIDEO_SCORES'


def accept_role(role,value,registration,registration_sha256,resources):
    if set(resources)!=set(ROLES) or any((r['bytes'],r['sha256'])!=WEIGHTS[name] for name,r in resources.items()):
        raise ValueError('Keep all five original resource identities')
    if (value['status']!='N10_METRIC_MODEL_REAL_CPU_SYNTHETIC_INPUT_PASS_NOT_VIDEO_SCORE'
            or value['exit_code']!=0 or value['role']!=role or value['source_revision']!=registration['source_revision']
            or value['registration_sha256']!=registration_sha256
            or value['complete_registered_model_roles']!=list(ROLES)
            or value['resource_sha256']!=WEIGHTS[role][1]
            or value['resource_path']!=resources[role]['path']
            or value['checkpoint_SHA_verified_before_import'] is not True
            or value['CUDA_initialized'] or value['forbidden_events']
            or value['synthetic_inputs_only'] is not True
            or value['paper_quality_scores_generated'] or value['final_videos_read']
            or value['GPU_submissions'] or value['server_ledger_written']):
        raise ValueError('Actual original CPU model/source/resource scope is not accepted: '+role)
    loads=value['real_checkpoint_loads'];states=value['actual_state_dict_loads']
    if (not loads or any(r['path']!=resources[role]['path'] or r['map_location']!='cpu' for r in loads)
            or not states or any(r['missing_keys'] or r['unexpected_keys'] or r['state_keys']<=0 for r in states)):
        raise ValueError('Actual declared checkpoint and complete compatible state must be loaded: '+role)
    actual=value['actual']
    constructor_ref='src/wcomr/automatic_quality_models_r1.py'
    if (constructor_ref in registration['payload_sha256']
            and actual.get('constructor_source_sha256')!=registration['payload_sha256'][constructor_ref]):
        raise ValueError('Actual model CPU must use the same frozen original constructor: '+role)
    if (actual['role']!=role or actual['model_class']!=CLASSES[role]
            or type(actual['parameter_count']) is not int or actual['parameter_count']<=0
            or actual['model_eval'] is not True or actual['all_parameters_CPU_FP32'] is not True
            or actual['actual_model_input_shape']!=INPUTS[role] or set(actual['outputs'])!=set(OUTPUTS[role])):
        raise ValueError('Actual model class, input geometry or eval precision differs: '+role)
    for name,tensor in actual['outputs'].items():
        expected=OUTPUTS[role][name]
        if (tensor['device']!='cpu' or tensor['dtype']!='torch.float32' or tensor['finite'] is not True
                or tensor['requires_grad'] or not re.fullmatch('[0-9a-f]{64}',tensor['sha256'])
                or (expected is not None and tensor['shape']!=expected)
                or (expected is None and math.prod(tensor['shape'])!=1)):
            raise ValueError('Actual finite CPU output interface differs: '+role+'/'+name)
    root=Path(registration['stage'])
    source=Path(actual['model_source'])
    if role=='MUSIQ_SPAQ':
        if actual['model_source_sha256']!=MUSIQ_SOURCE_SHA or value['dependency_versions']['pyiqa']!='0.1.10':
            raise ValueError('Original MUSIQ implementation changed')
    else:
        try:relative=str(source.relative_to(root))
        except ValueError:raise ValueError('Unregistered actual model source: '+str(source))
        if registration['payload_sha256'].get(relative)!=actual['model_source_sha256']:
            raise ValueError('Actual model implementation does not match the frozen payload')
    imported=value['imported_pinned_modules']
    if not imported:raise ValueError('Pinned VBench must really be imported')
    for row in imported:
        try:relative=str(Path(row['path']).relative_to(root))
        except ValueError:raise ValueError('Installed VBench silently mixed with pinned sources')
        if not relative.startswith('upstream/vbench/') or registration['payload_sha256'].get(relative)!=row['sha256']:
            raise ValueError('Imported VBench implementation changed')
    if role=='RAFT_THINGS' and actual['flow_iterations']!=20:raise ValueError('Keep original RAFT20 CPU probe')
    if role=='AMT_S' and (actual['interpolation_iterations']!=1 or actual['scale_factor']!=1.):
        raise ValueError('Keep original one-iteration AMT CPU probe')
    if role=='ViCLIP' and (actual['text_context_length']!=32 or actual['real_tokenizer_vocab_size']!=49408):
        raise ValueError('Original ViCLIP tokenizer/text interface differs')
    return dict(role=role,status='REAL_MODEL_CPU_ROLE_ACCEPTED_NOT_QUALITY',
        parameter_count=actual['parameter_count'],wall_seconds=value['wall_seconds'],
        constructor_source_sha256=actual.get('constructor_source_sha256'))


def drive(registration,registration_sha256,resources,callback):
    """Never drop or replace a failed role; every original role is attempted."""
    if registration['roles']!=list(ROLES):raise ValueError('Complete five-role CPU matrix required')
    rows=[]
    for role in ROLES:
        row=dict(role=role,status='CPU_ROLE_NOT_ACCEPTED',exit_code=None)
        try:
            original=callback(role);row.update(original)
            if row['exit_code']!=0:raise ValueError('Original role process did not exit0')
            row['acceptance']=accept_role(role,row['data'],registration,registration_sha256,resources)
            row['status']='CPU_ROLE_ACCEPTED'
        except Exception as error:
            row.update(error_type=type(error).__name__,error=str(error))
        rows.append(row)
    accepted=all(r['status']=='CPU_ROLE_ACCEPTED' for r in rows)
    return dict(status=PASS if accepted else 'N10_CPU_MODEL_FAILURES_RETAINED_ALL_FIVE_DENOMINATOR',
        source_revision=registration['source_revision'],registration_sha256=registration_sha256,
        registered_roles=list(ROLES),role_denominator=5,attempted_role_slots=5,
        accepted_roles=sum(r['status']=='CPU_ROLE_ACCEPTED' for r in rows),rows=rows,
        exit_code=0 if accepted else 1,paper_quality_scores_generated=False,final_videos_read=False,
        GPU_submissions=0,server_ledger_written=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',type=Path,required=True)
    args=parser.parse_args();stage=args.stage.resolve();destination=stage/'CPU-model-bundle-result.json'
    assert not destination.exists();sys.dont_write_bytecode=True
    registration=json.loads((stage/'registration.json').read_text());manifest=json.loads((stage/'model-resources.json').read_text())
    assert registration['purpose']=='N10_FULL_FIVE_METRIC_MODEL_CPU_ONLY_NOT_SCORING'
    assert all(sha(stage/name)==digest for name,digest in registration['payload_sha256'].items())
    assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
    started=time.time()
    def run(role):
        target=stage/('CPU-model-'+role+'.json');assert not target.exists()
        command=[sys.executable,str(stage/'scripts/evaluate_wc_N10_metric_model_cpu_r1.py'),
                 '--stage',str(stage),'--role',role]
        env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',
                 OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        with (stage/('CPU-model-'+role+'.log')).open('xb') as log:
            child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=env)
            code=child.wait()
        row=dict(command=command,original_child_pid=child.pid,exit_code=code,
                 result_ref=target.name,result_sha256=sha(target) if target.is_file() else None)
        if target.is_file():row['data']=json.loads(target.read_text())
        return row
    result=drive(registration,sha(stage/'registration.json'),manifest['resources'],run)
    result.update(wall_seconds=time.time()-started,interpreter=sys.executable)
    with destination.open('x') as handle:json.dump(result,handle,indent=2,allow_nan=False)
    raise SystemExit(result['exit_code'])


if __name__=='__main__':main()
