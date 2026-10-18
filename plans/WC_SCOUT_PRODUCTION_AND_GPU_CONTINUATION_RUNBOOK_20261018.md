# 本轮CPU收件后的直接执行入口

用户已直接批准原顺序、生产CPU通过后直接启动；无需再就严格<12GPUh的完整卡问确认。累计cap226与origin79.99637737158223及全部历史保持。不能改变N10原22:43时点、原stage或质量范围。

## 1. 原连续24现在已经具备生产证明

固定source a350ea9822e3443c3cd8f4c601673fc064d49684，stage `.sync/wc-drop1-window24-production-cpu-r1-20261018`，原CPU已终态接受：

- launch `reports/wc_drop1_window24_actual_production_CPU_R1_launch_20261018.json`
- capture `reports/wc_drop1_window24_actual_production_CPU_R1_collection_20261018.json.gz`
- accepted `reports/wc_drop1_window24_actual_production_CPU_R1_independent_acceptance_20261018.json`

N10原件／财务按原22:43收完后，fresh只读资源核对、选真正空闲UUID，调用原脚本（先读`--help`）：

```
.venv/bin/python scripts/launch_wc_drop1_window24_r1.py \
  --CPU-launch-ref reports/wc_drop1_window24_actual_production_CPU_R1_launch_20261018.json \
  --CPU-capture reports/wc_drop1_window24_actual_production_CPU_R1_collection_20261018.json.gz \
  --CPU-acceptance reports/wc_drop1_window24_actual_production_CPU_R1_independent_acceptance_20261018.json \
  --gpu-uuid <fresh空闲UUID> --output <新的GPU派发回执>
```

原配置不变：4CAL×4方法／16正式＋8预热，预测3.064166667、计费上限4GPUh。未知通信或已有fence不重放；不能把局部busy当任务结束或删fence重提。用`capture_wc_drop1_window24_r1.py --mode admission`一次核对。按真实launch的`halfway_check_not_before_unix`和`next_check_not_before_unix`分别安排一次心跳；模式为`halfway`／`terminal`，终态一次捕获后离线`analyze_wc_drop1_window24_r1.py`。先读CLI，严格保留24、旧12端点、四种36guided重复和共同前21步。输出与费用完整收完后再接探索卡。

## 2. 新探索248数值CPU，不是生产CPU

原248包含CAL12的80和BANK24的168完整Toy采样路径。直接复用既有采样／RF／UniPC与原weights-free导入边界，不下载模型；观察器OFF/ON、audit/lean、旧前缀或全轨迹均比较。原CPU句柄与source写在启动回执，长CPU只在半程和ETA各查一次。

数值通过后冻结其完整源码闭包；后续生产层如果只增加配置、监督和post，复用这个已验数值与未变采样依赖，不重新跑相同248。若发现采样实现错误，则保留失败，用新stage修复并按受影响完整范围验证。

## 3. 两卡仍要做的真实生产准备

以下为实施待项，不是已实现的GPU派发器：

1. `scripts/audit_wc_scout_DEV6_exposure_r1.py --output <新回执>`只做一次新六DEV身份审计；它跳过N10质量目录、不读分数。若有曝光／读取不全，保留注册版本与缺口，禁止事后换样凑成功。原六输入见`plans/scouts_20261018/SCOUT_EXPL_DEV6_INPUTS.json`。
2. 为CAL12和BANK24写独立生产配置／执行入口。重用`scout_sampling_r1.execute/plans/matrix`，kind显式绑定，不能改原完整24入口去跑不同scope。引用原完整24的`validate`重验真实模型／mode／校准／N09价格与旧控依赖，新请求再以实际`InferenceArguments`检验。Native分支调用原`clean_speed20_r1.execute(...,'NATIVE')`，真实生产不传Toy专用`CPU_native`。
3. 按已登记蓝图保留CAL12的8正式＋4预热，BANK24的18正式＋6预热／六Native，均一次模型加载。每配置warm1观察器OFF、warm2 ON（Native始终OFF），formal开启两点诊断；原warm完整36guided仍保存，两轮终态／动作／历史／RGB及ON/OFF等价必验。CALA的两个配置都保存step21输入哈希，可直接对同一前态及p20/21；G01不额外算A21提案，不把缺失Phi补成教师。
4. 报价从已验N09完整请求最大值、原N12整卡加载／未归属成本重建，加载／全部warm／观察器复制同步／失败余量不能删。原设计预测1.624315和3.019174、拟议上限2.25和4仍为参考；可预先增加明确诊断余量，但必须保留新完整报价与原粗估。组件包含区间不是A单价。上限若达到12或余额不足才按人类规则问具体整卡，不拆缩。
5. 在独立新stage执行实际生产CPU：已验数值闭包、真实请求／全部矩阵、guardrail拒绝路径、参数／来源／价格绑定、v2/逐UUID监督与完整原件接受接口。CPU通过前不派GPU。新stage不覆盖数值stage、原连续24或N10；每个source、registration、配置和证明明确绑定。
6. 补完整GPU监督／一次派发／CPU post／收件与独立接受。可以复用原24的v2/锁、PID+start_ticks和一次post机制，但新的scope必须正式适配，不能继承原24的“已通过”标志。未知派发只恢复原句柄，正常拒绝不补样。
7. 先CAL12完整验收，再固定CAL的μ/阈值（方向预设为较大z保留D、中位秩阈值，DEV不再拟合），然后BANK24。X-R共享银行，含当前D的误差只作离线标签，不单开GPU、训练或F/B。

## 4. 科学接受与报告

CAL12复核所有可用原件、全93帧LPIPS、G01/G00/G10/G11交互与单共享计划对照，原对照参考从N12／原24原件绑定；跨批次秒数不称clean重复速度。BANK24的D/A必须有同点输入哈希和前20guided依据，三元组仅取第21步；Native35在本卡同输入seed，缺参考留空。每row保存原probe／输出文件SHA及实际内存边界；不把p20/p21拷贝成本当免费门控。

原件、统计有效子集、全部路径／失败分母、实际GPU费用及本UUID释放分别接受。保留相反结果、无改进和证据不足；首次信号不自动合入主稿。更新paper总表、机器索引、稳定报告和LATEST并推送。所有长卡均一次半程和ETA查收，无持续监听。
