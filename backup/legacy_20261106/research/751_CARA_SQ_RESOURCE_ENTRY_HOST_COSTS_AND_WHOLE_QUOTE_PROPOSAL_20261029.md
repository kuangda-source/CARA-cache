# S 资源入口双端接受、主机成本与整卡报价草案

2026-10-29。[本轮综合原件](../reports/cara_sq_s_entry_and_cost_readiness_r1_20261029.json)完整保留四个原CPU容器及独立接受：新增资源入口使用源 `b9b06def44363ea97261dde1e7b7c93ef4d5c1e9`，固定合成CPU成本使用 `471eebb1cf9decc49b4f4de5666f75f479b38fc7`。全部原容器及CLI已退出0，没有重派、真实S标签、新视频、GPU提交或中央写入。

资源入口只增加目标事务首个诊断snapshot之前的元数据拒绝，原数值采集器和物理矩阵保持。每端13项控制、两种flow共216次目标检查、280文件重读及每flow四组完整OFF/ON通过；A6000的18条矩阵路径与两条独立tiny OFF源准备单列，Ada20条新路径。两个schema/source-proof及完整复制计数均独立核验，每端拒绝11类错误回执。原full2B meta和93帧默认合成解码控制按原SHA复用，没有重跑。入口异常后恢复原collection全局，未知shape/dtype/字段、meta、view backing超限和CPU/真实范围混用均拒绝。

原GPU协议需保留同状态、来源、owner及完整物理状态的指纹/恢复，不按视频均值掩盖该校准开销。[工作量与完整工程allowance](../reports/cara_sq_s_work_inventory_and_whole_quote_proposal_r1_20261029.json)按原代码两个restore-and-verify推导每成功目标3次物理指纹、7次owner指纹、3次输入和3次past-source指纹；BF16情景累计约1.988TiB受保护状态逻辑hash访问，不表示独立分配或实测GPU传输。

固定128MB合成BF16 CPU tensor，每操作一次warmup与三次正式，另计setup digest；没有真实状态或权重。原tree_digest包含CPU finite扫描，三次正式中最慢观测对应A6000主机约182.06MiB/s、Ada主机约142.63MiB/s。原data_record clone、deepcopy及内存BytesIO序列化同时测量；GPU finite/传输/前向和真实SSD速度仍未测，不能把这组CPU数据当作GPU原生价格。每端12正式+4warmup+1setup完整，8类错误回执拒绝。[双端CPU成本原件](../reports/cara_sq_s_entry_and_cost_readiness_r1_20261029.json)。

## 未冻结的整卡工程草案

| 主机 | 新路径/复用 | 原BF16情景预测 | R1允许FP32特征的保守情景 | 硬限提案 |
|---|---:|---:|---:|---:|
| A6000 | 9 / 1 | 7.779722GPUh | 12.520000GPUh | 14GPUh |
| Ada | 10 / 0 | 9.231111GPUh | 15.042500GPUh | 17GPUh |

两端都保持十个逻辑角色、108真实标签目标、56额外Dense及52额外C、八raw和24去重锚点。完整草案计入模型/辅助加载、全部物理pair、CPU全状态hash、CUDA搬运与contiguous materialization、snapshot/owner复制、raw转换/序列化、SSD落盘重读、独立视频见证、主机模式/容器/释放，以及25%失败余量。CPU基准采用最慢正式重复；每pair12秒、1GiB/s GPU-to-CPU、10GiB/s设备复制、128MiB/s私有SSD等均为显式未测allowance。所有情景是工程预测，硬限尚未冻结、GPU readiness与native价格接受均未形成；不能据此自动预约或启动。

同一f1 setup所有字段与S执行身份逐项相同，因此登记了兼容的20项模型/辅助资产membership及snapshot links，源保持只读。[S资产合同](../plans/cara_next_stage_20261028/sq/S_MODEL_ASSETS_R1.json)不构成S新主机的fresh资产接受，仍须在新GPU入口/准入中核验完整digest和链接。

四个CPU容器墙钟合计850.539818秒，分配vCPU时间上界1701.079636秒，已测worker CPU411.107263秒；已回收子进程仅资源矩阵两端有8.611435秒计量，成本微基准子进程、wrapper、结果写出后退出、staging/SSH/Git未完整计量。parent RSS不作为cgroup聚合峰值。长矩阵按实际起点检查；两卡成本微基准10.669秒即完成，早于预测半程，Ada60.128秒完成；没有等待估计过期后重启原件。

下一步完成S实际GPU runner/supervisor/guardian/once-only stage与中央结算的完整CPU承接，再绑定fresh资产、物理headroom与全卡报价审阅，之后才提交单独授权。原Q1 R2审阅与主线B36/F19分别保持，不修改共享账本/导航或他人工作；本轮不批准任何GPU卡。
