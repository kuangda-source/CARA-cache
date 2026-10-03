## 2026-10-03 最新文档核对 — 完整104点成本与实施阻碍

[完整104点成本核对](../../research/74_WC_FULL_COVERAGE_COST_AND_BLOCKERS_20261003.md)：r3仅call25/26×layer2的2点技术门，r2全104点输入/状态控制失败仍不追认。独立补验需保留共享官方prepared-input、完整RNG及全部九门，step13/18和全26深层。两次实测推算全cost1198.90–1216.65秒，20%规划包络1459.98秒，超现1200秒/child1170秒准入；包络不是实跑必然超时证明。累计余7.609536141569778GPUh足够不代表单卡时间授权。

新实施文件写入被自动审批按本次可信docs-only指令拒绝；草案未入库/部署/实际CPU验证，未GPU提交，新增GPU成本0，已用4.390463858430222/12h、31jobs不变。待实施与时间门得到明确解决后才继续有效coverage→H0→H1；不自动延窗、开多窗、复跑r2或启动RV/训练。以下旧段为各时点历史快照。

# worldcache-omr-experiments 短接续说明

## 最新执行授权 — 2026-10-03

[各项目累计12GPUh与恢复后队列](../../research/BUDGET_AUTHORIZATION_20261003.md)取代此前仅文档及旧预算限制；保留已用与历史账目，单昂贵任务，GPU优先WC。WC已用3.9117525685110333GPUh、28jobs保持，当前余额8.088247431488967GPUh。先中间刷新/全26深层覆盖准备和无扰动诊断，再H0互补性、H1来源×寿命；W1/replay已完成不重跑，RV后置。旧new4h/clean50不自动转为新队列。新runner须按明确12h权威账本校验，不能重新执行硬编码4h的旧launch。 下述2026-10-02原包适配/仅文档条目为当时快照。

对应现有置顶会话：**WorldCache 研究与实验推进**；ID `01a0f1eb-7894-7ed0-a186-d010111e14b1`。实际 checkout：`/Users/kuangda_gao/Documents/世界模型加速实验/worldcache_omr`。

本轮接续范围：只读取和整理文档，不运行实验/CPU研究/资源探测/下载模型/训练/评分，不改部署、Clash 或冻结协议。先读 [AGENTS](../../AGENTS.md)、[总览](../../EXPERIMENT_REPORT.md)、[状态](../../research/02_CURRENT_STATE.md)、[队列](../../research/09_NEXT_ACTIONS.md)、[交接](../../memory/handoffs/LATEST.md)，再看 [原包适配与编号映射](ADAPTATION.md)。

当前入口：WC-S/H 中间刷新与全 26 深层覆盖准备 → H0 → H1；W1/W2 扩展暂停，RV 为条件 DESIGN_ONLY。

保留现有配置、失败、预算与结果；不重跑已有兼容证据，不从包中建议值推导许可。任何未来运行都须另读其具体获准范围。原包 05 的通用模板不在本轮触发执行；沿用现有 memory/reports/manifests，不建第二套 ledger。
