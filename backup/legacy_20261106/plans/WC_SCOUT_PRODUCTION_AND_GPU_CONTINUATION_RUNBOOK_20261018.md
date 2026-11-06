# 本轮CPU收件后的直接执行入口

## 10-19最新：R2生命周期CPU两卡已接受

请先用[已验CPU直接接续手册](WC_SCOUT_GPU_READY_CONTINUATION_20261019.md)。两卡source2bd41dc8／每1789源／两命令均接受，CPU77.617048／65.231004秒；实际R2三件套与全部GPU CLI已写明。原24仍00:51优先资源检查，完整接受后才接CAL12；四CAL冻结gate后BANK24。以下R1失败及R2待查文字保留历史，不重跑已验数值／入口／生命周期CPU，不将工具就绪当新视频或实际GPU接受。

## 最新：生命周期R1打包失败，改用R2独立stage

[601原件与修复](../research/601_WC_SCOUT_LIFECYCLE_R1_PACKAGE_FAILURE_AND_R2_ISOLATED_REPAIR_20261018.md)：R1完整source/runtime一致，首组共用测试缺另一kind的配置，未执行第2命令／未接受；原失败保留。R2只将两份现有配置闭包都打入每卡新1789源stage，原1772执行依赖不改，两份overlay独立20项本地控制已通过。下面生命周期R1的stage／回执用于历史；新部署使用`wc-scout-<kind>-gpu-lifecycle-cpu-r2-20261018`与`reports/wc_scout_<KIND>_GPU_lifecycle_CPU_R2_launch_20261018.json`。其他CLI、接受边界和上游顺序保持；严格按R2真实launch分别安排半程／ETA，不重放R1，也不重跑已验数值／原入口。

## 23:00接续：原入口已接受，新生命周期使用独立证明

[600新工具和控制](../research/600_WC_SCOUT_DISTINCT_GPU_LIFECYCLE_LOCAL_CONTROLS_AND_PRODUCTION_CPU_20261018.md)：R2数值248＋10与两个真实入口CPU都已接受，以下旧待验／待开发段落为历史，不能重新执行它们。新生命周期代码已实现并通过20本地控制；每kind新stage复用原1772个文件，新增生命周期实际CPU两命令待验。

新stage的监督／post使用自己的source；真正生成始终调用原c1c95ce0入口stage，保持CPU证明对应原registration。每次完整准入重验二者，不能把新registration塞给旧入口CPU证明。

```sh
.venv/bin/python scripts/wc_scout_gpu_lifecycle_cpu_r1.py deploy --kind CAL12 --stage .sync/wc-scout-cal12-gpu-lifecycle-cpu-r1-20261018 --output reports/wc_scout_CAL12_GPU_lifecycle_CPU_R1_launch_20261018.json
.venv/bin/python scripts/wc_scout_gpu_lifecycle_cpu_r1.py deploy --kind BANK24 --stage .sync/wc-scout-bank24-gpu-lifecycle-cpu-r1-20261018 --output reports/wc_scout_BANK24_GPU_lifecycle_CPU_R1_launch_20261018.json
```

每launch的+180秒／+360秒分别一次半程／终态，不持续监听。用`capture_wc_scout_gpu_lifecycle_cpu_r1.py --mode halfway/terminal --launch-ref <原启动> --output <新回执>`，然后`--mode accept --capture <已存终态> --output <新独立接受>`。接受前不称GPU_dispatch_ready。

生命周期CPU及原Window24完整终态接受后，以原CPU三件套、原Window24实际完整capture／acceptance和fresh UUID执行：

```sh
.venv/bin/python scripts/launch_wc_scout_gpu_r1.py --CPU-launch-ref <CAL12生命周期原launch> --CPU-capture <CAL12生命周期完整capture> --CPU-acceptance <CAL12生命周期独立接受> --upstream-capture <原Window24实际完整capture> --upstream-acceptance <原Window24独立接受> --gpu-uuid <fresh UUID> --output <新GPU回执>
```

