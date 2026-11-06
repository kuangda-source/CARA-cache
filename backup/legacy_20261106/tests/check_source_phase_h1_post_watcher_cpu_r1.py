"""Reenact the prior wrong-output-path bug without executing GPU or scoring."""
import ast,json,pathlib,subprocess,sys,tempfile
R=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'src'))
from wcomr.source_phase_h1_production_r1 import RUN,CONFIG,matrix,validate_contract

c=json.loads((R/CONFIG).read_text());validate_contract(c);assert c['run_id']==RUN
outer=ast.parse((R/'scripts/deploy_wc_source_phase_h1_production_r1.py').read_text());code=None
for n in ast.walk(outer):
    if isinstance(n,ast.Constant) and isinstance(n.value,str) and 'postcode=' in n.value:
        for inner in ast.walk(ast.parse(n.value)):
            if isinstance(inner,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='postcode' for t in inner.targets):code=inner.value.value
assert code is not None;compile(code,'<post-watcher>','exec')
old_args,old_call=sys.argv,subprocess.call;calls=[]
try:
    with tempfile.TemporaryDirectory() as temporary:
        root=pathlib.Path(temporary);stage=root/'stage';stage.mkdir();output=root/'outputs'/c['run_id'];output.mkdir(parents=True)
        (output/'supervisor.json').write_text(json.dumps({'status':'SOURCE_PHASE_H1_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'}))
        def fake(cmd,**kw):
            assert cmd[1]==str(stage/'scripts/postprocess_wc_source_phase_h1_cpu_r1.py')
            assert kw['env']['CUDA_VISIBLE_DEVICES']=='';calls.append(cmd);return 0
        subprocess.call=fake;sys.argv=['watcher','999999999',str(stage),str(root),c['run_id']]
        exec(compile(code,'<post-watcher>','exec'),{})
        result=json.loads((stage/'post-CPU-exit.json').read_text());assert result['exit_code']==0 and result['GPU_submissions']==0 and len(calls)==1
        empty=root/'missing_stage';empty.mkdir();sys.argv=['watcher','999999999',str(empty),str(root),'wrong_run_id'];calls.clear()
        try:exec(compile(code,'<post-watcher-missing>','exec'),{})
        except SystemExit as e:assert 'admission failed' in str(e)
        else:raise AssertionError('Wrong output run silently accepted')
        assert not calls and not (empty/'post-CPU-exit.json').exists()
finally:sys.argv=old_args;subprocess.call=old_call
rows=matrix([r['name'] for r in c['requests']]);assert len(rows)==36
assert all(sum(r['method']==m and r['section']=='WARMUP' for r in rows)==2 for m in c['methods'])
assert all(sum(i+1 for s in range(4) for i,r in enumerate([x for x in rows if x['section']=='TIMED' and x['scene']==c['requests'][s]['name']]) if r['method']==m)==14 for m in c['methods'])
print(json.dumps({'status':'H1_CONFIG_RUN_ID_POST_WATCHER_JSON_EXIT_AND_FULL36_MATRIX_CPU_REGRESSION_PASS',
    'wrong_output_refused_without_scoring_or_submission':True,'matrix_science24_warm12_preserved':True,
    'each_method_equal_mean_science_position_3_5':True,'GPU_submissions':0,'ledger_written':False}))
