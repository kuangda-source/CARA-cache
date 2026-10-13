# 独立确认完整50路径：生产模板与费用

2026-10-13。承接401完整seed17/43接线240 CPU及394既有独立输入。397原595382e/661仍在最后场景生成，本项只准备独立生产CPU；原算法/参数/数据/范围不改，0新GPU。

## 完整问题与固定输入

四未曝光提示词×seed17/43×Native/RA/A_NO_P/P_OFF/一个冻结候选，40正式；AV28/seed0的五方法各两次完整CAL预热，共10，**50路径/1800pairs/3600CFG、一次加载、0 teacher/训练/人工评审**。每提示词两个seed方法顺序相反、每seed块与整体均平均位置3。没有把预热当独立样本或将50缩成少数成功配置。

候选现在仍是TABLE_PHASE的生产模板，candidate_frozen=false、template_production_CPU_only=true、GPU_execution_selected=false，原protocol/manifest均未改。完整H1结果验收后才选择并另行绑定冻结回执；新输入没有生成或评分，不在确认侧选γ/λ/阈值/赢家。强P_OFF/A_NO_P确认继续保护，不以H2/P执行器成熟为前提。

## 费用与生产CPU职责

[完整50模板费用](../manifests/wc_source_conditional_confirmation_full50_template_cost_r1_20261013.json)预计**6.561346751 GPUh**，以原已测最大Native主时间298.2962秒加每路径60秒算法余量×全部50，再含一次导入/加载、全部写出、失败清理，整体1.25余量。明确是未全实测包络，不是确认已花费或可宣称实际加速；完整范围不按8h门槛拆缩。

[完整配置模板](../configs/wc_source_conditional_confirmation_full50_production_template_r1_20261013.json)复制既有已测source×phase/仅source表、旧γ和真实报价；实际8新请求与单独CAL warmup分别解析，按同一matrix交替。context标签适配只来自401已测核心，采样/算法/计时/价格无新改动。主时间文本编码、去噪、VAE和必要算法维护，加载/额外guardrail/保存/清理单列及全入GPU账本。

新生产校验核对完整40＋10范围、输入原件/暴露/保留E2组/参数/全50费用hash、实际命令、旧root C排序价与新plain-C分价、真实seed/guardrail/无训练无teacher；没有冻结回执时GPU准入明确拒绝。CPU模板通过也不能当作已冻结候选的实际GPU生产CPU通过，最终候选/版本要重新封存精确入口。

当前新生产模板代码已编译，复制原401 source8b845b3/651及其全240结果后，在独立目录仅运行CPU。现时生产CPU/最终40×93评分入口/GPU均待；不会创建确认视频或修改账本。397当时30/36生成回执，最后场景在跑，全部原件/正式24×93/终态与实际账本尚待。

## 接续

先验收397全量结果和九对照；400 teacher270卡已生产CPU就绪，可串行回答目标对齐。402模板减少确认准备延迟，真正冻结后全量确认已有主干与候选。继承≤8自主/严格>8按整卡确认、现fresh48余额与单昂贵GPU任务；原E2完整76和用户暂缓P13h身份/权限保持，无预算重置。

## 生产模板CPU完成

原401已测651核心按hash复制，新生产模板sourcefb5ba49/671全部保持。CPU541058已结束，实际8＋CAL warmup请求解析、全50矩阵与3600CFG范围、数据/参数/费用/资源、真实child-command/hash与变更拒绝通过；未有冻结回执的模板明确拒绝GPU准入，CUDA未初始化、0 GPU/账本写入。见[实际模板回执](../reports/wc_source_confirmation_template_r1_production_cpu_receipt_20261013.json)。

本通过状态专门记为`SOURCE_CONFIRMATION_TEMPLATE_PRODUCTION_CPU_PASS_CANDIDATE_UNFROZEN_NO_GPU`。它不能转为真实已选确认候选的GPU门通过；原protocol/manifest和新配置的candidate_frozen=false均保持，最终选定后另冻结准确回执/生产字节再验证。当前只减少接线和费用准备延迟，不生成确认视频。

397最新现场33/36（12warm＋21正式）生成回执，原三个handleslive/661保持，最后场景A_NO_P在跑；全部原件/24×93/控制/独立科学结论仍待。400完整270生产已过保持，依397全量验收后串行安排；本轮未新GPU、现预算不重置。
