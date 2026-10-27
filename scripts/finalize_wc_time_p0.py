import json,hashlib
from pathlib import Path
r=Path(__file__).resolve().parents[1];d=r/'plans/cara_wc_time_protocol_p0_20261027'
def load(p):return json.loads((r/p).read_text())
def sha(p):return hashlib.sha256((r/p).read_bytes()).hexdigest()
def save(p,v):(r/p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
local=load('reports/cara_wc_time_P0_local_CPU_20261027.json');dual=load('reports/cara_wc_time_P0_dual_host_CPU_20261027.json');ra=load('reports/cara_wc_time_P0_RA_identity_20261027.json')
refs=['src/wcomr/wc_time_protocol_p0.py','tests/check_wc_time_protocol_p0.py','reports/cara_wc_time_P0_local_CPU_20261027.json','reports/cara_wc_time_P0_dual_host_CPU_20261027.json','reports/cara_wc_time_P0_dual_host_CPU_attempt1_20261027.json','reports/cara_wc_time_P0_resources_postcheck_20261027.json']
for h,x in dual.items():
 assert x['exit_code']==0 and not x['container_running'] and x['device_requests'] is None
 assert x['payload_sha256']['src/wcomr/wc_time_protocol_p0.py']==sha('src/wcomr/wc_time_protocol_p0.py')
 assert x['payload_sha256']['tests/check_wc_time_protocol_p0.py']==sha('tests/check_wc_time_protocol_p0.py')
 assert not x['result']['CUDA_initialized']
for c in local['checks']:assert c['Native_WC_allD_guided_latent_RGB_RNG_equal'] and c['timing_on_off_all_three_equal']
save(d/'TIME_BOUNDARY_TESTS.json',dict(status=local['status'],source_and_receipt_SHA={n:sha(n) for n in refs},local=local,hosts={h:{k:x[k] for k in ('exit_code','wall_seconds','container_running','device_requests')} for h,x in dual.items()},GPU_submissions=0,real_GPU_equivalence_passed=False,seven_role_production_combination_passed=False))
cost=load(d/'COST_AND_RESOURCE_ENVELOPE.json');cost['CPU_scoring_plan']={'phase_A':{'cpus':4,'memory_GiB':12,'wall_hours':1,'allocated_vCPUh':4},'phase_B':{'cpus':4,'memory_GiB':12,'wall_hours':6,'allocated_vCPUh':24},'total_allocated_vCPUh_cap':28,'measured_full_quote':None}
cost['current_turn_actual']={'GPUh':0,'CUDA_initialized':False,'quality_model_executions':0,'dual_host_CPU_container_wall_seconds':{h:x['wall_seconds'] for h,x in dual.items()},'dual_host_CPU_allocated_vCPUh':sum(x['wall_seconds'] for x in dual.values())*2/3600,'latest_local_CPU_test_wall_seconds':local['CPU_wall_seconds'],'RA_binding_CPU_wall_seconds':ra['CPU_wall_seconds'],'all_local_preparation_CPU_seconds':None,'note':'Only measured jobs listed; earlier local trials, source inspection and failed serialization wall were not instrumented. No invented total; four_card recovered original terminal, not billed twice.'}
cost['budget_authorization_delta']={'mainline_cap_increment_GPUh':24,'notify_on_each_increase':True,'applied':False,'current_cap':226,'new_GPU_execution_authorized':False}
save(d/'COST_AND_RESOURCE_ENVELOPE.json',cost)
rows='\n'.join('| '+h+' | '+str(round(v['native_request_seconds'],3))+' s | '+str(round(v['all73_at_native_scenario_GPUh'],3))+' GPUh | null |' for h,v in cost['hosts'].items())
(d/'PRICE_QUOTE.md').write_text('''# 本轮唯一费用与资源汇总

状态：**NOT_READY — 尚缺全方法真实报价；CPU准备完成不等于GPU执行许可。**

| 主机 | 历史Native T_request参考 | 73条均按该Native计的规划情景 | 完整实测报价 |
|---|---:|---:|---|
'''+rows+'''

情景公式：(73×历史Native秒/3600 + 两次加载合计1h + 保存释放0.35h)×1.25。加载/保存是规划占位，不是实测。此数既非真实报价也非保守上界，不据此申请运行、扣账或承诺5–7GPUh。两服务器是择一方案，不叠加两份额度。

逐方法NATIVE/allD/README/PaperPort/Tuned/RA/CARA均在COST_AND_RESOURCE_ENVELOPE.json列明新T_DD与完整报价=null；仅两卡历史Shared有可参考T_request，四卡Shared新口径无同身份价格。allD额外probe、WC不同命中、RA、诊断张量/hash开销、完整scorer和热环境尚无实测完整价格。报价补齐前不能称可执行P0卡。

总范围73：A26+B47，两次加载、13warm、12诊断、8锚点/候选、28正式、12复测；0自动重试。实际持卡必须包括安装、全部运行、保存、空等、失败、回收和结算。A释放后4Alex/372帧；B释放后24Alex+24PIQ/VGG，共4464评分帧次，以及84质量门+28活动度描述位置。A/B评分CPU总上限提案28 allocated vCPUh（4核，分别1h/6h，12GiB），不能冒充实际用量；评分GPU预算0。

当前实耗：GPU提交0、CUDA初始化false、质量模型执行0。两个远程CPU容器分别17.444048秒、20.173147秒、2CPU/8GiB、已退出；allocated vCPUh总0.02089844。最终本地小张量CPU测试2.3860035秒；RA身份重建0.870966583秒。资源哈希读取分别2.440436/2.511431秒。第一次双端调度中四卡已成功、两卡基准路径断言失败未创建任务；修复后仅两卡执行，四卡恢复原终态，无重复工作。其他本地早期测试/失败序列化/整理耗时没有统一仪表，完整CPU总量=null，不伪造数字。机器可读实耗与所有接受件指纹一并保存。

磁盘规划最低可用30GiB，真实视频/诊断张量尺寸上界及写入速度仍需测量；初始空闲约四卡989.5GiB、两卡1009.2GiB，RAM可用约80.3/53.4GiB。当前快照不替代启动时准入。

中央226GPUh上限，已用172.2657747141984，财务不确定保留16.5，可用37.234225285801614；两卡镜像旧数不合并。用户允许必要时主线上限每次增加24GPUh并通知；本轮不调额度、不改账本。最终16完整费用与保留额尚未报价，先预留确认预算再申请CAL。增加总上限不修改既有卡硬限或自动授权新卡。

本轮交付没有附加高速19D。完整生产监督器/七角色组合CPU、LPIPS权重绑定、真实GPU等价与全部报价缺口须统一补齐，形成一次完整执行申请；不要拆成未报价的小试跑绕过范围合同。
''')
