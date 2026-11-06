# 完整公平基线入口：Native/少步/三WC工作点与阶段候选CPU通过

2026-10-04。承接[103在线八输出终态](103_WC_ONLINE_STAGE_RESULTS_AND_FAIR_BASELINE_NEXT.md)，本轮补齐完整生成的公平比较核心，不再只检查scheduler网格。当前**CPU接口与原件/源码独立审计通过，尚未新GPU卡选择、执行或预付**。累计仍9.691073425147268/12GPUh、43jobs，余2.308926574852732h，无inflight。

## 方法与完整对照

[工作点声明](../src/wcomr/fair_workpoints.py)、[完整请求核心](../src/wcomr/fair_sampling.py)、[十四输出组合](../src/wcomr/fair_output.py)。每个曝光CAL固定保留六点：Native35请求/36实际更新、Native23请求/24实际更新、WorldCache阈值0.04/0.06/0.08（35请求/36实际）以及CAL选定的stage every1（WC0.06、窗口23–27）。少步只改采样步数，WC三点只改rel_l1阈值；其余输入、模型/权重、seed/guidance、93帧/分辨率、模式/精度、offload和guardrail设置共享。新对照不会删原生少步或调阈值WC以凑优势。

WorldCache会把网络实例的 `forward` 替换为缓存方法。**只把 `pipe.worldcache_enabled` 设为False不能得到Native**。新核心绑定固定官方 `MinimalV1LVGDiT.forward` 类方法，并执行其继承的 `MiniTrainDIT.forward` 完整路径；Native开关关闭、所有deep调用必须执行，不能以负阈值的WC“强制full”冒充Native。用于逐臂初始化的WC状态重置发生在生成前，随后立即恢复官方Native方法；Native生成不调用probe、Gamma、warp或缓存近似。

每臂复制样本并只修改num_steps，原35步样本不变；恢复共同入口RNG、重置buffer，真实prepare一次。官方request reset与完整UniPC负责35→23→35网格/solver历史重置，不能沿用Light入口硬编码36/72来误验Native23。三WC点必须保留实际声明阈值，stage继承原生full/cache反馈，无未来掩码、固定deep或S配额承诺。

完整组合先两输出strict WC D/D，再两个CAL各六工作点，共十四输出。D/D九门和完整pipeline不符即止；WC0.06历史输出桥在stage之前核验，错误不继续stage或下一请求。失败保留十四分母、已完成请求和产物，不替换输入。共同mode/参数和buffer、Native/WC开关、阈值设置、forward及全部观察挂钩在返回/异常时恢复。

测量仅保留首/末block计数、完整pipeline几何与必要stage来源/核检查，不在六工作点加入逐前向张量哈希或checkpoint复制。完整generate在CUDA边界同步；各子阶段host wall不当作独立CUDA延迟。逐臂实验配置/状态初始化与文件SHA在generate wall之外，整卡GPU费用将包含它们、模型加载、失败、flush与释放；CPU wall不能当GPU成本或加速。

## 当前实际CPU证据

[当前r3](../reports/wc_fair_sampling_cpu_r3_20261004.json)，实际Cosmos Torch2.7.1+cu128，**64.099950秒**，禁止CUDA初始化、没有模型权重/实际稀疏核。[独立原件/源码审计](../reports/wc_fair_sampling_cpu_audit_20261004.json)逐SHA绑定服务器原始回执、30份当前依赖和7份固定官方源码，两个Native forward的规范AST也一致。服务器原件SHA `e593ccf79d760dde8d35df24c6542e10c340159978975b0227e5c6d142f47cda`。现场预算与CPU前一致，无GPU提交或预付。

当前14组控制包括：

- Flow OFF/ON各一组六点完整采样。实际CPU更新序列36/24/36/36/36/36，CFG72/48/72/72/72/72；全部真实函数体prepare一次，Native每次deep执行，三阈值与stage0.06被保留。
- Native35、Native23分别与**直接调用官方类方法和普通生成路径**的CPU参考比较：全部prepared输入、逐前向命名输入/输出张量、最终latent、解码张量、RNG与mock文件逐项相等，避免只凭饱和mock像素碰巧相等。
- 两个完整CAL的十四输出组合，D/D全部九门/完整pipeline、六点全覆盖及WC35→Native23→WC35状态重置通过；历史桥完全复现的组合也通过。
- D/D解码不一致、第二CAL的Native23写入失败、错误Native23 scheduler网格、错误历史WC桥均拒绝；前序输出与原分母、forward/hooks/buffer/开关/阈值恢复断言通过。
- 每Flow四种非法工作点分配（少点、可变列表、bool步数、错阈值）均在生成前拒绝。

[首轮r1](../reports/wc_fair_sampling_cpu_r1_20261004.json)24.385秒验证六点核心；[r2](../reports/wc_fair_sampling_cpu_r2_20261004.json)64.331秒加入十四输出组合。之后补强Native失败时的配置恢复断言并重跑r3，**当前30依赖以r3及其独立审计为准**，不追认旧回执覆盖后来的代码。三次CPU均预算不变，没有GPU费用。

CPU保留了七份固定官方文件中的原函数体，包括Native LVG/base、Sampler/get_velocity/denoise/decode wrapper、UniPC、WorldCache、generate_vid2world和Inference；类构造、mask/patch embedding、位置参数Toy block桥、归一化/conditioner/广播、tokenizer/decoder/writer及稀疏核为明确CPU替身。本toy stage出现10个S call不是两个真实CAL的配额预测。该证据不能证明实际权重的Native GPU parity、编码视频质量、物理行为或稳定速度。

## 下一张卡与尚缺证据

公平十四输出具体GPU scope/runner/监督器、完整十四视频来源与Native相对全部十候选指标、费用/释放审计仍须单独具体化。先绑定当前r3原件与30依赖、实际官方source/prepare/native-meta与Native方法origin、asset/import/package、两实际条件及历史WC视频；冻结source同步GitHub后，再fresh UUID/sm86/VRAM/compute/f1锁/no-inflight/12h账本/磁盘准入，只提交新身份一次。现有104点和在线八输出单次卡不重提。

[99成本草案](99_WC_ONLINE_STAGE_CPU_AND_FAIR_FRONTIER_BUDGET.md)保留full代理和完整矩阵，fair14拟6300秒、后续CONF6拟3000秒当前不能共同准入；下一卡实际结算后重算后序余额，不按Native23步数线性折扣成本。若仍缺资源就报告缺口，不删除基线、改CONF定义或重置预算。

Native GPU完整输出/独立parity、实际公平质量—时间数据、独立CONF、重复计时和语义/物理评价仍未成立。every1只是CAL选定的公平候选，先比较简单少步和调过WC，再决定是否值得深化稀疏/刷新或学习Head。当前继续WC，自主科学goal active，不训练、付费评分或新增人工评审。
