# Fast 论文结果入口接入完整 B36

2026-10-30。本轮修复主线结果承接：新增当前结果清单 R2 和只读装配入口，将原完整 B36 分析、图表、CSV 与费用接到论文索引。生产入口与八项本地控制通过，新增 GPUh 为 0。

## 缺口与处理

原 `PAPER_RESULTS_MANIFEST.json` 是启动前 R1，仍有空的 `accepted_batches` 和 `TARGET_ONLY_NO_RESULT`。原通用分析入口要求 `ACCEPTED_COMPLETE/formal_rows`，实际 B36 完整接受使用经过五份原回执重建的 `COMPLETE_ACCEPTED_B36_ANALYSIS`。因此旧入口不能直接消费当前完整结果。

R1 清单及原通用脚本已在六份绘图关键源码内冻结，不能为补一条结果而改写它们。本轮保留全部原件，用 [R2 清单](../plans/cara_next_stage_20261028/mainline/PAPER_RESULTS_MANIFEST_R2.json)作为当前入口，显式引用 R1 的原统计协议。新装配脚本复用原 `verify_analysis` 和角色标签函数，不建立第二套评分、聚合或绘图实现。

当前可读产物为 [Fast19 已接受结果索引](../paper/results/cara_fast_r2_20261030/FAST_RESULTS.md)，机器产物为 [accepted-results.json](../paper/results/cara_fast_r2_20261030/accepted-results.json)。

## 完整绑定

- 重新通过原五份回执的完整分析读者，核对32个正式位置、26份新评分与六份原 A 指标的既有接受。
- 绑定原绘图生产 CPU 的正常终态、输出报告 SHA、原图面接受及六份冻结绘图源码。
- 核对四组 PNG/PDF 与四份 CSV，共12个原导出文件；图表直接链接原件，不复制或重新渲染。
- 八角色摘要保持 T_DD、T_request、Alex、SSIM。T_DD 区间直接引用原 CSV 的20,000次输入簇探索性 bootstrap，不重新抽样。
- 机器索引保留 ALL/FIT/CHECK 全24行、逐输入 PSNR 的 `+inf`、未定义梯度分母及原 FIT A-only 敏感性分析。
- WC/RA 保持 FIT UNMATCHED，Native22 的 MATCHED 仍只指原 FIT 时间选择。四个旧 CAL 的 CHECK 不升级为独立新输入。

费用来自同一份原中央结算的两个 SETTLED 作业：A32 为2.2557055054700728 GPUh，B36为2.384553982338661 GPUh，总4.640259487808734 GPUh，含原预热、等价控制、校准、重复与分配开销。这是原采集的费用披露，本轮没有预约、派发或写账本。

25D 的原 DEV128 只作单独历史开发证据，不与本批合并时间。S/Q 尚无登记在此清单内的新方法接受；F18 保持静态 CPU，Q5/第二骨干/最终确认仍待前瞻范围与新证据。人工审阅没有并入本数值批次。

## CPU 与生产入口验证

[接受回执](../reports/cara_fast_paper_results_R2_CPU_acceptance_20261030.json)记录八项测试，覆盖完整数据与费用保留、原图表链接和禁止覆盖、原区间复用、计划/空/重复登记拒绝、伪改汇总拒绝、CPU夹具或部分结果拒绝、图表原件/源码/图面接受改变拒绝，以及未结束或失败的原绘图 CPU 拒绝。即使更改外层 SHA，伪造的分析仍不能通过原完整接受读者。

实际 CLI 正常退出，生成八角色摘要并绑定12个原导出；全部相对链接可解析。原52份执行、4份汇总、6份绘图源码以及 A32 冻结重新核对保持。没有模型、评分网络、bootstrap 或 GPU 任务重跑。

复现时使用新输出目录：

```sh
python3 scripts/assemble_cara_fast_paper_results_r2.py \
  --manifest plans/cara_next_stage_20261028/mainline/PAPER_RESULTS_MANIFEST_R2.json \
  --output-dir /tmp/cara-fast-paper-results-review
```

输出目录已存在时拒绝覆盖。原 B36 聚合和绘图 CLI 继续作为冻结组件，R2 仅装配它们已经接受的结果。

## 后续执行

下一项可独立推进的主线工作是验证既定 F18-C、F18-A1、Uniform18 的受影响生产 CPU 路径，复用现有 CLI/采样器，不修改原 B36。该 CPU 验证不等待新 GPU，也不代表 F18 整卡已经冻结或准入。

GPU 顺序继续保持 S 优先；待冻结方法、完整物理范围、双端生产证据与整卡报价后再决定下一最小卡。S/Q 的实际 CLI 组合检查仍由原对话完成，本轮未操作其文件、执行句柄或资源轮询。最终输入和额外 seed 未曝光。
