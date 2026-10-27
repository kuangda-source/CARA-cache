# WorldCache 对 Native 的历史 LPIPS 审计

用户要求核查约0.5的旧结果，核对配置、种子、视频配对和官方评分，保持原评价标准。此次仅读取原件并做 CPU 重评分；没有重新生成视频、启动 GPU 或修改旧验收。

## 审计范围与身份

旧结果来自两个相关但不同的批次：

- 10月4日 FAIR 两场景阈值扫描：human_199 的 WC .08 对 Native 为 **0.501563**；同一场景 .04/.06 分别为0.346907/0.424745。common_sense 的 .04/.06/.08 分别为0.287830/0.333153/0.408304。
- 10月6日补齐 Native 参考后的七组 WC .06：industry_084 为 **0.532712**，misc 为 **0.493993**；七场景等权均值 **0.410505**。原 CAL 分母8，robot_054 拒绝，接受7，拒绝未替换。

旧93帧距离范围：industry .06为0.510496–0.562548，misc .06为0.469393–0.525334，human .08为0.481266–0.538297。因此这些高均值不是少数异常帧造成；帧不是独立样本，不据此增加场景样本量。

不能把上述结果概括为“官方配置所有样本都约0.5”，也不能把两场景 .08 扫描当作论文全部超参数的实现。

证据：[FAIR原结果](119_WC_EXISTING_FAIR_W1_FULL_FRAME_LPIPS_RESULTS.md)、[七组原结果](138_WC_W1_APPROVED_FIVE_REFERENCE_EXECUTION_AND_RESULTS.md)、[本次身份复核](../reports/wc_native_lpips_historical_protocol_audit_20261027.json)、[16个原始视频哈希现场复核](../reports/wc_native_lpips_original_asset_preflight_20261027.json)。

## 配置与种子核查

五个补生成 Native 的完整 request 字典与对应旧 WC 一致，包括提示词、负面提示词、seed=0、guidance=7、T2W、input_path=None、432×768、93帧、请求35步。setup 字典仅 output_dir 和 worldcache_enabled 不同；两臂使用同一2B/post-trained权重路径及快照标识。

实际采样均为同一36项 UniPC/Karras 时间步，72次CFG；Native 记录为72次完整计算、0次跳过，并显式恢复原类 forward，未让旧实例上的缓存 patch 留在 Native 中。WC 缓存 horizon 仍为70，这个与72调用的交互是已披露的本地协议。

另外两组 Native 来自 FAIR。其 WC .06 视频与旧 CAL8 对应视频 SHA 完全相同，Native 参考也与历史评分所指 SHA 一致。七对均按明确场景和哈希配对，没有按目录顺序猜测。

固定公开代码的样本配置默认seed也是0；这不等于论文逐样本seed清单已获验证。

采样源码 `arch_invariant_rand` 使用私有 `numpy.random.RandomState(seed)` 产生初始噪声，同 seed/shape 不依赖之前全局 RNG 消耗。但旧视频批次未找到完整初始噪声张量哈希，不能把源码保证写成当时实际张量逐位验证。

另有归因边界：五组 Native 补生成代码要求共享 eval，早期 WC runner 未保留同样的显式模式守卫。两组跨批 WC 视频逐位一致支持兼容性，却不能证明其余五组的模式等价。未找到同次运行“WC wrapper 强制所有步完整计算”与原生 forward 的完整视频零差异对照。故不声称已排除所有运行路径因素。

## 与论文及官方代码的对照

| 项目 | 这批历史结果 | 官方资料 |
|---|---|---|
| 生成任务/参考 | CAL T2W，参考同请求 Native | 论文表6是 EgoDex I2V，参考真实视频 |
| 采样 | UniPC/Karras，请求35、实际36步 | 论文4.1写 Euler 35步 |
| 缓存基础阈值 | 七组 .06；两场景另扫 .08 | 论文 .08 |
| saliency weight | 1.0 | 论文 .12 |
| 光流计算空间缩放 | README命令的2.0，源码实际上采样 | 论文附录选择.5，源码默认也为.5 |
| ATS增长系数 | horizon=70使代码计算base_mult=5 | 论文beta_d=4 |
| LPIPS实现 | lpips0.1.4 / AlexNet / version0.1 | 官方 evaluate.py 调用 piq.LPIPS()，默认 VGG16 |
| 输入规范 | RGB float32 [-1,1] | RGB float32 [0,1]，PIQ内部标准化 |

两种输入范围分别符合各自实现，未发现“把0..255直接送入LPIPS”的归一化错误。但不同骨干的数值不能混为同一尺度。官方 requirements 未锁定 PIQ 版本，本次桥接明确固定 PIQ 0.8.0，不冒充作者当时的精确环境。

公开 WC 固定版本 `60a486df6d2e6d2aa3c21815895aac157a88e95d` 缺少部分模型目录，原项目从 NVIDIA `a2c298b0a3df3778b973fe65e9e58877b292d8a7` 补全缺失目录，未覆盖 WC 已有文件。该补全带来了上述 UniPC 路径。[9月30日采样决策](10_SAMPLER_PROTOCOL_DECISION.md)已经明确记载用户选择“先完成当前代码技术对照”，不应在后续口头说明中升级为论文精确复现。此前笼统称“官方配置”不准确，本报告纠正这一称谓。

