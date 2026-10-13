# 冻结H1：独立确认完整50路径最终生产登记

2026-10-13。接续403完整H1、404候选冻结与401/402完整CPU。当前只准备最终生产及服务器CPU验证；原teacher GPU任务继续，不取消、重启或并发确认GPU。

## 1. 实验问题和完整范围

确认已冻结 TABLE_PHASE_H1、A_NO_P 和 P_OFF 在新提示词/不同初始噪声上的保真与实际成本；Native 和 RA 是保留的完整对照。主候选是高保真工作点，不能以当前比RA更贵取消其确认；本卡也不单独证明匹配成本优势。

四个已提前固定的新提示词 AV46、Human125、misc2711212、robot043，各 seed17/43，五方法 Native/RA/A_NO_P/P_OFF/TABLE_PHASE_H1，**40条正式路径＋10条CAL seed0完整预热，共50路径、1800pairs/3600CFG、一次模型驻留、40视频全93帧评分**。两个seed镜像执行顺序，每个提示词和总体五方法平均位置相同。输入选择和原protocol/manifest不改，不替代或转用E2完整76及用户暂缓P13h。

冻结回执绑定完整开发结果和原source595382e，来源×阶段方法fingerprint34ef948e、lambda525.1463509809399及原gamma/费用/保护/支持域/当前P执行器保持。不按场景拼赢家，不根据确认终点、teacher或新seed调参；无训练、在线teacher、head省算或人工评审。

## 2. 从已验收模板到最终生产

原fb5ba49/671 CPU-only模板与8b845b3/651完整240种子CPU保持原身份。新最终stage复制全部已验收文件，再追加独立最终配置、冻结回执和生产/评分程序。采样、缓存、读出及主计时仍执行原seed入口与开发方法；最终runner从GPU环境断言至完整50采样及清理的代码，与已验模板逐字相同。只改变候选封口/生产路径及CPU、post绑定，不因本地缺torch修改算法。

新配置[full50最终生产](../configs/wc_source_conditional_confirmation_full50_production_r1_20261013.json)明确candidate_frozen=true、template_CPU_only=false，但仍未选GPU。旧模板保持未冻结禁止GPU。验证逐个核对freeze的源码、参数、开发分析和输入hash；真实CPU使用同一最终supervisor构造实际child命令。所有50实际seed身份、完整更新/计时边界、自动post目录和完整评分范围必须验收；旧模板CPU通过不是本卡最终CPU通过。

## 3. 终态评价及必要控制

全50位置保留，全部接受视频逐帧完整解码，原始终态有限性/hash/形状核对；拒绝、缺失和技术中断均保留原位置，不补零、不补挑样。十个预热检查五组重复final/动作/93RGB，同时对照403同一CAL的五个原验收输出。Native没有缓存动作所有者，actions=null，不虚构DD列表。

全部可配对的40正式视频，用**同一提示词且同一seed的Native**评分93帧。先对每个视频聚合，再对一个提示词的两个seed聚合，最后四提示词等权；保留全部八请求/seed配对、正负帧数和最坏状态。缺一个seed的提示词不得进入完整两seed主均值；报告固定分母4提示词、8请求seed、40视频，不把372/744帧算独立样本。

六个固定对比：H1/RA、H1/A_NO_P、H1/P_OFF、A_NO_P/RA、P_OFF/RA、P_OFF/A_NO_P。记录实际主时间、每输入seed的基线÷候选倍数、完整动作/读出/来源及额外head。单配置输入seed一次正式计时不是稳定重复测速；物理/语义质量不由LPIPS替代。

CPU分析检验包含有益和有害提示词、ratio-of-means与mean-of-ratios区别、缺seed不输出完整均值、wrong-seed/wrong-context/wrong-reference/缺帧/错误均值/在途状态拒绝，以及实际watcher目录与完整评分命令。数值采样仍由已接受完整两flow240路径证据覆盖，不把synthetic统计fixture当真实确认结果。

## 4. 费用、执行顺序与当前状态

[最终完整费用](../manifests/wc_source_conditional_confirmation_full50_final_cost_r1_20261013.json)仍为 **6.561346750690589GPUh**，50路径各完整计算包络，包含一次加载、导入、所有预热/正式、写盘和失败清理，再乘1.25余量。部分费用是保守allowance，不伪称全部实测。严格≤8依用户授权；单次完整卡不得拆缩规避阈值。

目前原teacher4b18478/665、563522/563676/563523仍运行，GPU和kernel由其持有，全部teacher终态/自动CPU未结束。新卡先在独立stage进行最终CPU，之后等待原teacher全GPU与CPU终态、原handles消失/锁释放和实结账本，再单次准入。即使GPU退出也不在其CPU评分中途启动下一卡，防止改动原post的账本身份。

提交teacher前实际68.668097882/cap104.971363333/余额36.303265451；在途used=cap是预留，不是已花完。新确认尚0GPU。原模板本地测试遇到默认Python无torch，已记录为环境缺口；源码语法通过，使用既有服务器pinned Python/Torch做实际CPU，不新装依赖、不把环境问题当方法负结果。

该卡不取代固定mask/匹配成本归因、稳定测速和P真实profile/单覆盖轴；这些工作继续按403保护资源。确认不是等待所有机制解释完的门槛，teacher对照也不是确认是否允许的新增科学门槛。

## 5. 最终服务器CPU已通过

实际生产CPU565611现已结束/PASS；独立最终stage source `e48ba58047b09507ea6f438f5077ebffb4fb2114` 的 **684文件**全部保持。实际最终supervisor构造的child命令、完整50范围/八请求/17与43/冻结fingerprint/原输入和参数/资源及变更拒绝通过，CUDA未初始化、0新GPU/0账本写入。

[最终生产CPU回执](../reports/wc_source_confirmation_final_r1_production_cpu_receipt_20261013.json)同时接受实际watcher配置派生的run目录与post命令。四提示词×两seed的签名统计fixture保留正例和有害例；缺seed不输出完整主均值、错误上下文/seed/Native参考、缺帧/错误均值/在途状态均拒绝。所有50 GPU执行分支与旧已验模板逐字相同，原240数值CPU核心hash继续保持；本次统计fixture不是新的科学终点证据。

[最终只读回执](../reports/wc_source_confirmation_final_r1_live_or_terminal_capture_20261013.json)确认无本卡runner/GPU-launch、原CPU已消失、所有684hash正确。**完整确认GPU仍未执行**；费用6.561346751GPUh和完整50范围不变。当前原teacher唯一GPU继续，下一按原CPU和GPU都结束的真实状态串行准入，不改冻结文件或重做已通过的CPU。

最新真实teacher已完成2/4组父路径及对应后缀；原三个handles仍live、665保持、GPU18054MiB/kernel持有。全部四组/12原件/93帧与终态结算仍待，不据半卡报告方法结论。最终确认现可在满足串行条件后单次运行 `python3 scripts/deploy_wc_source_confirmation_production_r1.py --launch`，使用原e48ba58/684，而不是后续文档commit或CPU-only模板。
