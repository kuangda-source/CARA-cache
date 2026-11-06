# 同配额 CFG 位置交换：完整核心与生产 CPU 通过，单次例外待确认

2026-10-08。当前卡 `WC-W3-CFG-BUDGET-MATCHED-R1-20261008-A`；累计预算 50 GPUh 已实际生效，旧费用保留。这是继续 v5.8 的位置区分，不扩训练、稀疏、OMR 或人评。

已完成的价值：新实际路由与原固定采样器在服务器生产 Python 上 CPU 验证通过，source `0001f28bb3ada3e329816562d76f9125d2cb3819`。父/完整后缀/模拟输出为 4/40/24，五类故障回滚保留，104 项证据破坏拒绝。各四细胞全 72 调用掩码独立重建后均 CFG0/CFG1 18/17、总 35；45/47、46/48 交换、其余位置、初始化/70 reset/71–72 全算尾保持。五组严格重复、完整状态/配置原值、两个 pre46 桥及父/OFF/BASE 编码桥通过。

原 CPU driver 3329239、child 3329240 已退出。driver 总 wall 288.911300 秒，检查本身 286.168160 秒；无 CUDA，新增 GPU 0。288 载荷源与执行后哈希一致，根账本原字节未变。四次成功包含两种 flow 与原建议/尾段建议不同两种情况；CPU fixture 强制原建议和模拟网络/编码，不能把它称为真实 GPU 固定掩码可行性或视频质量结果。

证据入口：

- `reports/wc_w3_cfg_budget_core_cpu_r1_20261008_terminal_capture.json` 与所有原件 gzip。
- `reports/wc_w3_cfg_budget_core_cpu_r1_independent_audit_20261008.json`：独立 stdlib 从原始状态、配置、动作、配额、完整轨迹及重复重建。
- `manifests/wc_w3_cfg_budget_r1_execution_preregistration_20261008.json`：完整四组合与费用登记；原 v5.8/CPU 登记原件不修改。

完整 1 父、10 后缀、6 新视频、1 旧 Native、4 主要比较、1 交互保持。原整卡费用预测 1.994372556 GPUh 完整保留。两 flow 的同规格十后缀 CPU wall 最大相对新增 4.430841690%，按完整旧预测追加 318.122966 秒保守集成预算，得 **2.082740047 GPUh**。这是规划代理，不是 GPU 测速或速度收益；没有借旧整卡较低实费、删对照或拆卡降低预测。

单次 2 GPUh 规则仍有效，因此新 GPU 不能凭累计 50h 扩额直接提交。真实生产入口、全部301载荷/资产/延迟导入/评分资源 CPU 验证已完成并独立确认，按直接用户约定只请求这张完整卡的 >2h 例外。尚未选择/执行新 GPU。

当前累计 **23.702366117/50 GPUh**、60 jobs、无在途；余 **26.297633883 GPUh**。原四组合 12bc430 已完整结束及评分独立确认，不复跑已消耗身份。goal active；本轮核心 CPU 和完整生产准备有进展，总体研究未完成。

## 实际生产 CPU 已完成与完整卡范围

生产 source `4ff96ed3b0385a07bd82f19313d1a98bc9595094`、独立 `.sync/wc-w3-cfg-budget-production-cpu-r1-20261008`，真实两步骤 runner/metric 均 exit0，总 CPU wall **65.930159 秒**。301 份载荷执行前/后/原字节与配置绑定一致，29 个本地传递依赖齐全，9 项契约破坏拒绝，实际 HF guardrail 路径及 Blocklist 已检查，LPIPS FP32/AlexNet 权重与源版本核对并在 CPU 实例化；没有解码新视频或评分，没有 CUDA/GPU。原三个句柄 **3329901/3329902/3330067** 均已退出，原件和独立绑定回执已保存。

`reports/wc_w3_cfg_budget_production_cpu_r1_terminal_capture_20261008.json` 和 `reports/wc_w3_cfg_budget_production_cpu_r1_independent_audit_20261008.json` 为入口；原 receipt SHA `ab3672b204fca430f6ad7b394ba05eb40fd7629fc73c919d3575f0108291f156`。评分资源原历史协议的 policy/benefit 元数据仍按原件保存；新评分实际结果剔除这两项单动作说明，固定配额 estimand 由新实验登记、实际路由及 per-CFG 18/17 审计单独绑定，数值协议未改。

待直接确认的只有完整单卡 **2.082740047 GPUh** 例外，见 `manifests/wc_w3_cfg_budget_single_job_exception_request_20261008.json`。该文件是范围可审阅的请求，`direct_user_authorization=false`，不冒充批准。实际 GPU 当前零提交、selected=false。累计50h权威已经生效；不得将累计扩大解释为单次>2h的自动许可。

科学问题：若 CFG0 的 LPIPS 正信号在相同18/17配额下仍存在，支持这次刷新位置重分配；若不保留，说明当前自适应收益可能依赖其他后续路由或多算，但不能唯一归因或否定W3。所有正负帧、四比较/交互、诊断时间与真正实费完整保留。已有种子曝光，仍不是独立CONF、物理质量或稳定速度优势。

接续：直接批准该完整卡后，新增精确范围/forecast 的用户例外权威，冻结原生产301载荷，做 selected CPU 实际绑定，再 fresh 目标GPU/共享锁/余额准入，只单次提交。现有累计账本SHA `70ceb44d6c4fbe2a86ba1b0531477f2598ab3c4801ff8915f857c99040afdf16`；不得复投原12bc430四组合、0001f28核心CPU或4ff96ed生产CPU。单次例外尚未答复，目标 active（本轮必要准备有进展），整体科学目标未完成。

## 最新执行状态：实际 blocked，等待原单次例外

第三连续目标轮已实时核对：没有直接新卡单次例外权威，selected/output 均不存在，五原CPU进程退出，账本23.702366117/50 GPUh不变且无在途。首轮完成必要准备并提出具体请求，后两轮只有相同等待条件，无可继续的安全研究步骤；goal工具于1791437783实际返回 **blocked**，见 `reports/wc_w3_cfg_budget_goal_blocked_receipt_20261008.json`。这是等待授权，不是预算耗尽、方法失败或目标完成。停止重复自动检查，保留全部已验收源/范围/正负结果/费用，用户直接答复原完整卡单次2.082740047h例外后接续。前文active是当时的历史状态。

## 2026-10-09 直接批准与文档先行已完成

用户本轮允许完整2.082740047GPUh例外，同时要求先用飞书CLI形成组会报告。完整报告已创建并回读验证：[飞书组会报告](https://lcnssrlun9lz.feishu.cn/docx/HTSIdK0uLofCG5xUI1IcTKaCnAh)。实际权威见[单次授权](../manifests/wc_w3_cfg_budget_single_job_authorization_20261009.json)，CPU载荷301份冻结保持。下一同源selected CPU绑定及独立审计，然后fresh资源准入与完整GPU/释放后全93评分；此刻新GPU=0。旧待答/blocked与原预测、范围不改。

## 2026-10-09 原完整GPU已启动

文档先行已完成，selected实际CPU16.380秒/301载荷/全部直接权威独立重建通过，source8457dfb的原GPU3368923/3368938已进入生成；释放后全93CPU3369011绑定原句柄自动执行。完整范围与各CFG18/17保持，尚无本轮科学结果，原费用底数与第61job在途预留保留。后续跟踪见[162实际执行](162_WC_CFG_BUDGET_MATCHED_AUTHORIZED_EXECUTION_20261009.md)，不重启已消费身份。
