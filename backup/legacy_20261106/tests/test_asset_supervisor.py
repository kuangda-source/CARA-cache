import json,sys,os,subprocess
from pathlib import Path


import pytest

@pytest.mark.parametrize('endpoint,seconds',[('https://huggingface.co',1200),('https://hf-mirror.com',3600)])
def test_download_is_cpu_only_single_identity_and_lock_blocks_duplicates(tmp_path,endpoint,seconds):
    project=tmp_path/'project';(project/'scripts').mkdir(parents=True)
    manifest=project/'manifest.json';manifest.write_text(json.dumps({'endpoint':endpoint,'cpu_download_seconds_cap':seconds,'intended_role':'Small development VQA judge, not paper Qwen3-VL235B or final Joint confirmation'}))
    script=project/'scripts/download_auxiliary.py';script.write_text("import os,json,sys\nfrom pathlib import Path\nPath(sys.argv[sys.argv.index('--receipt')+1]).write_text(json.dumps({'cuda':os.environ['CUDA_VISIBLE_DEVICES'],'token':os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN']}))\n")
    binary=tmp_path/'bin';binary.mkdir();timeout=binary/'timeout';timeout.write_text('#!/usr/bin/env python3\nimport os,sys\nos.execv(sys.argv[3],sys.argv[3:])\n');timeout.chmod(0o755)
    output=tmp_path/'out';cmd=[sys.executable,str(Path(__file__).resolve().parents[1]/'scripts/supervise_asset_download.py'),'--project',str(project),'--manifest',str(manifest),'--output',str(output),'--python',sys.executable]
    env=dict(os.environ,PATH=str(binary)+os.pathsep+os.environ['PATH'])
    subprocess.run(cmd,env=env,check=True,capture_output=True,timeout=10)
    state=json.loads((output/'supervisor.json').read_text());assert state['status']=='DOWNLOAD_EXITED_REQUIRES_INTEGRITY_CHECK' and state['exit_code']==0 and not state['gpu_workload_started']
    assert json.loads((output/'download.json').read_text())=={'cuda':'','token':'1'}
    result=subprocess.run(cmd,env=env,capture_output=True,timeout=10);assert result.returncode!=0
    import fcntl
    with (project/'.sync/judge-download.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        result=subprocess.run(cmd[:-3]+[str(tmp_path/'out2'),'--python',sys.executable],env=env,capture_output=True,timeout=10)
        assert result.returncode!=0 and not (tmp_path/'out2').exists()


@pytest.mark.parametrize('valid',[True,False])
def test_range_mode_selects_cpu_downloader_only_after_pinned_protocol_gate(tmp_path,valid):
    project=tmp_path/'project';(project/'scripts').mkdir(parents=True)
    manifest=project/'manifest.json';protocol={'endpoint':'https://huggingface.co','cpu_download_seconds_cap':3600}
    if valid:protocol['download_strategy']='bounded_http_ranges'
    manifest.write_text(json.dumps(protocol))
    script=project/'scripts/download_l0_adapter_ranges.py';script.write_text("import os,json,sys\nfrom pathlib import Path\nPath(sys.argv[sys.argv.index('--receipt')+1]).write_text(json.dumps({'cuda':os.environ['CUDA_VISIBLE_DEVICES'],'strategy':'ranges'}))\n")
    binary=tmp_path/'bin';binary.mkdir();timeout=binary/'timeout';timeout.write_text('#!/usr/bin/env python3\nimport os,sys\nos.execv(sys.argv[3],sys.argv[3:])\n');timeout.chmod(0o755)
    output=tmp_path/'out';cmd=[sys.executable,str(Path(__file__).resolve().parents[1]/'scripts/supervise_asset_download.py'),'--project',str(project),'--manifest',str(manifest),'--output',str(output),'--python',sys.executable,'--range-download']
    result=subprocess.run(cmd,env=dict(os.environ,PATH=str(binary)+os.pathsep+os.environ['PATH']),capture_output=True,timeout=10)
    if valid:
        assert result.returncode==0 and json.loads((output/'download.json').read_text())=={'cuda':'','strategy':'ranges'}
        assert json.loads((output/'supervisor.json').read_text())['exit_code']==0
    else:
        assert result.returncode!=0 and not output.exists()
