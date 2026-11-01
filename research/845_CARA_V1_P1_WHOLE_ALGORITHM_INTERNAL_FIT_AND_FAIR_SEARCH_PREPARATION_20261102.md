# V1完整算法、内部FIT评分和公平搜索准备

P0两状态已完整接受，后续开始组成能自动给出19D/22D布局的P1。新生产算法已实现完整64标签、三组固定估值、同DP各top3、完整两FIT选择、选择后的旧CHECK请求及两预算LPIPS搜索。本地33项控制通过；真实Linux加载/独立指标子进程尚待当前新CPU。没有真实V1校准标签、规划器视频收益或P1 GPU授权。

## 完整范围修正

原132路径草案漏计了14个必要预热和控制位置：两预热、四CAL的allD对Native、两FIT的Native与Uniform19计时OFF/ON、两预算sigma父计划在两FIT的四个独立普通轨迹控制。新[完整范围](../plans/cara_next_stage_20261101/source_lifecycle/V1_P1_WHOLE_MANIFEST_R1.json)上限146；保留全部语义槽位，相同策略/输入/seed/clean类别可以共享物理质量和时钟样本，不能把别名当成独立重复计时。

[旧时钟审计](../plans/cara_next_stage_20261101/source_lifecycle/V1_P1_SCOPE_AND_COST_AUDIT_R1.json)仅14条请求约增1.0682GPUh。随后[有界物理费用草案R2](../plans/cara_next_stage_20261101/source_lifecycle/V1_P1_BOUNDED_PHYSICAL_COST_DRAFT_R2.json)进一步按完整搜索/评分上限计算：146语义位置、扣除4个必然复用的初始Uniform视频，最多142物理生成/5176模型pair，最多42双FIT内部查询/84对持卡CPU指标，释放后最多32新增指标。旧请求时钟、31秒/对及未实测启动/IO余量合计10.9158GPUh，20%余量13.0989。它仍不是正式报价或硬限；实际22D、snapshot和宿主broker开销/准入尚待完整接受，不能据此启动。

## 已实现的完整算法边界

- [Collection](../src/wcomr/cara_source_lifecycle_p1_collection_r1.py)为每个物理/拟合/评分/选择操作先写意图；未决或失败只恢复原件。已完成的物理、指标和选择回执不再执行。合成全链及恢复覆盖146语义位置、64标签、六项一次FIT选择、完整CHECK与双预算搜索；真实CPU未接受前不称生产全链通过。
- [新内部评分](../src/wcomr/cara_source_lifecycle_fit_scores_r1.py)和[独立worker](../scripts/score_cara_source_lifecycle_fit_r1.py)只接受同源完整两FIT/93帧原请求，沿用原Fidelity-v2解码RGB/PTS、Alex0.1和PIQ0.8.0的PSNR/SSIM/时序/细节实现。内部指标可供固定算法消费，最终科学接受仍等整卡释放和唯一结算；旧P0/M1释放后评分门不改。
- [新搜索](../src/wcomr/cara_source_lifecycle_search_r1.py)分别19D/22D、Uniform起点，与DP同一合法空间，无额外step24保护。每预算最多12次完整双FIT查询，预定6次SA及1轮至多5邻居HC；费用先到时保留未准入/未到达分母，不声称HC完成。原RGB-MSE/19D搜索控制器、赢家和冻结未改。
- 同费用上限由每预算的一半共享校准/控制、一半主模型估值费用及主模型完整top3 FIT生成/评分/选择的工件并集组成；消融额外费用不抬高主方法额度。搜索先扣相同一半共享参考/预热/计时控制，再计原guardian时钟下的持卡全过程。查询上限与GPUh分别记录；所有原实耗仅由guardian结算一次。
- [loaded入口](../src/wcomr/cara_source_lifecycle_p1_runner_r1.py)和[真实请求适配](../src/wcomr/cara_source_lifecycle_p1_requests_r1.py)保留共享eval、BF16/Wan-FP32、参数/完整状态/PreparedInputReplay、采样器历史和干净双时钟边界。生产费用只接受同launch/source/boot/namespace原guardian的单调时钟，不拿CPU计时定GPU价格。

## 原件和剩余交付

[本地控制回执](../reports/cara_v1_P1_algorithm_local_CPU_component_r1_20261102.json)覆盖固定估值、完整两FIT内部评分、19/22合法搜索、费用停止、半FIT/错误身份拒绝、失败/UNKNOWN及全链无重派恢复。旧R3标量CPU和P0保持，不重放。

原R1 CPU于04:14:07唯一启动，04:17:39退出1。固定源已越过33控制的断言，首条warm Native的夹具writer收到原管线的文件名前缀，却未追加`.mp4`；因此视频工件读回失败，尚未采集来源标签或完成算法接受。[原失败与终态](../reports/cara_v1_P1_algorithm_Linux_CPU_original_failure_r1_20261102.json)保留，不重启。修复只涉及合成writer的后缀契约；新R2使用`scripts/cara_source_lifecycle_p1_linux_cpu_r2.py`，原R1源码和容器保持。

新CPU仅two_card，单核26/4GiB/no-swap/no-network/no-GPU，工作1800秒、退出60秒。它使用原WC/RF globals和实际Cosmos参数执行两种flow的完整tiny算法，并将tiny输出指纹作为显式93×64合成媒体种子运行原Alex真实权重。该媒体与合成费用ticks均非真实模型结果或GPU报价；原进程一旦启动只恢复。

完整GPU入口还需要：持卡期间的宿主机独立CPU容器broker及原句柄接受；原终态/释放/唯一结算后的完整工件与补充指标接受、图表和一次冻结；实际资产/源码/内存/磁盘/独占资源组合及146上限整卡报价。完成后才提交单次>4GPUh与新卡原中央账本事务许可。原P0例外已经关闭，未新增GPU、预约或账本读取。
