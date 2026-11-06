"""Exercise the actual watcher path builder and refuse changed complete cards."""
import copy,importlib.util,json,tempfile
from pathlib import Path


def run(stage,project):
    from wcomr.teacher_first_velocity_production_r1 import CONFIG,RUN
    spec=importlib.util.spec_from_file_location('actual_teacher_watch',stage/'scripts/watch_wc_teacher_first_velocity_cpu_r1.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    output,command=module.paths(stage,project)
    assert output==project/'outputs'/RUN
    assert command[1:]==[str(stage/'scripts/postprocess_wc_teacher_first_velocity_cpu_r1.py'),
        '--project',str(project),'--stage',str(stage)]
    original=json.loads((stage/CONFIG).read_text());refused=[]
    with tempfile.TemporaryDirectory() as tmp:
        fake=Path(tmp);(fake/CONFIG).parent.mkdir(parents=True)
        for mutation,value in [('run_id','wc-wrong-path'),('branch_labels',['C_REPLAY']),
                ('teacher_committed_to_parent_or_suffix',True),('first_branch_readouts',['A','C'])]:
            changed=copy.deepcopy(original);changed[mutation]=value
            (fake/CONFIG).write_text(json.dumps(changed))
            try:module.paths(fake,project)
            except ValueError:refused.append(mutation)
            else:raise AssertionError('Changed complete watcher contract accepted: '+mutation)
    return {'actual_watch_config_derived_output_and_post_command':True,
        'watch_changed_card_refused':refused,'GPU_submissions':0,'ledger_written':False}