源码另一个可计算差异：`video2world.py` 将请求35步乘2写入 `worldcache_num_steps=70`；ATS取u=70/35=2，再计算u²/6+u/2+10/3=5。若取35才得到4。这是固定源码与运行horizon的联合推导，身份复核脚本直接执行该AST表达式确认；尚未通过新视频消融测定它对LPIPS的贡献。

官方来源：[论文4.1与表6](https://arxiv.org/html/2603.22286v1)、[固定版本EgoDex评分代码](https://github.com/umair1221/WorldCache/blob/60a486df6d2e6d2aa3c21815895aac157a88e95d/Evaluation/EgoDex-Eval/evaluate.py)。进一步源码追踪：`worldcache_flow_scale` 原样传入 `estimate_optical_flow(..., scale_factor=...)`，用于 `F.interpolate` 的空间缩放，随后流场恢复原尺寸并乘以倒数。因此 README命令的2.0确实对应先上采样，代码默认.5对应下采样；不能把2解释成“.5的倒数表达所以等价”。论文附录选择.5。代码裸默认、README命令和论文是三个不同参数组合，本地用的是README显式参数，不应统称“官方默认”。

## 原件全帧重评分

| 场景 | 阈值 | 原Alex重算 | 官方PIQ/VGG桥接 |
|---|---:|---:|---:|
| av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | .06 | 0.389524 | 0.446071 |
| common_sense_6487f37f-ef57-49ca-afdc-d898922b5191 | .06 | 0.333153 | 0.421124 |
| human_199 | .06 | 0.424745 | 0.468254 |
| industry_084 | .06 | 0.532712 | 0.559247 |
| misc_13398218_3840_2160_60fps | .06 | 0.493993 | 0.510926 |
| physics_045 | .06 | 0.305083 | 0.388536 |
| av_51b45829-502e-4143-9c32-c026bd6ab191 | .06 | 0.394325 | 0.438121 |
| common_sense_6487f37f-ef57-49ca-afdc-d898922b5191 | .08 | 0.408304 | 0.483631 |
| human_199 | .08 | 0.501563 | 0.520514 |

七组.06等场景均值：Alex **0.410505**，PIQ/VGG **0.461754**。两列均以Native为参考，不能与论文的GT参考0.518直接比较，也不能相加。

九对全部完成，16个原视频，837帧对；旧Alex逐帧最大绝对复算差 **2.98e-08**（门限1e-6）。全部帧的mediapy/PyAV RGB逐位一致，PTS一致，原件前后SHA一致，自比较为零，PIQ批均值控制通过；CUDA未初始化、GPU提交0、视频生成0。CPU评分wall **1546.8秒**。

[完整接受回执及逐帧分数](../reports/wc_native_lpips_official_rescore_accepted_20261027.json) · [原任务终态、scope和日志](../reports/wc_native_lpips_rescore_terminal_20261027.json)。

执行代码：[CPU重评分脚本](../scripts/audit_wc_native_lpips_rescore_r1.py)。直接提取固定官方 `compute_metrics` 函数 AST，函数内容不改；用冻结 PIQ 实例替代逐次初始化，并按单帧计算、93帧均值降低CPU内存。两帧批聚合控制验证平均规则。官方 mediapy 解码与旧 PyAV 的全部 RGB 帧必须逐位一致，双方PTS/帧数/尺寸必须一致；不触发官方的裁短或尺寸插值分支。每对读取前后再次验证原件SHA。

## 判断与后续边界

**已确认存在论文复现配置/口径不等价；同时，旧视频相对Native的高偏移也是真实可复算的。两者并存，不能归结为单一评分bug，也不能宣称已证明论文官方设置本身就会偏移0.5。**

1. 数值层面：原件哈希、帧对齐和原评分全部复核通过；没有发现错种子配置、错视频配对或输入归一化造成的虚高。换成官方PIQ/VGG后仍可测到偏移，不能靠更换量尺让旧结果消失。
2. 本地缓存层面：FAIR同批同eval的两场景里，.04→.06→.08对应Native偏移持续增大，支持缓存设置确实影响保真度；human .08约0.502不是拼接错配的产物。对跨批补Native的五组，保留模式等价和完整前向路径对照缺口，不将所有偏移强行归到缓存跳过。
3. 论文复现层面：采样器/实际步数、显著性权重、光流缩放、ATS系数、LPIPS骨干和参考对象均有差异。将旧技术对照叫作“论文官方配置复现”不成立。必须先补同条件因果对照及明确版本的论文配置验证，才可以评价论文设置下的缓存代价。

**决策：保留现有评价标准和历史结果；先修正基线身份与复现协议，不以这批结果为放宽Native保真门槛的依据。**

后续若要识别缓存的纯因果份额，应另建配对验证卡：同进程、同初始噪声实测哈希、同 eval/backend、相同提示词/条件/权重/采样时间步，至少包含 Native、WC wrapper 强制全计算、实际 WC 三臂。先要求前两臂一致，再归因缓存跳过。论文配置比较需单独固定 Euler 实现及完整sigma网格、.08/.12与warp参数映射；不能仅把num_steps改成35就叫Euler35复现。对官方表6还需 EgoDex I2V 输入/真实视频，并同时报告 Native-GT、WC-GT、WC-Native。

本次没有创建可自动执行的新GPU任务，没有改任何旧LPIPS门槛、数据、分母或主线准入标准。新官方评分仅是审计桥接列，不能用它替换旧量尺后宣称原验收通过。
