# 最终共同完整180生产CPU接受，等待具体整卡与预算决定

2026-10-16。**最终共同测试的真实生产CPU已完整接受，可以执行的具体卡已准备好；目前待决定的只有超过自主门槛的完整GPU费用与预算增量。** 方法、最终八新prompt、seed17/43和全部180范围保持冻结，尚未生成新的最终视频或速度结果。

## 1. 原CPU独立验收

12:35按预计时间一次查source `140d0a6af7d5be16d1b191ab3a8e68ffe83d0007` / 原PID1111913，已终态。全部1725 payload SHA、注册身份、六命令退出0与真实Cosmos无权重生产proof通过；完整160 typed请求参数、180排程、Native双seed和guardrail检查、原99数值执行SHA全部接受，148.735906秒。

该CPU没有CUDA初始化、模型权重加载、在线teacher、GPU派发或账本写。原R1第三组测试漏传automatic_quality的失败及其原件在499保留；R2独立重做全六命令，没有拼接旧成功命令或放宽接受。原任务查收自动化已暂停，后续不再查询R1/R2旧进度。

|身份|SHA256|
|---|---|
|原配置|`9de3e5b9c2ce0377888e1244aa77043b42d4f92f0d9cea498c13c59e3aeafd0c`|
|注册|`ebf9703a7babd41d4a8b6cf473427e2a66c5a5a689ff92fd094048c496f304f4`|
|真实生产proof|`bc2516964d0ab3f8271992caf316a5ab3eccb64a5ebab19d4a5688a341c3a0fa`|
|完整CPU bundle|`6fe28e42cd9ccfd930f217ac2fe65b861ff91371c6f666c8eb514ea5aa3f44a0`|
|bound输入指纹|`ca6057af17f795fa1e6c2964715ff80922f1decc4da30d29cf9a6436b07b63ca`|

## 2. 完整待执行卡

卡`WC-PAPER-N07-FROZEN-SHARED180-R1`，run `wc-paper-n07-frozen-shared180-r1`，使用原R2不可变stage/source。四类各2个新prompt×seed17/43×10方法=160正式；20完整warm另计，共180、6318pairs/12636CFG，一次加载、0新teacher。完整十方法包括七个N05前沿点、两强前密简单对照和Native26；所有93帧兼容评分、原拒绝/失败/缺失分母与提示词分组统计均保持。

目标是在新输入、双seed下确认两个已冻结工作点是否具有保真—实际时间价值，并直接面对强有限调优WC/RA与前密C/A对手。GCR/CPA仍使用原实现，不引入T1/P/F_B或训练，不按最终输出重选工作点。

## 3. 最新账本与审批对象

12:36只读fresh v2确认：**累计实结93.581824657 / 当前cap104.971363333 GPUh，预留0、可用11.389538676**，原origin79.99637737158223不变。该查询没有写服务器账本或启动GPU。

- 本卡完整预计及计费上限：**15.055555556 GPUh**，严格超过自主少于12的范围，也超过当前余额。
- 后续N08原完整40预计：3.627500000 GPUh；两卡合计18.683055556。
- 提案：批准本完整180卡，将**同一累计cap提高到113 GPUh**；原used、origin、全部任务与已结算费用保留，不另开窗口。按两卡估计约余0.735119787。
- N09/N10真实费用另待核定；本提案没有假定这些费用为0，也没有用缩卡、删配置或分拆绕过门槛。

已通过界面一次询问该具体范围和cap113，当前未收到直接回复。配置中的113始终是拟议审批对象，服务器cap仍是原值；不因CPU通过自行更新cap、预留或派发GPU。确认来自用户直接规定的单次严格少于12GPUh自主规则及现余额不足，不是新增人工科研评审。

若批准，用已准备的独立cap增量函数原子保留原账本记录，再以具体整卡批准、原source/CPU/参数指纹、全部费用及fresh UUID/v2准入一次派发。首个GPU查收按原配置为启动后16小时，另设一次ETA；不持续读partial。N08在N07完整终点接受后按原40完整范围接续。

## 4. N08预算兼容性检查

等待期间定位到N08合同曾固定旧cap104.971363333，导致即使未来人类明确提高同一窗口的cap，也会被旧常量挡住。原错误已用合成合同重现并保存；现在合同要求cap与原共同配置完全一致、数值有限且不低于旧cap，原origin仍固定，真实准入仍匹配权威账本与单独授权。12项CPU控制通过，没有改变完整40、时钟、角色、费用或授权门槛；不是实际N08生产/速度结果，也没有影响原R2 stage或99数值执行源。

N05/N06均已完整接受；N07共同确认→N08重复clean时间→N09部署/N10自动质量仍是主线顺序。P/T1后排、F/B关闭，无新训练、OMR或人工评审。

## 原件与审查入口

- [wc_paper_N07_actual_production_CPU_R2_collection_20261016_1235.json.gz](../reports/wc_paper_N07_actual_production_CPU_R2_collection_20261016_1235.json.gz) · SHA256 `e49b5a0141d4f240da6dbe7314fe6d187c971d6324cd8b38bca35daf933eeecf`
- [wc_paper_N07_actual_production_CPU_R2_independent_acceptance_20261016.json](../reports/wc_paper_N07_actual_production_CPU_R2_independent_acceptance_20261016.json) · SHA256 `cfb40010e4c902649597488504adeb7e4799eef9081e06c19f5f9b0d3bf784e9`
- [wc_paper_N07_preapproval_fresh_budget_20261016_1236.json](../reports/wc_paper_N07_preapproval_fresh_budget_20261016_1236.json) · SHA256 `fb395945620b7c61114d66542d922ff0ff2c023b8293abbb68dd6dd95e4ad2ea`
- [wc_paper_N07_full180_complete_CPU_and_budget_approval_review_20261016.json](../reports/wc_paper_N07_full180_complete_CPU_and_budget_approval_review_20261016.json) · SHA256 `5209b91124b9931d5b4374b70a225e8861a378a433a14979532cbd49bbbaa09c`
- [wc_paper_N08_fixed_cap_contract_R1_probe_20261016.json](../reports/wc_paper_N08_fixed_cap_contract_R1_probe_20261016.json) · SHA256 `c75be93fde6cffe580240292be0d3a3d752f53124513790691f19699d1d49835`
- [wc_paper_N08_same_window_cap_contract_CPU_repair_20261016.json](../reports/wc_paper_N08_same_window_cap_contract_CPU_repair_20261016.json) · SHA256 `aa7b5270f10e1419e167d6a305efcca4a9bd59b5addc5c3c0df62c90d01528f5`
