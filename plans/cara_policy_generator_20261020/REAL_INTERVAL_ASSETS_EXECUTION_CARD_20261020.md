# PG-P1-ASSETS：完整真实区间标签与独立动作价格卡

2026-10-20。直接人类要求将此关键前置落实为可执行卡，生产CPU通过后按预算规则推进。原BANK24保持第一顺位，任何旧stage/源码/gate/CPU均不修改。

## 固定完整范围

Cosmos-Predict2.5-2B，原四CAL/seed0/T2W/CFG7/432×768/93帧/35参数对应36实际更新。实际生产适配器保护1–7及36，所有其余合法来源s/时刻t均采集：每CAL406格，四CAL1624正式格；覆盖7→35的最长合法年龄28，不用旧稀疏点补齐。

14完整路径=两条完整预热（observer OFF/ON）+每CAL的Native/observer OFF全D/observer ON全D三条，共12正式。ON预热也采全406格，因此实际采2030格。每格C、A(alpha0.5)、A(alpha1)各一次预热及一次正式，最近D来源的每时刻另加两轮平衡正式重复，共13020实际双支读出试验。各alpha付自己的warp/head/RF/fusion，不把一次头计算重复声称测价。

## 实际采集与标签身份

参考轨迹自然全D执行。保存其实际严格过去D缓存的CPU副本；在当前实际paid probe上对所有合法来源执行源码逆变换核验过的WC完整C分支，以及原beta1单位增量修正和真实head/RF。候选只写独立cache view，不能改变参考轨迹、缓存锚、输入、条件、RNG或solver。每格保存C/Phi/A_HALF原始guided FP32张量，D按当前时刻共享原件。CPU post逐格重读原件，重算e²/ed/d²及实际alpha0.5误差和FP32融合界。

表的身份明确是TEACHER_CONDITIONED_PROPOSAL，C所用两真实D锚为Native参考历史中的s−1/s。它不是随后自由策略中所有先前D历史的真值，也不证明终点质量；之后PG-P1必须完整自然轨迹检验。

## 非重叠费用

实际全D pair测共享paid prefix与之后D区间。候选计时从已经付费的当前probe之后开始，包含自己的完整C/修正head、精确warp/RF和alpha融合，排除诊断源搬运/恢复、hash、原件写盘；这些另纳入整卡真实墙钟。每一合法格均有正式C/A0.5/A1费用，最近D状态在每CAL/时刻保留三轮平衡正式样本。源内平均后按时刻取各CAL最慢观测来源，再CAL等权，输出保守提案价格。保护位置的C/A不可用，写null而非伪造0或D价。

共享非步工作只从observer OFF控制计算，不将ON采集时间写入部署shared cost。该控制含登记的guided取证开销，属于组件提案费用，不能称干净重复端到端速度。

## 完整报价

[配置](../../configs/wc_policy_interval_assets_full1624_r1_20261020.json)，[整卡报价](../../manifests/wc_policy_interval_assets_full1624_whole_quote_r1_20261020.json)。预计9.918333333GPUh，计费上限12GPUh。包括14完整请求、13020读出试验、约52.6GB原始输出、约2.069TB规划源搬运、SHA/重读/归约及退出余量，25%规划margin；此前N09包含区间仅作保守规划依据，不是新动作单价。最低数据盘余量约100.4GB，CPU锚bank规划约18.35GB。实际空闲UUID/显存/compute/锁/v2余额、磁盘和主存均需再准入。

12不属于用户严格<12的免确认范围。准备和生产CPU已获授权；整卡GPU须自己的明确12GPUh批准，不拆卡/缩范围或降低上限规避。

## 生产与验收

CPU新闭包：新单元控制→两flow全部28完整Toy路径/4060格/26040读出试验及原件重读→真实Cosmos请求/guardrails与源码逆变换验证。Toy不是视频/价格结果；不重跑已验旧248+10、旧入口或BANK24的CPU。

执行入口scripts/wc_policy_interval_assets_lifecycle_r1.py，提供prepare/deploy-cpu/cpu-worker/capture/accept/launch-gpu/supervise；实际GPU采样scripts/run_wc_policy_interval_assets_r1.py，CPU原件验收scripts/postprocess_wc_policy_interval_assets_r1.py。原件、失败、拒绝和未到达全部保留；先原件落盘后离线分析，未知派发只恢复原句柄。

原BANK24完整原件与费用接受后才具备上游资格；本卡CPU接受与整卡批准也必须满足。真实启动后一次技术半程和一次ETA收件，不循环监听。GPU进程结束、v2实费加法结算与UUID锁释放后另做独立CPU post，不把释放后的CPU时间算GPU占用费。

只有全1624正式格/费用及Native—OFF—ON全36guided、终态和适用93帧RGB控制均接受，才输出generator_input_ready。原N07/N08/N10/Window24/CAL12不重查，F/B关闭，无训练、人评、付费VLM或OMR。
