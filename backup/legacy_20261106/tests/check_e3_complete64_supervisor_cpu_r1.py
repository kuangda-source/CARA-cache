"""Run actual whole20 supervisor lifecycle against isolated CPU process fixtures."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile


def run(stage,config):
    from wcomr import e3_complete64_production_r1 as dependency
    path=Path(stage)/'scripts/supervise_wc_e3_complete64_r1.py'
    spec=importlib.util.spec_from_file_location('E3_actual_supervisor_CPU_fixture',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    original={k:getattr(dependency,k) for k in ('validate','validate_selected','admit')}
    argv=sys.argv[:];cases=[]
    original_popen=module.subprocess.Popen;original_killpg=module.os.killpg
    try:
        for label,failed_index,protected,expected in (
                ('ALL20_EXIT0',None,False,20),('KNOWN_CAPACITY_FRESH_NEXT',0,True,20),
                ('UNKNOWN_FIRST_STOP',0,False,1),('UNKNOWN_FIFTEENTH_STOP',14,False,15)):
            with tempfile.TemporaryDirectory(prefix='E3_CPU_SUPERVISOR_NOT_GPU_') as folder:
                root=Path(folder);project=root/'project';temporary=root/'stage'
                for p in (project/'reports',project/'.sync',project/'outputs',temporary):p.mkdir(parents=True,exist_ok=True)
                before={'cap_gpu_hours':config['cumulative_cap_GPUh'],'used_gpu_hours':40.31376163972491,
                    'gpu_jobs_launched':77,'status':'CPU_FIXTURE_NOT_REAL_LEDGER'}
                dependency.write(project/'reports/budget.json',before)
                dependency.write(temporary/dependency.CONFIG,config)
                proof={'status':'E3_COMPLETE64_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU',
                    'exit_code':0,'config_binding_sha256':dependency.binding(config),'CPU_ONLY_FIXTURE':True}
                dependency.write(temporary/'production-CPU-receipt.json',proof)
                dependency.write(temporary/'selection.json',{'source_revision':'CPU_FIXTURE_NOT_EXECUTABLE',
                    'selected_config_sha256':dependency.sha(temporary/dependency.CONFIG),
                    'production_CPU_receipt_sha256':dependency.sha(temporary/'production-CPU-receipt.json')})
                dependency.validate=lambda *a:(config,None,None,None)
                dependency.validate_selected=lambda *a:proof
                dependency.admit=lambda *a:(before['cap_gpu_hours']-before['used_gpu_hours'],8.)
                commands=[];kill_calls=[]
                class Process:
                    def __init__(self,command,**kwargs):
                        index=len(commands);commands.append(command);self.pid=900000+index
                        key=command[command.index('--block')+1]
                        self.returncode=1 if index==failed_index else 0
                        output=project/'outputs'/dependency.RUN/key;output.mkdir()
                        dependency.write(output/'receipt.json',{'status':'CPU_PROCESS_FIXTURE',
                            'protected_capacity_failure':protected and index==failed_index})
                    def poll(self):return self.returncode
                    def wait(self,*a,**k):return self.returncode
                module.subprocess.Popen=Process
                module.os.killpg=lambda *a:kill_calls.append(a)
                module.observe=lambda *a:{'uuid':dependency.UUID,'compute_cap':'8.6','memory_used_mib':24,'pids':[]}
                module.monitored=module.observe
                sys.argv=[str(path),'--project',str(project),'--stage',str(temporary),
                    '--source-revision','CPU_FIXTURE_NOT_EXECUTABLE']
                module.main()
                result=json.loads((project/'outputs'/dependency.RUN/'supervisor.json').read_text())
                after=json.loads((project/'reports/budget.json').read_text())
                assert len(commands)==expected and len(result['blocks'])==20
                assert [c[c.index('--block')+1] for c in commands]==[b['id'] for b in config['blocks'][:expected]]
                assert all(c[c.index('--stage')+1]==str(temporary) for c in commands)
                assert len([b for b in result['blocks'] if 'exit_code' in b])==expected
                assert result['all20_original_processes_attempted']==(expected==20)
                if expected<20:
                    assert result['unexpected_technical_failure_remaining_scope_retained']==config['blocks'][failed_index]['id']
                    assert all(b['status']=='UNSTARTED_REGISTERED_SCOPE_RETAINED' for b in result['blocks'][expected:])
                else:assert 'unexpected_technical_failure_remaining_scope_retained' not in result
                assert sum(b['planned_paths'] for b in result['blocks'])==54
                assert after['gpu_jobs_launched']==78 and not any('inflight' in k for k in after)
                assert after['used_gpu_hours']==before['used_gpu_hours']+result['wall_seconds']/3600
                assert not kill_calls and result['planned_scope']==config['scope_counts']
                cases.append({'case':label,'complete_registered_blocks_retained':20,'fresh_slots_retained':54,
                    'CPU_process_fixtures_attempted':expected,'one_temporary_ledger_job_charged':True,
                    'no_GPU_or_model_process_created':True,'foreign_processes_never_stopped':True})
    finally:
        for k,value in original.items():setattr(dependency,k,value)
        sys.argv=argv
        module.subprocess.Popen=original_popen;module.os.killpg=original_killpg
    return cases
