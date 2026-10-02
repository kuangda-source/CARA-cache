# r3独立技术门通过：共用官方输入、完整RNG及逐字段状态

2026-10-03，北京时间。唯一run `wc-mid-parity-r3`，卡 `WC-INPUT-STATE-PARITY-R3-20261003-A`，部署source `4bd3b72ef68b90d0eb3eb833e8f452c2b7149aa4`。supervisor退出0、原runner正常结束，原始文件/source/状态/费用/释放审计通过。**仅接受本次最短匹配前缀技术门，不自动解锁H0/H1或RV。** r1/r2原FAIL、源代码、回执和全部成本永久保留，[71](71_WC_MIDDLE_R2_RESULTS.md)没有被升级为PASS。

## 1. 具体修复与公平接口

实际17项CPU控制及全部固定资产/import/package门通过后才执行本卡，见[72协议](72_WC_PREPARED_INPUT_CPU_AND_R3_CARD.md)。官方 `_get_data_batch_input` 首次执行，原batch保持隔离master拷贝；第二臂使用相同prepared字段和独立深拷贝，并重放相同准备前→准备后RNG转移。保持官方随机FPS、模型、输入场景、seed、采样器和缓存算法，不硬编码FPS。

两阶段重置完整Python、NumPy、Torch CPU/CUDA RNG，独立请求内solver `seed_g`仍由StateRoundtrip保存/恢复。新增命名输入、实际condition全部字段以及完整状态组件签名；原input/output/state/trace/counts/sampling门全部保留，没有drop字段或放宽比较语义。

## 2. 实际结果

baseline和observed均止于13个完整UniPC更新/26次CFG前向；包含中间刷新pair25/26，仅layer2的两个QKV和六个真实dense、matched-full、sparse shadowcase。dense输出始终返回原模型，候选不写部署cache。

| 技术门 | 结果 |
|---|---|
| 官方prepared请求/字段及准备前后各RNG签名 | 两臂全部一致 |
| 26个原聚合输入/输出哈希 | 全部一致 |
| 26个命名输入（张量及非张量）/CFG condition | 全部一致 |
| full/skip trace、block counts、36步时间网格/采样配置 | 一致 |
| 第13步原完整状态指纹 | 一致 |
| 第13步36个状态组件 | 全部一致，无字段差异 |
| observed进程内restore/latent字节 | 一次检查通过 |
| 2QKV原始文件与6case/3repeat | source、file/raw SHA、shape/dtype/finite、覆盖及重复中位数审计通过 |

36个组件包括14个net/WC/cache字段、16个实际非callable solver字段、输出latent、Python/NumPy/CPU/CUDA RNG及独立Generator。两臂命名输入和condition差异列表为空；全9项合并门均true。独立CPU审计没有初始化CUDA，没有新GPU重算误差。

两个layer2采样点的操作速度比分别1.204、1.200，中位1.202；matched-full最大RMSE0.586%、sparse最大1.131%，二者通过5%/1.1技术筛查。只采一个已消耗开发场景的两个相关位置，不是独立质量确认、全层配置验收或端到端加速。

## 3. 能解释和不能解释的内容

修复后的共享准备/全RNG控制在真实模型最短配对前缀中达到严格一致，说明该技术接口可继续用于有界准备。修复同时控制prepared batch和完整RNG，**没有单独干预FPS与RNG的GPU因子对照**，不把结果写成r2唯一根因已经确定。r2只保存总SHA，其现场具体差异仍UNKNOWN；r2的104点数据仍是部分可用算子诊断。

本卡止于step13，restore后没有实际GPU续推到下一步；条件签名相同也不等于实现了独立可重启的condition/closure整管线快照。正式H1/RV分叉还需完整快照、重复/顺序互换和续推等因果门及独立具体范围。没有完整解码视频、质量收益、反事实收益标签、Head/LoRA或专家数据训练。本卡通过不自动批准后续GPU任务；无r4授权。

## 4. 成本与资源释放

监督GPU全过程墙钟 **486.3193481573835秒（0.13508870782149543GPUh）**，包括加载、准备、两前缀、shadow、状态诊断和flush，低于1200秒上限。累计 **4.390463858430222/12GPUh**、31jobs，余 **7.609536141569778GPUh**，无inflight；原r1/r2失败及旧任务都计入。

原supervisor2633815、timeout2633897、runner2633899均退出，shared `f1.lock`空闲；指定A6000回到24MiB，compute apps为空。没有停止其他任务。权威账本保留原supervisor实际结算标签，独立审计结论另存。

## 5. 证据及下一项

- [原runner](../reports/wc_mid_parity_r3_runner_20261003.json)、[supervisor结算](../reports/wc_mid_parity_r3_supervisor_20261003.json)、[摘要](../reports/wc_mid_parity_r3_summary_20261003.json)、[独立审计](../reports/wc_mid_parity_r3_audit_20261003.json)。
- [actual CPU17/来源回执](../reports/wc_mid_parity_r3_deployment_20261003.json)、[授权与固定范围](../manifests/wc_mid_parity_r3_authorization_20261003.json)。
- 两个原QKV留服务器 `outputs/wc-mid-parity-r3/diagnostic/`，Git只存回执/路径/SHA。

下一步由协调者决定单个科学问题的具体卡及预算；可基于该接口和既有数值诊断准备H0互补性或H1来源×寿命所需的完整因果检查，当前不直接提交。W1/replay/build不重跑，W2扩展保持暂停。[WC-RV W3](68_WC_COUNTERFACTUAL_REFRESH_VALUE_DESIGN.md)保留同状态有符号刷新收益与同预算机会成本设计，先收益空间及标签可靠性再有证据的小Head，不因技术门通过直接开始训练。
