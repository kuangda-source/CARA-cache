"""Actual two-flow whole-card supervisor against isolated process/ledger CPU fixtures."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types


def run(stage,config):
    from wcomr import p_reference_same_state_production_r1 as dependency
    path=Path(stage)/'scripts/supervise_wc_p_reference_same_state_r1.py'
    spec=importlib.util.spec_from_file_location('E5_actual_supervisor_CPU_fixture',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    original={k:getattr(dependency,k) for k in ('validate','validate_selected','admit')}
    argv=sys.argv[:];cases=[]
    original_popen=module.subprocess.Popen;original_killpg=module.os.killpg
    from wcomr import p_reference_same_state_execution_r1 as execution
    checks={k:getattr(execution,k) for k in ('validate_execution','validate_post_proof')}
    execution.validate_execution=lambda *a:None;execution.validate_post_proof=lambda *a:None
    arms=[{'id':arm,'flow':flow,'planned_paths':4} for arm,flow in config['flow_arms'].items()]
    try:
        for label,failed_index,busy_index,expected in (
                ('ALL2_EXIT0',None,None,2),('FIRST_STOP',0,None,1),
                ('SECOND_STOP_RETAINED',1,None,2),('BUSY_BETWEEN_OWN_PROCESSES',None,2,1)):
            with tempfile.TemporaryDirectory(prefix='E5_CPU_SUPERVISOR_NOT_GPU_') as folder:
                root=Path(folder);project=root/'project';temporary=root/'stage'
                for p in (project/'reports',project/'.sync',project/'outputs',temporary):p.mkdir(parents=True,exist_ok=True)
                before={'cap_gpu_hours':config['cumulative_cap_GPUh'],'used_gpu_hours':41.90868894585461,
                    'gpu_jobs_launched':78,'status':'CPU_FIXTURE_NOT_REAL_LEDGER'}
                dependency.write(project/'reports/budget.json',before);dependency.write(temporary/dependency.CONFIG,config)
                proof={'status':'P_REFERENCE_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU',
                    'exit_code':0,'config_binding_sha256':dependency.binding(config),'CPU_ONLY_FIXTURE':True}
                dependency.write(temporary/'production-CPU-receipt.json',proof)
                dependency.write(temporary/'selected-CPU-receipt.json',{})
                dependency.write(temporary/execution.PROTOCOL,{})
                dependency.write(temporary/'selection.json',{'source_revision':'CPU_FIXTURE_NOT_EXECUTABLE',
                    'selected_config_sha256':dependency.sha(temporary/dependency.CONFIG),
                    'production_CPU_receipt_sha256':dependency.sha(temporary/'production-CPU-receipt.json'),
                    'selected_CPU_receipt_sha256':dependency.sha(temporary/'selected-CPU-receipt.json'),
                    'execution_protocol_sha256':dependency.sha(temporary/execution.PROTOCOL)})
                dependency.validate=lambda *a:(config,None,None)
                dependency.validate_selected=lambda *a:proof
                dependency.admit=lambda *a,**kw:(before['cap_gpu_hours']-before['used_gpu_hours'],8.)
                commands=[];kill_calls=[];observations=[]
                class Process:
                    def __init__(self,command,**kwargs):
                        index=len(commands);commands.append(command);self.pid=900000+index
                        arm=command[command.index('--arm')+1];self.returncode=1 if index==failed_index else 0
                        output=project/'outputs'/dependency.RUN/arm;output.mkdir()
                        dependency.write(output/'receipt.json',{'status':'CPU_PROCESS_FIXTURE'})
                    def poll(self):return self.returncode
                    def wait(self,*a,**k):return self.returncode
                def observe(*args):
                    index=len(observations);observations.append(index)
                    return {'uuid':dependency.UUID,'compute_cap':'8.6','memory_used_mib':24,
                        'pids':[987654] if index==busy_index else []}
                module.subprocess.Popen=Process;module.os.killpg=lambda *a:kill_calls.append(a)
                module.observe=observe;module.monitored=observe
                sys.argv=[str(path),'--project',str(project),'--stage',str(temporary),
                    '--source-revision','CPU_FIXTURE_NOT_EXECUTABLE']
                module.main()
                result=json.loads((project/'outputs'/dependency.RUN/'supervisor.json').read_text())
                after=json.loads((project/'reports/budget.json').read_text())
                assert len(commands)==expected and len(result['arms'])==2
                assert [c[c.index('--arm')+1] for c in commands]==[a['id'] for a in arms[:expected]]
                assert all(c[c.index('--stage')+1]==str(temporary) for c in commands)
                assert len([a for a in result['arms'] if 'exit_code' in a])==expected
                assert result['complete_original_model_process_attempted']==(expected==2)
                assert sum(a['planned_paths'] for a in result['arms'])==8
                assert all(a['status']=='UNSTARTED_REGISTERED_SCOPE_RETAINED' for a in result['arms'][expected:])
                if failed_index is not None:assert result['unexpected_technical_failure_remaining_scope_retained']==arms[failed_index]['id']
                if busy_index is not None:assert result['resource_did_not_release_between_registered_model_processes']['pids']==[987654]
                assert after['gpu_jobs_launched']==79 and not any('inflight' in k for k in after)
                assert after['used_gpu_hours']==before['used_gpu_hours']+result['wall_seconds']/3600
                assert not kill_calls and result['planned_scope']==config['scope_counts']
                cases.append({'case':label,'all_registered_arm_slots_retained':2,'whole_paths_retained':8,
                    'CPU_process_fixtures_attempted':expected,'one_temporary_ledger_job_charged':True,
                    'no_GPU_or_model_process_created':True,'foreign_processes_never_stopped':True})
    finally:
        for k,value in original.items():setattr(dependency,k,value)
        sys.argv=argv;module.subprocess.Popen=original_popen;module.os.killpg=original_killpg
        for k,value in checks.items():setattr(execution,k,value)
    return cases
