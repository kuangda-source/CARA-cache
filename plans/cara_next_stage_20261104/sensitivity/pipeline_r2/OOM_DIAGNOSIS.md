# sensitivity8 pipeline r2：OOM诊断与续卡估价

Run `cara-native-sensitivity8-pipeline-r2-20261104`，launch `56926fe31f234746940a9d2d6677335d`，执行源码fafb0f23。本轮零GPU：未重启、重派、准备或预留新卡，也未运行score/analyze。

原容器北京时间11月4日17:26:59退出：OOMKilled=true、ExitCode1，runner -9；仅8/122完成，PIPE_009中断。guardian账单 **0.650497297213102GPUh / 2341.790269967169秒**，中央唯一结算 **seq96**；原11.5预留解除，其他16.5责任保留。项目累计 **220.7842113659855GPUh**。运行状态现为OOM_STOPPED，running列表为空，操作状态central_settlement_pending=false。
原billing.json与guardian的哈希绑定，保持原字节；结算回执复制到原stage/central-settlement.json，ops.status据此覆盖pending显示。collection.json已按真实终态协调，8条COMPLETE保留、PIPE_009标OOM_STOPPED；协调前collection已保存在oom_evidence.json。

## 原因与证据

- 内核17:26:54报CONSTRAINT_MEMCG，命中40GiB memory+swap总限额；anon=40,064,684,032 bytes（37.31GiB），file=16,785,408 bytes（16.01MiB），runner anon-rss=39,121,172KiB。不是显卡显存不足，也不是大量文件页缓存单独造成。
- 40g为宿主RAM cgroup限额；Docker Memory/MemorySwap均为42,949,672,960 bytes。OOM前显存最高27,764MiB，低于A6000容量。内核还记录swap活动，不能把两个限额相等解释为从未发生任何swap。
- 具体跨请求保留路径：`sampling.py:196`把约3.330GB完整checkpoint装入CPU；`start`闭包捕获saved，经`resume_sampler`的exec函数→globals→函数环留存（66–84、198–214行）。`load_state.rebuild`的局部StateUnpickler类/方法闭包还捕获stores/tensors（47–63行）。引用计数无法及时释放这些环，自动代际GC不按请求边界触发。
- 轻量CPU复现：8次1MiB真实save_state/load_state，8份字节存储仍存活，gc.collect后归零；加同型sampler globals环结论相同。实际PIPE_004/005/006/007/008完成了5次checkpoint加载，PIPE_009是第6次；若六份均滞留，仅原CPU stores就约18.61GiB。这是与故障吻合的实际累积源，不是模型每请求重载。
- `runner.py:155`只建立一个Inference；结果列表保存标量/历史与文件描述，final_latent从result移出后落盘。此时新Native记录尚未开始，Native专用Δv/first-block列表与state写入不是本次触发点；新卷state_before文件数为0。
- 没有逐请求Host RSS/cgroup曲线，退出后cgroup已移除；已有遥测只含GPU。不能精确分摊37GiB或保证修复后真实峰值必低于40g。下表为已记录请求时钟/显存峰值，不能充当Host RAM曲线。

| 请求 | 类型 | 完整请求秒 | 遥测显存峰值MiB |
|---|---|---:|---:|
| PIPE_001 | NATIVE35 | 334.401 | 24794 |
| PIPE_002 | F19_A1 | 212.578 | 26724 |
| PIPE_003 | NATIVE35 | 317.169 | 26724 |
| PIPE_004 | RESUME_D@8 | 292.342 | 26942 |
| PIPE_005 | RESUME_D@34 | 107.158 | 27138 |
| PIPE_006 | SINGLE_C@8 | 287.987 | 27350 |
| PIPE_007 | SINGLE_C@10 | 274.224 | 27546 |
| PIPE_008 | SINGLE_C@12 | 261.976 | 27764 |

## 最小修复与可复用结果

`runner.py:97`在请求结果持久化和本卡状态清理后调用一次gc.collect，回收不可达sampler/unpickler闭环，再进入下一请求。没有增加fallback、哈希或重试，没有改40g限额，也没有降低50GiB准入、90°C或4GiB低水位。修复仅在Mac仓库，未同步到已结束的GPU stage。
`tests/test_cara_sensitivity_request_memory.py`用8个小状态检查实际collect_loaded请求边界的对象存活：旧代码第二条请求前失败，修复后2项通过，1.85s，CUDA=false。真实GPU峰值/GC代价仍未验证。

8条完成结果的16个latent/video文件哈希全部匹配，共66,574,299 bytes。PIPE_001/002为warm，PIPE_003–005为Native桥及t8/t34不干预控制（latent equal=true/max_abs_diff=0），PIPE_006–008为t8/t10/t12单C。6条控制/科学结果可直接承接；2条warm可存档，但新进程仍计2条fresh warm。尚无LPIPS/MSE正式评分；可复用原始产物不等于整卡科学接受。PIPE_009只有2094-byte参数JSON，无可接受终态/MP4，必须重做。
产物保留在原`outputs/cara-native-sensitivity8-pipeline-r2-20261104/{PIPE_001..008.pt,requests/PIPE_001..008/}`；旧5条Native和F17卡产物仍在各原目录，不移动或删除。

## 新run报价，均未授权执行

沿用已发布模型：D-pair6.859528063s、非循环68.257886994s、42次新state保存、每次保存70.414s、冷读+恢复59.794s，中心10%波动、600s加载+600s释放；工程范围保留GPU请求−5%/+15%、state路径−25%/+35%，不是置信区间。

| 方案 | 新请求 | GPUh中心=单GPU墙钟小时 | 工程范围GPUh/小时 | 建议单卡硬限 |
|---|---:|---:|---|---:|
| 续接PIPE_009：114原剩余＋2新warm | 116 | 9.842432 | 8.019355–10.801045 | 11.0 |
| 全重跑本122请求计划 | 122 | 10.371019 | 8.459252–11.370268 | 11.5 |

全重跑仍复用原5 Native/F17 clean16，不是重跑原143卡。续接扣除已完成Native桥、2 RESUME_D、3 SINGLE_C的计算及5次恢复；保留42次新保存、109次恢复和fresh warm成本。新warm按原673.55s保守计，当前实测两warm合计546.98s。GC真实开销未GPU测量，工程范围保留。
优先保留可验证产物、另建新run承接114条；现有runner不会直接重启已结算目录。新续接配置还需预置已完成行/索引（包括FULL_SINGLE_C@8引用PIPE_006），尚未制作或stage。
用户最新预算政策为累计仅记账、无总量硬上限，**任何新单卡报价>8GPUh需本人批准**。两方案均>8，旧run批准不能授权重启；当前均无新GPU权限。旧ledger cap字段作为历史格式保留，本轮没有按它限制报价或扩展预算框架；下一卡准入须按新政策另行准备。

原始证据与唯一结算：`reports/cara_sensitivity8_pipeline_r2_20261104/{terminal_capture,central_settlement,terminal_status,oom_evidence}.json`。本轮已完成财务结清与轻量生命周期回归；真实40g峰值及新续接运行验证受零GPU指令限制，留待另行批准。
