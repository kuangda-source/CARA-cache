# 修正P创建目标的完整256 CPU已顺序部署

2026-10-10。新验证已按785f8471b6e6e443e1b1b46a7f61ce7bf60ba646一次部署；服务器独立stage为`.sync/wc-current-birth-sampling-cpu-r1-20261010`，监督3999876。现场1791624114.344627状态为`CURRENT_BIRTH_CPU_WAITING_ORIGINAL_WORKING_FULL256`，新测试子尚未启动；原4a7dfe3监督3977159／测试3989547均存活。不是完整CPU通过，也没有新的GPU或视频结果。

314份冻结载荷、driver、注册及实际runtime哈希均核对，原276份文件保持。注册SHA `5cc71013ce230179732ac5e3197214579a166747c2ccd6fae96c3da5950dfedb`，driver SHA `8afcf6d6f28aeaaf619d4911edabdbd056561a35f6be7325a11097e2cf6a7a69`。独立监督等待原完整256任务exit0、原PID消失、结果SHA和完整范围成立后才启动重CPU；原任务未改、未取消、未重复提交。当前GPU compute为空、预算SHA前后保持，新增GPU提交0、未获取GPU锁或写账本。

新完整范围仍是两规则各保留原128：256×36／9216更新、18432普通net、4736成功张量重新读取、16 full-GEMM参考、1024健康恢复；保留原32变异、12工作周期变异、四截断和四末写出故障，另12当前P／后续C目标变异。创建时支付正P经验floor，后续C保留floor＋借用漂移；真实D历史、两工作周期、阶段A、保护步和连续P上限保持。

新64脚本CPU已通过，P动作0→240是目标对齐与路由可选性证据，仍用固定D6包、不是真实自适应P或终点收益。原完整32的阶段W1／β1四CAL保真正结果保持；完整成本结果P整组约1.29%费用降低保持。下一顺序捕获原完整CPU、新完整CPU，核对全部张量／4032决策，再接实际参数、生产CPU及完整真实视频卡；严格>4GPUh的完整预测才需确认，不拆卡。无训练或额外人评。

飞书组会文档已revision59→60；197顶层块全文核对，只更新绑定进度段，其他内容保持，没有发送消息。证据为`reports/wc_current_birth_sampling_cpu_r1_launch_20261010.json`、`reports/wc_current_birth_sampling_cpu_r1_sequence_observation_20261010.json`及`reports/wc_current_birth_target_and_full_cpu_feishu_20261010_verification.json`。累计37.676066656/77.895246590，新48窗口余40.219179934GPUh，goal active/progress。
