# W3 完整因果核心与 LPIPS CPU 准备，13 GPUh 授权已接入

2026-10-04。当前成果是可执行核心和 CPU 控制，尚无新的真实 C/D GPU 视频、正式 RV 标签或方法收益。原 [104 点补验](75_WC_FULL104_R4_CARD_AND_RESULTS.md) 已完成，1153.547616 秒低于单次 1800 秒授权；不重复提交。107 的稀疏端到端净收益未成立判断保持。W3 继续固定 WorldCache 近似器与 dense 算子，先验证同状态下刷新与复用的后果。

## 本轮实现与完整范围

[核心](../src/wcomr/rv0_causal.py) 调用普通推理入口，保留两场景各四种父轨迹：原 Native、cache-off 原 Native 路径、无 router 原 WorldCache、router OFF WorldCache。每条父轨迹使用同一 prepared input、初始噪声和完整 RNG，运行 36 个实际 UniPC 更新 / 72 CFG 调用；没有把强制全算 WorldCache 当作 Native。

在 step22 后对 CFG0/1 分别运行 OFF1、OFF2、C_first、D_second、D_first、C_second，各完整续推 14 更新 / 28 CFG。干预只发生在 call45 或46 的官方 probe 后、decision 前；后续仍使用原自适应策略函数，未来 mask 和 full 次数可以改变。这是一次动作诊断，尚不是同预算策略收益或训练标签。

单组完整范围为 **8 父轨迹、24 后缀、18 模拟编码输出**。相比113的16输出预案，增加每场景一个 OFF 分支解码输出，共2个，用于检验分支解码/guardrail/写出与普通父视频整条路径相等。原8个父视频和8个唯一C/D视频不减少，重复C/D先比较完整轨迹、终态与状态，不再重复编码。完整失败分母保留。

分支解码和写出取自固定官方函数的完整 post-sampling AST，包括 guardrail；两个官方源SHA和两段AST摘要随回执保存。扩展解码只允许 diffusion offload 关闭的当前单进程范围，真实 VAE、设备搬运、峰值显存及耗时仍待实际验证。

## CPU 证据与两次失败

[R3实际CPU回执](../reports/wc_rv0_causal_cpu_r3_20261004.json) 绑定40阶段文件、9官方源及实际冻结 Video2WorldCondition 的 origin/完整类AST；35项未改历史依赖复用R4同SHA回归。CPU禁止CUDA初始化，不加载生成模型权重；Native函数体、采样器、WC、UniPC和解码尾部来自固定源码，网络/条件构造/decoder/writer仍是Toy。

R3用时 **274.089974秒**。flow OFF/ON两组各完成8父、24完整后缀、18模拟输出；合计16父、48后缀、36模拟输出。Native/cache-off和WC/router OFF的每次输入/输出/deep/cache bank、solver输出、终态、完整状态、RNG及模拟编码SHA相等。C/C、D/D交换顺序复现；C/D当前输入相同、C深层调用0、D完整调用；C只使用过去同CFG真实full历史。尾部call71/72是官方70-call horizon之外的原生全算，合法绕过probe。

额外writer缺失和guardrail拒绝两次TECH_BLOCKED保留完整8/24/18计划分母，确认父状态、挂钩、buffers和后端flags恢复。没有新增人工语义审核。

[R1](../reports/wc_rv0_causal_cpu_r1_20261004.json)/[R2](../reports/wc_rv0_causal_cpu_r2_20261004.json) 都在OFF解码桥检查失败，保留原件身份，分别81.637212/82.134445秒。R2明细显示解码输入/输出、guardrail输入/输出和编码SHA均相同，仅缺写出输入观察事件。原因是编译尾部时复制了旧writer全局引用，而父观察器随后才安装。R3将命名空间writer改为调用时解析当前推理模块函数，保留原AST及全部五事件检查；没有删门或改视频来通过。

[独立本地回执审计](../reports/wc_rv0_causal_cpu_local_audit_r3_20261004.json) 重新核对返回JSON的原件SHA、当前40依赖、9源表、两组完整原始轨迹、桥和失败分母，通过。R3原件SHA `3b62223b24853d2c5135e73ec821e8609486a56eb911d3e1ce4d1b3d51ef4dd4`。**尚未回读服务器原件或重验服务器阶段文件**，不能称远端原件独立审计通过。

## LPIPS 资源与冻结诊断协议

