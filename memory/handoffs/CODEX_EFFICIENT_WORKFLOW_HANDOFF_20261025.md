# Codex 交接：高效实验流程 R3

2026-10-25。新卡同时准备四卡SM89和两卡SM86兼容profile，共用科学manifest；启动时默认四卡，四卡无合格空闲卡才选两卡。双端各自验证受影响生产路径、资源、存储与报价；单一中央预算包、跨主机单次提交，原预算与GPU授权边界不变。详见[执行流程第7节](../../docs/EXECUTION_MODES.md#7-双服务器准备与启动选择)。最小入口尚不实现自动选机，不能把模板当作启动证明。

**CAL66已完整接受：66路径、48组LPIPS、156质量评分齐全，4.776207536318 GPUh已中央结算，GPU/原进程/容器/锁全部释放，模式恢复Default。原半程和终态检查均已删除。按冻结合同选择Shared25-C，准备新DEV；新GPU未授权。见[702](../../research/702_CARA_CAL66_A6000_COMPLETE_RESULTS_AND_FROZEN_SHARED25_C_20261026.md)及[冻结文件](../../manifests/cara_CAL66_selected_CAL_candidate_r1_20261026.json)。旧launch保留，禁止Ada或A6000重复启动。**

历史链保持：[698原R1失败](../../research/698_CARA_CAL66_EARLY_FAILURE_TECHNICAL_AND_FINANCE_20261025.md)、[699冻结参数修复](../../research/699_CARA_CAL66_FROZEN_ADAPTER_REPAIR_CPU_ACCEPTED_AND_RECOVERY_QUOTE_20261025.md)、[700四卡R2待空闲](../../research/700_CARA_CAL66_R2_BOUND_CPU_STORAGE_AND_IDLE_GPU_ADMISSION_20261025.md)。这些历史等待/检查安排不能再触发启动。

## 先读与权限

先读 [AGENTS](../../AGENTS.md)、[执行流程](../../docs/EXECUTION_MODES.md)、[问题队列](../../plans/QUESTION_QUEUE.md)、[当前状态](../../docs/project_status.json)、[CAL66合同](../../plans/cara_policy_generator_20261020/CAL66_DESIGN_AND_DECISION_CONTRACT_R1_20261025.md)。交接中的状态是保存证据快照；如已有更新终态，优先复用新原件。

## 本次已完成

1. 流程采用按变更验证、复用接受证据、事件式文档；“两次失败/一天”是复盘触发，不是全面停工。默认前后两批提交，必要修复不受硬性次数限制。聊天中的明确授权有效，无需再签名。
2. [固定48组增量审计](../../reports/cara_new_input_pool48_delta_r1_20261025.json)范围内未发现新增执行证据；沿用16新DEV、16最终确认、16备用，不重新选池。原源文件/来源组及历史审计绑定已核验，首次使用前仍需增量检查。它不是GPU准入，也不证明未覆盖机器上绝无使用。
3. [最小入口](../../scripts/run_card.py)只提供离线validate/plan，以及白名单内既有句柄的recover/capture/accept。无prepare/launch/retry；原监督、计费、StorageGuard和接受器不变。[用法](../../cards/README.md)、[本地CPU边界测试](../../tests/test_card_workflow_r1.py)。本次没有通过新入口连接或接管CAL66。

## 后续按顺序

- CAL66已完整接受并按原合同冻结Shared25-C；Q1完成。Shared24/25-C通过，四个含A候选因相对Native MUSIQ界失败；不改α或筛查阈值。
- 按已冻结Shared25-C、S25-A参考和Native26近时间对照，准备六角色并重算完整128请求（96正式+24重复+6warm+2控制）的报价；旧保守估计12.778311 GPUh超过12h子池，不把粗估当批准。累计226和最终部署上限不变。
- 新DEV用冻结池前16组，最终确认另外16组隔离。执行前增量曝光审计；DEV用于选择后不再是最终TEST。不使用BANK24六DEV替代。
- 新卡在两端分别为改变的路径补CPU验证和必要适配，复用未变组件证据，准备各自完整报价；实际使用前曝光审计覆盖两端。最小入口不提供新GPU派发权限；新报价/卡仍按既有授权边界处理。

## 不再沿用旧交接的做法

不要求每卡重新造独立CPU卡，不要求实现完整通用启动框架后才能做科学工作；不把探索结果一律排除论文；不将所有计时重复或桥接因指纹相同删掉；不把点估计预算可行写成95%上界确认；不因普通修复重复请求已有授权。

旧流程的未签署探索自主额度未生效。本R3不授予额度，不追溯改变CAL66或历史失败。
