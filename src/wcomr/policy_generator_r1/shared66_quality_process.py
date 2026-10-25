"""Isolated original-model child under the post-release CPU envelope."""
import json,os,subprocess,sys
from pathlib import Path
from .continuation_preparation import require
from .production_evidence import sha
from ..gpu_budget_pool_v2 import atomic_json
ENTRY='scripts/score_cara_cal66_quality_cpu_r1.py'

def run_bound_child(binding,binding_path,plan,release,out,run=None):
    require(all(release[k] for k in ('GPU_released','ledger_settled','lock_free','CUDA_hidden')),'Release required before model child')
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Child must inherit hidden GPU')
    out=Path(out);stage=Path(binding['registration']['stage']);child=stage/ENTRY
    require(json.loads(Path(binding_path).read_text())==binding and plan['evaluator_identity']==binding['identity'],'Quality binding differs')
    require(binding['registration']['payload_sha256'][ENTRY]==sha(child),'Registered scorer source differs')
    overlay=Path(binding['dependency_overlay']);lock=overlay.parent/'dependency-overlay-manifest.json'
    require(overlay.is_absolute() and not overlay.is_symlink() and sha(lock)==binding['dependency_overlay_manifest_sha256'],'Overlay binding differs')
    manifest=json.loads(lock.read_text());require(manifest['base_environment_modified'] is False,'Base environment changed')
    for name,h in manifest['files'].items():
        relative=Path(name);f=overlay/relative
        require(not relative.is_absolute() and '..' not in relative.parts and not f.is_symlink() and sha(f)==h,'Overlay source changed')
    atomic_json(out/'quality-plan-input.json',plan);atomic_json(out/'quality-release-input.json',release)
    env=dict(os.environ,PYTHONPATH=str(stage/'scripts')+':'+str(stage/'src')+':'+str(overlay))
    command=[sys.executable,str(child),'--binding',str(binding_path),'--plan',str(out/'quality-plan-input.json'),'--release',str(out/'quality-release-input.json'),'--output',str(out)]
    return (run or subprocess.run)(command,env=env,check=True)