[协议实现](../src/wcomr/rv0_lpips.py) 固定lpips包0.1.4、metric0.1、Alex、FP32 CPU、eval、spatial=False，RGB uint8转NCHW并归一化至[-1,+1]。这些输入约定和Alex/metric0.1的选择依据见[官方LPIPS仓库](https://github.com/richzhang/PerceptualSimilarity)。本项目冻结全部93帧、原432×768、不resize/crop/subsample、逐帧距离算术平均；这是我们的评估协议，并非官方视频或物理质量标准。

每个C/D输出分别相对同输入/初始噪声/解码策略的Native35视频，计算 `J_C - J_D`；保留负收益，强制同一Native SHA、帧数和PTS。拒绝缺帧、几何/时间错配及不同Native参考。不是仅比较C/D互距；一次动作自适应后缀的这个量不能直接升级成同预算RV训练标签。

[V2实际CPU资源回执](../reports/wc_rv0_lpips_resource_cpu_v2_20261004.json) 记录隔离目录 `.sync/wc-rv0-lpips-resource-v2/site`，未改共享环境。PyPI wheel完整SHA核对通过；使用已有AlexNet缓存及wheel内linear weights，没有下载新backbone。CPU资源/运行共7.315361秒，禁止CUDA和运行时下载，预训练LPIPS确实在CPU运行。四张64×64合成图的自距0、差距0.1082902923、重复完全相同、负差值保留，四项错配拒绝通过。

wheel SHA `fd537af5828b69d2e6ffc0a397bd506dbc28ca183543617690844c08e102ec5e`；AlexNet SHA `7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02`；linear SHA `df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0`。V2服务器回执SHA `796c9ef2762b90c8ebea7e12c5382be64bcc8848f74097a510125dafbc6407ff`。

[本地返回回执检查](../reports/wc_rv0_lpips_resource_local_check_v2_20261004.json) 验证该SHA与当前协议源码、CPU控制；**服务器package/weight原件复审尚未完成**。V1与此前“指定共享环境没有lpips包”的观察均保留，隔离安装没有使历史观察失真。尚无真实93帧C/D评分、质量接受或物理结论。

## 13 GPUh 最新授权与完整费用

用户在「汇报逐文件核对结果」对话于2026-10-04 06:13:36UTC直接答复“允许增加 GPUh”，对应明确的12→13累计上限提议；已读取直接用户消息核对。见[新授权](../manifests/budget_authorization_20261004_wc_13gpuh.json)/[预算变更回执](../reports/wc_13gpuh_budget_change_20261004.json)。另一会话在原锁下更新权威账本并释放锁，本机镜像SHA与其服务器回执一致；没有清零费用、挪用其它项目预算、选卡或启动实验。

现 **11.022315686839217 / 13 GPUh，45 jobs，无inflight**，余额7119.663527秒。CPU原件记录的12h是变更前快照，保留不改；本地审计识别后续授权变更且核对used/jobs未变。

[新版完整成本](../reports/wc_rv0_causal_scope_cost_r3_20261004.json)/[28项CPU拒绝控制](../reports/wc_rv0_causal_scope_cpu_r3_20261004.json) 接入13h及精确授权ref，拒绝旧12h、错ref、超费或缩范围。18输出条件估算6765.585233秒，拟全wall6900、child6870、kill5、释放30，含准入需6915秒，**算术余量204.663527秒**；尚未选择、预付或提交GPU。C/D未来计算变化、实际decode和峰值未测，代理加余量不是运行上界或完成保证。旧16输出/12h拒绝报告与18输出/12h R2报告保留历史身份。

## 当前审批限制和下一步

自动审批两次拒绝把LPIPS只读审计脚本经既有SSH发送到实验服务器执行，称实验/CPU许可未明确授权该私有代码向该目的地披露。补充与已授权104部署相同路线的核验后仍拒绝；未执行被拒动作，也未换路径绕过。见[限制记录](../reports/wc_rv0_readonly_audit_approval_block_20261004.json)。这与13h预算许可分别处理。

[完整CPU原件审计脚本](../scripts/audit_wc_rv0_causal_cpu.py) 和[LPIPS资源审计脚本](../scripts/audit_wc_rv0_lpips_resource.py) 已准备，本地syntax/返回回执检查完成。待用户明确准许代码同步后，先只读回验服务器原件、固定阶段/上游/资源文件、预算，不初始化CUDA；随后补生产CLI/监督器、真实视频reader/评分接线、冻结部署与fresh GPU资源/锁/预算门。GPU卡只能在全部必要门通过后单次提交，不复用原104或restore身份。正式预算匹配收益、RV标签/Head、独立CONF及完整科学目标仍缺，goal active。