先一次`capture_wc_scout_gpu_r1.py --mode admission`核对真实准入。长卡按launch的`halfway_check_not_before_unix`与`next_check_not_before_unix`各另约一次；终态capture后只离线`analyze_wc_scout_gpu_r1.py`，CAL12另加`--gate-output <新的四CAL门控.json>`，完整接受后才固定四CAL的μ／中位阈值。BANK24使用同一启动CLI、自己的生命周期CPU三件套、CAL12完整capture／acceptance及`--frozen-gate <事前四CAL门控.json>`。不先跑DEV再拟合门控，不将X-R另开GPU。

原Window24由`worldcache-gpu`两小时资源任务承接，下一次00:51，不在本工具开发任务双派发。生命周期CPU完成后将其真实证明补入原24未来终态查收接续，GPU顺序保持原24→CAL12→BANK24。busy无派发与未知通信分别保留，不能清fence重试。

## 当前补充：R1接受，R2拒绝边界重验与可执行的生产入口CPU

先读[597](../research/597_WC_SCOUT_R1_NUMERIC_ACCEPTED_REFUSAL_BOUNDARY_R2_AND_PRODUCTION_NEXT_20261018.md)。原R1完整248接受；R2保留全部248并补10拒绝边界，22:10／22:25各一次，尚未接受。六DEV项目输出身份审计已由R1＋R2补齐，无命中，外部曝光不作保证。以下旧“待审计／尚未执行”均为历史。

R2数值全部接受后，依次生成配置和完整报价，保留旧设计估算：

```
.venv/bin/python scripts/prepare_wc_scout_production_entry_r1.py --kind CAL12 --quote-output reports/wc_scout_CAL12_whole_quote_R1_20261018.json --output reports/wc_scout_CAL12_production_entry_config_preparation_R1_20261018.json
.venv/bin/python scripts/prepare_wc_scout_production_entry_r1.py --kind BANK24 --quote-output reports/wc_scout_BANK24_whole_quote_R1_20261018.json --output reports/wc_scout_BANK24_production_entry_config_preparation_R1_20261018.json
```

将两份新configs、两份报价与两份preparation及R2实际接受原件明确提交到Git，再单次部署各独立入口CPUstage（不要拷贝修改在跑stage）：

```
.venv/bin/python scripts/wc_scout_production_entry_cpu_r1.py deploy --kind CAL12 --stage .sync/wc-scout-cal12-production-entry-cpu-r1-20261018 --output reports/wc_scout_CAL12_real_entry_CPU_R1_launch_20261018.json
.venv/bin/python scripts/wc_scout_production_entry_cpu_r1.py deploy --kind BANK24 --stage .sync/wc-scout-bank24-production-entry-cpu-r1-20261018 --output reports/wc_scout_BANK24_real_entry_CPU_R1_launch_20261018.json
```

每个stage两命令：完整配置／可逆入口／固定计划控制组，以及真实Cosmos生产入口`--cpu-check`。数值依赖复用未变R2的248＋10，不再跑第三遍。部署器核对完整源闭包不覆盖任何已验数值文件，禁止CUDA、权重与下载，不碰N10原stage。入口CPU证明不覆盖尚未实现的GPU监督／post／收件链，接受字段明确`production_entry_CPU_accepted=true / GPU_dispatch_ready=false`，不能直接转GPU准入。

按每份launch的halfway_not_before_unix（+180秒）／final_not_before_unix（+360秒）各约一次，不持续监听。收件CLI：

```
.venv/bin/python scripts/capture_wc_scout_production_entry_cpu_r1.py --mode halfway --launch-ref <原kind启动回执> --output <新的半程.json.gz>
.venv/bin/python scripts/capture_wc_scout_production_entry_cpu_r1.py --mode terminal --launch-ref <原kind启动回执> --output <新的完整.json.gz>
.venv/bin/python scripts/capture_wc_scout_production_entry_cpu_r1.py --mode accept --capture <已存完整回执> --output <新的独立入口接受.json>
```

若部署未知，只恢复同stage原句柄不重放。失败或不完整均保留，原24与N10不受影响。入口接受后继续实现／验证新scope的GPU监督、一次派发、post与逐原件接受，不能把入口组件通过写成全生命周期通过。完整CPU接受、上游原24终态接受且fresh资源／v2准入后按原授权启动CAL12，然后固定CAL gate参数、推进BANK24。

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
