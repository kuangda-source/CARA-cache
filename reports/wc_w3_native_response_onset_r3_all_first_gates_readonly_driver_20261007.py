
import base64,gzip,hashlib,json,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');out=root/'outputs'/M['run_id'];stage=root/M['stage'];s=json.loads((out/'supervisor.json').read_text());raw=(out/'diagnostic/receipt.json').read_bytes();r=json.loads(raw);row=r['requests'][0]
assert s['pid']==3115400 and s['child_pid']==3115418 and s['source_revision']==r['source_revision']==M['source_revision'] and s['status']=='GPU_W3_NATIVE_RESPONSE_ONSET_RUNNING'
for pid in (3115400,3115418):
 p=pathlib.Path('/proc/'+str(pid));assert p.exists() and str(stage) in (p/'cmdline').read_bytes().replace(b'\0',b' ').decode() and M['source_revision'] in (p/'cmdline').read_bytes().replace(b'\0',b' ').decode()
by={c['label']:c for c in row['children']};modes=['FIXED61','LATE69','RESP65','RESP67']
assert all(by[m+'_first']['status']=='COMPLETE_NATIVE_RESPONSE_SUFFIX_NOT_RV_LABEL' for m in modes)
checks={}
for n,group in [(65,modes),(67,['FIXED61','LATE69','RESP67']),(69,['FIXED61','LATE69'])]:
 a=by[group[0]+'_first'];prefix=n-45;entry={}
 for mode in group[1:]:
  b=by[mode+'_first'];items={'complete_state_and_history':a['response_boundaries'][str(n)]==b['response_boundaries'][str(n)],'inputs_through_first_variable_call':a['inputs'][:prefix+1]==b['inputs'][:prefix+1]}
  for k in ['outputs','deep','banks','solver_outputs']:items[k+'_prefix']=a[k][:prefix//2 if k=='solver_outputs' else prefix]==b[k][:prefix//2 if k=='solver_outputs' else prefix]
  assert all(items.values());entry[mode]=items
 components=a['response_boundaries'][str(n)]['components'];assert components and a['response_boundaries'][str(n)]['own_CFG_history']
 assert {'output','cpu_rng','python_rng','numpy_rng','cuda_rng','explicit_generators','net.cnt','solver._step_index'}<=set(components)
 assert all(type(d) is str and len(d)==64 and all(c in '0123456789abcdef' for c in d) for d in components.values())
 checks[str(n)]=entry
c=by['RESP67_first'];record=c['record'];report=record['action_report'];assert c['responsive_calls']==[67,68,69,70] and record['parent_restored'] is True and len(c['inputs'])==28 and len(c['solver_outputs'])==14
native=[e for e in report['suffix_events'] if e['call'] in c['responsive_calls']];assert len(native)==4 and all(e['native_response'] is True and e['paid_probe'] is True and not e['current_deep_truth_used'] and not e['actual_native_override'] and e['actual_action']==('C' if e['native_skip'] else 'D') for e in native)
fixed=by['FIXED61_first']['record']['action_report']['actual_actions'];changes=[i+1 for i,(a,b) in enumerate(zip(fixed,report['actual_actions'])) if a!=b];assert changes==report['response_action_changes'] and set(changes)<=set(c['responsive_calls'])
counts=[sum(a=='D' for a in report['actual_actions'][slot::2]) for slot in (0,1)];assert counts==report['per_CFG_full_counts']
artifacts={}
for mode in modes:
 encoded=next(d for d in row['decoded_children'] if d['label']==mode+'_first');assert encoded['status']=='ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE';a=encoded['artifact'];p=pathlib.Path(a['path']);p.resolve().relative_to((out/'diagnostic').resolve());assert hashlib.sha256(p.read_bytes()).hexdigest()==a['sha256'] and p.stat().st_size==a['bytes'];artifacts[mode]=a
post=root/'.sync/wc-w3-native-response-onset-postrun-cpu-r3-20261007';q=json.loads((post/'continuation.json').read_text());p=pathlib.Path('/proc/3115990');assert q['pid']==3115990 and p.exists() and str(post/'continue.py') in (p/'cmdline').read_bytes().replace(b'\0',b' ').decode();assert q['steps']==[] and q['status']=='WAITING_ORIGINAL_GPU_TERMINAL_NOT_CPU_AUDIT_OR_SCORE'
data=gzip.compress(raw,mtime=0);result={'status':'ALL4_FIRST_MODES_COMPLETE_ALL_REGISTERED_PRE65_67_69_STATE_INPUT_HISTORY_GATES_PASS_FULL_REPEATS_PARENT_QUALITY_PENDING','observed_unix':time.time(),'run_id':M['run_id'],'source_revision':M['source_revision'],'original_GPU_pids_confirmed_live':[3115400,3115418],'postCPU_pid_confirmed_live':3115990,'postCPU_steps':0,'registered_prefix_gates':checks,'first_mode_full_CFG_counts':{mode:by[mode+'_first']['record']['action_report']['per_CFG_full_counts'] for mode in modes},'RESP67_actual_response_changes_fixed_calls':changes,'RESP67_native_response_events_67_to70':native,'first_control_wall_seconds':{mode:by[mode+'_first']['record']['control_wall_seconds'] for mode in modes},'first_artifacts':artifacts,'RESP67_LATE69_actual_counts_equal_first_only':counts==by['LATE69_first']['record']['action_report']['per_CFG_full_counts'],'scope_counts':[1,10,6,2],'complete_suffixes_at_snapshot':sum(c['status']=='COMPLETE_NATIVE_RESPONSE_SUFFIX_NOT_RV_LABEL' for c in row['children']),'started_labels_at_snapshot':[c['label'] for c in row['children']],'original_receipt_sha256':hashlib.sha256(raw).hexdigest(),'original_receipt_bytes':len(raw),'archive_sha256':hashlib.sha256(data).hexdigest(),'GPU_submissions':0,'score_runs':0,'full_batch_or_quality_acceptance':False}
print(json.dumps({'result':result,'native_gzip':base64.b64encode(data).decode()}))
