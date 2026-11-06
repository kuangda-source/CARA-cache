
import base64,gzip,hashlib,json,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');out=root/'outputs'/M['run_id'];stage=root/M['stage'];s=json.loads((out/'supervisor.json').read_text());raw=(out/'diagnostic/receipt.json').read_bytes();r=json.loads(raw);row=r['requests'][0]
assert s['pid']==3115400 and s['child_pid']==3115418 and s['source_revision']==r['source_revision']==M['source_revision'] and s['status']=='GPU_W3_NATIVE_RESPONSE_ONSET_RUNNING'
for pid in (3115400,3115418):
 p=pathlib.Path('/proc/'+str(pid));assert p.exists() and str(stage) in (p/'cmdline').read_bytes().replace(b'\0',b' ').decode() and M['source_revision'] in (p/'cmdline').read_bytes().replace(b'\0',b' ').decode()
by={c['label']:c for c in row['children']};a=by['FIXED61_first'];b=by['LATE69_first']
assert a['status']==b['status']=='COMPLETE_NATIVE_RESPONSE_SUFFIX_NOT_RV_LABEL' and b['responsive_calls']==[69,70] and len(b['inputs'])==28 and len(b['solver_outputs'])==14
checks={'actual_complete_state_and_own_history_before'+str(n):a['response_boundaries'][str(n)]==b['response_boundaries'][str(n)] for n in (65,67,69)}
for n in (65,67,69):
 components=a['response_boundaries'][str(n)]['components'];assert components and a['response_boundaries'][str(n)]['own_CFG_history']
 assert {'output','cpu_rng','python_rng','numpy_rng','cuda_rng','explicit_generators','net.cnt','solver._step_index'} <= set(components)
 assert all(type(d) is str and len(d)==64 and all(c in '0123456789abcdef' for c in d) for d in components.values())
checks['all_inputs_through69_equal']=a['inputs'][:25]==b['inputs'][:25]
for k in ['outputs','deep','banks','solver_outputs']:checks[k+'_before69_equal']=a[k][:12 if k=='solver_outputs' else 24]==b[k][:12 if k=='solver_outputs' else 24]
assert all(checks.values())
report=b['record']['action_report'];changes=[i+1 for i,(x,y) in enumerate(zip(a['record']['action_report']['actual_actions'],report['actual_actions'])) if x!=y]
assert changes==report['response_action_changes']==[69,70] and report['per_CFG_full_counts']==[21,19] and b['record']['parent_restored'] is True
encoded=next(c for c in row['decoded_children'] if c['label']=='LATE69_first');assert encoded['status']=='ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE'
artifact=encoded['artifact'];ref=r['scope']['references']['human_199']['LATE69'];video=pathlib.Path(artifact['path']);video.resolve().relative_to((out/'diagnostic').resolve())
h=hashlib.sha256(video.read_bytes()).hexdigest();assert h==artifact['sha256']==ref['sha256'] and video.stat().st_size==artifact['bytes']==ref['bytes']
post=root/'.sync/wc-w3-native-response-onset-postrun-cpu-r3-20261007';c=json.loads((post/'continuation.json').read_text());p=pathlib.Path('/proc/3115990');assert c['pid']==3115990 and p.exists() and str(post/'continue.py') in (p/'cmdline').read_bytes().replace(b'\0',b' ').decode();assert c['steps']==[] and c['status']=='WAITING_ORIGINAL_GPU_TERMINAL_NOT_CPU_AUDIT_OR_SCORE'
archive=gzip.compress(raw,mtime=0)
result={'status':'FIRST_LATE69_COMPLETE_AND_HISTORICAL_BYTES_PRE_RESPONSE_STATE_INPUT_HISTORY_PASS_WHOLE_BATCH_PENDING','observed_unix':time.time(),'run_id':M['run_id'],'source_revision':M['source_revision'],'original_GPU_pids_confirmed_live':[3115400,3115418],'postCPU_pid_confirmed_live':3115990,'postCPU_steps':0,'FIXED61_vs_LATE69_prefix_checks':checks,'native_response_action_changes':changes,'LATE69_actual_CFG_full_counts':[21,19],'new_LATE69_artifact':artifact,'historical_LATE69_reference':ref,'actual_video_sha256':h,'three_old_loss_candidates_encoded_byte_bridges_now_verified':True,'completed_suffixes_at_snapshot':sum(c['status']=='COMPLETE_NATIVE_RESPONSE_SUFFIX_NOT_RV_LABEL' for c in row['children']),'started_labels_at_snapshot':[c['label'] for c in row['children']],'original_receipt_sha256':hashlib.sha256(raw).hexdigest(),'original_receipt_bytes':len(raw),'archive_sha256':hashlib.sha256(archive).hexdigest(),'GPU_submissions':0,'score_runs':0,'full_batch_or_quality_acceptance':False}
print(json.dumps({'result':result,'native_receipt_gzip':base64.b64encode(archive).decode()}))
