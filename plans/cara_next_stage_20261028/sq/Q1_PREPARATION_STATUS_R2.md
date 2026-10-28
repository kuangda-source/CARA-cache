# Q1 读出准备 R2 与下一最小验证

2026-10-28。受影响的CPU路径和固定源码条件类恢复已接受；**真实加权C重放、codec输出增量、部署缓存/峰值/速度均未接受，GPU_READY=false**。[接受回执](../../../reports/cara_sq_q1_dual_cpu_accepted_r2_20261028.json)。

## 本轮已完成

- Q1八角色执行器：原C、FP32 M变换回转C、I/M各三个固定bit组合；先核对原C逐值相等，失败则停止codec评分。每点私有输入、模型/solver/RNG恢复，q_total、q_codec和交叉项分别保留。完整12状态后才允许留一prompt和最终共享方向选择。
- 本地及两端各10项小张量检查通过，包括完整96个正式C pair的fixture矩阵、原C漂移拒绝、错误恢复、完整Video2WorldCondition类定义和S共同语法。head/teacher为明确fixture，不是Cosmos数值结果。
- A6000：重新核对B1的32文件SHA，12个真实状态的条件对象字段、Enum、tensor dtype/引用及严格过去锚点恢复通过；没有生成新状态。
- 双端：4,118,575,006 B固定checkpoint的SHA均为`565bbb2c9645737327983f4461e4d32627bba465b0a8dc26447edea144e1ff47`，与已接受WC73资源回执一致；三块final-layer tensor的shape/dtype/SHA也完全一致。仅只读mmap与元数据，不执行head、不构造完整模型。
- S：在新父数据产生前，将共同语法绑定到已有生产profile（max-age28）。D24额外保护保留为S设计限制；170个结构候选。旧6步诊断接口及158候选回执保留，尚无完整108标签或真实S掩码。[支持域修订](S_SUPPORT_RECONCILIATION_R2.json)。

## 已定位并保留的工程失败

两端R1都在GPU隐藏时，因完整条件模块连带导入Qwen后触发FlashAttention可用性断言退出。双卡容器墙钟25.70 s、四卡297.66 s，实际进程CPU未完整计量；分配vCPUh上界合计0.17964。没有GPU、模型执行或资产采集，原stage未修改或重派。

R2复用仓库已有的完整固定源码类定义编译器，验证真实序列化字段恢复；原模块的CUDA关联导入仍单独记为未通过，未伪造CUDA可用性、修改上游或安装依赖。此边界不影响已经完成的源码类定义/字段检查，也不能被称为完整CUDA导入接受。

## 资源

| R2 | 容器墙钟 | 进程CPU秒 | 峰值RSS |
|---|---:|---:|---:|
| 双卡 | 121.78 s | 95.53 s | 0.815 GiB |
| 四卡 | 309.85 s | 47.41 s | 0.810 GiB |

成功轮实际进程CPU合计0.03970 CPUh；分配vCPUh上界0.23980。两轮均为2核/8 GiB、禁网、GPU隐藏、原件只读，成功轮正常退出。源/运行时SHA相符；新增GPUh、预约和ledger写入均为0。本地编辑、SSH、staging与Git CPU未完整计量。四卡没有B1 raw，未传bulk、未声称四卡已做真实B1字段恢复。

## 下一最小验证：完整读出子图

原`ReadoutKernel._run('C')`使用已保存的current o/probe、历史p/r窗口、embedding/adaln和pair条件，调用原C/warp、`final_layer`、`unpatchify`与RF。该路径不调用deep blocks；其可训练参数仅为本轮已核对的三块head权重，checkpoint BF16合计3,407,872 B。源定义与资源足以先准备精确读出子图，完整模型生成与部署仍是另一个范围。

下一步实现并检查这个子图的权重/精度/原C数值控制，先用预定AV28 step22做CPU边界核验。**没有原C一致性证据就不评分codec，不修改容差来通过。** CPU与原A6000输出的后端差异若存在，原样记录，再用另冻范围的同硬件GPU重放解决。不能由head权重少推断总显存、部署速度或新GPU报价。

Q1的96正式pair分母保持；完整GPU卡还须逐项加入预热、数值控制、重复、编码/传输、I/O、加载/释放和失败余量后冻结报价。S公共采集仍需生产父轨迹hook及pre-D shadow-C、OFF/ON完整控制；无新GPU卡已获准。

## 总缓存分母的新增明确缺口

实际生产`GuidedW1Readout`还在`ResidualCalibrator.observe_full`克隆并保留两份true-D p/r锚点。除native三项窗口、previous输入/输出和solver外，**readout/calibrator/owner持有的tensor及其storage别名也必须清点**。仅统计`net.WC_FIELDS`不足以证明部署省显存；CPU packet比不替代这一分母。

A-SQ-FAST的轻量运行时元数据提案据此包括这些owner；不新增Q25 raw。部署codec不得同时保留用于逃避实际压缩的未压全精度影子。

## 长程检查

后续每张获准GPU卡用唯一launch的实际开始时间和完整ETA安排一次半程与一次终态验收。半程只检查运行身份、数量、健康、资源/锁/温度/账本，不读取部分科学成绩调参；终态收取原始输出、退出/释放/独占与准确费用，完整接受后再分析。ETA变化更新既有检查，不重复派发。本轮没有GPU launch，因此没有创建虚假的未来检查。
