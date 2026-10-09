# guided-W1 输出接口：β=1、联合监督与共享读出

2026-10-10。接续[213共享α格点与真实源码映射](213_WC_GUIDED_W1_CORE_AND_PARTIAL_MLP_SOURCE_MAP_20261010.md)，新[输出核心](../src/wcomr/cfg_guided_w1_outputs.py)实现β=1残差对照、两分支共享α输出融合以及直接guided速度向量的矩统计。输入坐标明确为原RF denoise完成条件帧处理后的FP32 BCTHW速度；不把hidden融合当作相同操作，也不从PaidProbe标量恢复速度。

在线共享读出只有原速度、提议速度和冻结α，没有teacher参数；α=0/1保持原对象和精确端点，α=.5按速度输出融合。离线监督直接形成eg=8ec−7eu、qg=8qc−7qu再归约，保留逐分支误差诊断；FP32输出向量的乘积在FP64归约，供既有场景等权格点器使用。β=1严格使用当前浅层增量与调用者提供的过去真实D锚点，不更新缓存、拟合器或锚点。

[新CPU登记](../manifests/wc_mf_a_output_core_cpu_r1_preregistration_20261010.json)及[必要控制](../tests/check_cfg_guided_w1_outputs_cpu.py)覆盖实际Torch张量、原RF源码全文denoise的四种条件帧／时间处理（每种六次调用）、分支改善而guided退化、输出与非线性hidden融合不同、精确端点、输入／版本／RNG保持和七种拒绝。受影响源已AST／compile通过，真实服务器CPU尚待；原格点控制和采样内核不重复跑大矩阵。

这些张量为小型受控输入、RF net为显式提供输出的CPU替身，不能说成Cosmos教师、真实CAL或模型收益；接口本身也不证明输入teacher来自同一状态。下一真实采集仍须四CAL场景AV28／Human／misc／AV51各两合法起点，绑定实际v0／vβ1／vW1／vF、条件、原生warp／head、严格过去D与自身轨迹，再接共享α完整视频。旧仅保存标量误差或RA guided父输出不足，不能补造缺失候选速度。

R2 source384f032／229源保持，原GPU3876022／3876094、后CPU3876023与评分3876501继续原作业；本接口用现有Python环境独立CPU目录，不获取GPU锁、加载权重、写预算或新增GPU。预算若在CPU期间变化，必须区分原GPU真实结算与CPU本身没有写入，不要求暂停原生成。
