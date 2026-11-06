# CAL106 整卡组合 CPU 接受与完整报价复核

2026-10-25。整卡监督、释放 GPU 后评分、恢复与终态验收组合已通过独立 CPU 接受。原 α、三条历史强基线、19角色、106路径和原报价保持。此次 GPU 提交、预算预约均为0；独立质量模型的真实资源与 CPU 前向尚未接受，不能据此启动 GPU。

## 1. 本次完整接受

- 生产 source：`cd26726541a3dcb218e5000f250d80e65f5dffde`。
- stage：`/data20t/gaokuangda/worldcache_workspace/.sync/cara-shared106-combination-CPU-r3-20261025`。
- 原容器于北京时间15:47:51启动、15:56:24退出0，无OOM；终态实际观察为15:56:51（以回执 observed_unix 为准）。检查主体约510.87秒。资源1CPU/4GiB、GPU隐藏。
- [原启动](../reports/cara_shared_CAL106_combination_CPU_launch_r3_20261025.json)、[原终态](../reports/cara_shared_CAL106_combination_CPU_terminal_r3_20261025.json)、[独立接受](../reports/cara_shared_CAL106_combination_CPU_accepted_r3_20261025.json)。

| 检查 | 本次结果及边界 |
|---|---|
| 完整采集与序列化 | 106物理位置；76正式、20计时重复、8warm、2诊断；22项同角色同输入数值控制 |
| 释放后LPIPS调度 | 72对、6696帧，拒绝释放前评分；完成分数可恢复，不重放GPU |
| 独立指标调度 | 76视频×3指标=228位置，raw与分数及输入身份绑定；本次为声明式合成回调 |
| 真实评分入口 | 另做真实93帧432×768 LPIPS；不是Cosmos生成结果 |
| 监督与释放 | 9项真实CPU子进程生命周期，包括失败、超时、外部上下文、评分失败/超时与模式恢复延期 |
| 存储保护 | 6项检查，包括实际tmpfs ENOSPC与跨盘日志恢复；不调用真实GPU或管理员模式变更 |
| 终态与回归 | 远端53项测试通过；本地相关67项通过。测试计数包含复用测试，不等于不同科学情形数 |

另以真实R3终态回执重放独立接受，并验证6种篡改（源码载荷、分母、生命周期失败、非零退出、GPU可见、报价）均被拒绝，见[负例检查](../reports/cara_shared_CAL106_CPU_acceptance_negative_checks_r1_20261025.json)。

原76条生产链小张量CPU采样通过的组件按SHA复用，未重新派发；本次新增106端点、72配对及228指标调度用明确声明的合成fixture验证组合。实际模型质量、速度及真实硬独占均未据此宣称通过。

## 2. 补齐的执行约束

1. 监督器核对原runner上下文、FD锁与连续独占；保留硬时限、StorageGuard和跨盘原日志。CPU检查以隔离账本演练，不写权威GPU账本。
2. GPU采集结束后先保存真实账单、结算、释放锁与上下文，再评分。评分失败只恢复原视频评分，不重放GPU。
3. 推理容器保留48GiB；仅释放后的评分子进程设8GiB地址空间、至多2CPU核、21600秒上限，CPU生命周期已验证限制与停止行为。
4. LPIPS及独立质量失败保存为独立不可覆盖回执；恢复进度不能抹掉之前失败。无效raw不得静默覆盖。
5. 独立终态接受核对106分母、22控制、72配对、228指标、源和原件SHA、费用、原句柄退出、锁释放、完整独占监测、跨盘财务原件一致性。缺真实质量模型CPU绑定仍拒绝GPU完整准入。

实现与约束详见[整卡组合合同](../plans/cara_policy_generator_20261020/CAL106_COMBINATION_AND_RELEASE_SCORING_R1_20261025.md)。本地控制入口当前只有CPU准备与只读终态收件/接受，没有自动GPU派发。

## 3. 保留的检查历史

- R1原组合退出0并接受，但尚无新增评分失败回执保留和评分子进程资源限额证明；[原终态](../reports/cara_shared_CAL106_combination_CPU_check9_r1_20261025.json)、[原接受](../reports/cara_shared_CAL106_combination_CPU_accepted_r1_20261025.json)保留。
- R2在故意注入第三项质量评分失败时暴露异常保存分支缺少`json`导入，退出1；[失败原件](../reports/cara_shared_CAL106_combination_CPU_terminal_r2_failed_20261025.json)保留。修复后增加完整228项恢复回归，R3以新source、新stage完整执行，不覆盖R2。
- R3合成大批量fixture使用有界256MiB tmpfs加速CPU检查，持久化证明、摘要与失败副本；ENOSPC测试另用64MiB隔离卷。未改变真实实验输出合同或科学范围。

## 4. 完整报价与预算

[逐路径复核原件](../reports/cara_shared_CAL106_whole_quote_recheck_r1_20261025.json)绑定[未修改的范围清单](../manifests/cara_shared_CAL106_scope_quote_r1_20261025.json)。

| 项目 | GPUh |
|---|---:|
| 106路径生成 | 8.1707101784 |
| 模型加载 | 0.15 |
| 保存与释放 | 0.35 |
| 上述合计加15%余量 | **9.9713167052** |
| 原拟硬上限 | **11.5** |

释放后CPU评分仍为2CPU、8GiB、最多6小时/12vCPUh，不占GPU账单。6小时是停止上限，尚不是实际独立模型完成吞吐保证。

[本轮只读账本](../reports/cara_CAL106_budget_readonly_20261025.json)：累计已用156.1354543951 GPUh，旧两卡未知责任预约16.5 GPUh，可用53.3645456049 GPUh，总上限226 GPUh。CAL106未登记、未预约；未来若按11.5预约，可用余额将为41.8645456049 GPUh，当前未执行该动作。

最终部署门槛仍为 `min(257.7712338712067秒, 0.8×新Native完整请求均时)`；报价不是执行授权，也不改变原α、强基线或历史失败。

## 5. 下一项明确缺口

[四卡资源只读核查](../reports/cara_CAL106_quality_resource_preflight_20261025.json)显示现有原始质量工厂所需模型资源及依赖overlay仍未齐备：DINO、AMT、RAFT、ViCLIP、MUSIQ等。CAL106只评分注册的MUSIQ、主体一致性、运动平滑三项，不称完整VBench；其共享工厂依赖不能用合成回调替代。

下一步应准备原资源、做真实完整视频CPU前向及吞吐接受，形成不可变quality-binding，再重新核实费用与资源。当前 `independent_quality_models_CPU_accepted=false`、`GPU_dispatch_ready=false`。不重派已接受的入口和组合CPU，不启动GPU，不改旧P1/104/112原件或账单。
