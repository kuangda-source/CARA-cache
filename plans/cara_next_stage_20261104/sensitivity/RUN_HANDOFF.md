# sensitivity8：终止部分运行已结算；磁盘诊断与待批准方案

2026-11-04。run `cara-native-sensitivity8-confirm4-r1-20261104`，launch `c751f711b5e74daf8552eabe0109afe2`，原源码 `44f738feadad1c9e697274d9f69a48192c40518c`。
本轮只做原终态捕获、唯一结算和只读诊断；未准备、provision、预留、启动、重派、评分、analyze 或创建任何监控，未删除/搬移远端文件。
原启动记录保留在本文件 Git 历史 `b36ca12b`。本说明替代此前 RUNNING/预计完成时间；旧 ETA 已失效。

## 原运行与唯一结算

- guardian：北京时间 03:31:08.522200–05:59:08.149631；完整单调墙钟 **8879.627261445858 s = 2.4665631281794047 GPUh**。
- 容器 03:31:24.947943–05:59:06.528432，exit **130**，OOMKilled=false。guardian 为 TERMINAL，错误为 `OSError [Errno 28] Private output low water; stop before next request`。原角色均结束、两锁释放、Default 已恢复。
- 7/143 COMPLETE，008 被中断，余135 NOT_REACHED。collection.json 保留最后 RUNNING 快照，不能用它否定 guardian 终态，也没有将部分结果伪造为完整成功。
- 原预留 seq91，`SENSITIVITY8_WHOLE9_5_RESERVE` 9.5GPUh；本次唯一结算 **seq92 `SETTLE_ACTUAL_ADDITIVELY`**，job=SETTLED，释放余量 **7.033436871820595GPUh**。

| 中央 ledger（GPUh） | cap | used | reserved | available |
|---|---:|---:|---:|---:|
| 本次结算前 | 250 | 216.46598506550802 | 26 | 7.534014934491978 |
| 本次结算后 | 250 | 218.93254819368744 | 16.5 | 14.567451806312562 |

回执：[原终态](../../../reports/cara_sensitivity8_terminal_partial_r1_20261104/terminal_capture.json)、[原交易结算](../../../reports/cara_sensitivity8_terminal_partial_r1_20261104/central_settlement.json)。
原 billing.json 的 `central_settlement_pending=true` 是结算前的不可改写账单字段，中央结算回执已将原 job 关闭；不能据此再收费。
现有 capture/financial_terminal 本来支持失败终态，不需要工具修复、重复验证或 CPU 重放。唯一远端写入是用户明确要求的中央结算交易。

## 保留资产与字节数

服务器 `minchen-X11DAi-N`（10.128.160.181）。直接 SSH 本次在命令前关闭；实际使用本卡既有 office→two_card_lan SSH 路由，只读检查同一宿主。
令 `R=/data20t/gaokuangda/worldcache_workspace`，`S=$R/.sync/cara-budget-calibration-GPU-native-sensitivity8-confirm4-r1-20261104`，`O=$R/outputs/cara-native-sensitivity8-confirm4-r1-20261104`。
`R` 是符号链接，物理位置为 `/media/minchen/4def5c03-8324-4cba-ac0b-9fda7c79dc7b/gkd/cara_cal66_sm86_workspace`。
下表 bytes 是文件逻辑大小之和，含各自 requests JSON/MP4、`O/SENS_NNN.pt`，record 另含 `O/native_states/<input>/`；不重复分摊公共日志。

| path | kind / input | bytes |
|---|---|---:|
| SENS_001 | warm Native / av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | 8,321,353 |
| SENS_002 | warm F19 / 同001 | 8,321,175 |
| SENS_003 | record / 同001 | 47,041,292,221 |
| SENS_004 | record / human_199 | 47,042,096,616 |
| SENS_005 | record / misc_13398218_3840_2160_60fps | 47,042,298,237 |
| SENS_006 | record / av_51b45829-502e-4143-9c32-c026bd6ab191 | 47,041,301,784 |
| SENS_007 | record / av_cc90f226-5312-4e0f-959a-39cd4eb4d90d | 47,042,051,035 |
| SENS_008 | partial record / human_034 | 29,930,903,712 |

每条完整 record 的 native_states 是66文件、约47,032,970,666 bytes（43.802867GiB）：14份完整状态合计约46,626,782,618 bytes；每份3,330,480,299–3,330,488,299 bytes，另36份前步 latent、14份 guided、终态 latent 和 metrics.json。
008 已有24份前步 latent、8份 t8…22 完整 ZIP 目录的状态及8份 guided；`state_before_24.pt` 仅3,032,182,784 bytes、无 ZIP 中央目录，是截断文件，不能恢复；没有完整终态/MP4/metrics.json。ZIP 目录存在也不替代将来的内容完整性与后缀等价检查。
003…007 是5条可供后续复用的完整 Native 记录；001/002 是 warm，不可充作4新输入的 clean 速度基准。全部留在原位。

## 磁盘与清理候选（全部未执行）

读数约北京时间11:37–11:45；GiB=2^30 bytes。`df -h`：

| filesystem / location | 容量 / 已用 / 可用 / 使用率 |
|---|---|
| /dev/sdb1 XFS，minchen 挂载盘 | 14T / 13T / 309G / 98%；精确可用330,841,604,096 bytes（308.120255GiB） |
| /dev/loop51 ext4，本卡 O | 251G / 247G / 4.0G / 99%；可用4,252,110,848 bytes（3.960087GiB） |
| /dev/sda5，/data20t 所在根盘 | 916G / 808G / 62G / 93%；可用65,850,662,912 bytes（61.328209GiB） |

256GiB 是**已预分配的镜像文件** `S` 同级 `storage-reservations/native-sensitivity8-confirm4-r1/output.ext4`，size274,877,906,944，实际分配274,877,943,808 bytes，经 loop51 挂载。文件系统有效容量250.923893GiB，已用246.948181GiB，不能把镜像标称256GiB全当作可用数据空间。
低水位配置在 `S/history104-storage.json`：output **4,294,967,296 bytes=4GiB**，inode≥1024，宿主余量≥16GiB；由 `src/wcomr/history104_storage_r2.py:70` 执行，值出自 `scripts/provision_cara_f19_speed190_storage_r1.py:126`（本卡 provision.py 只改卷大小）。本次 inode余量16,776,793、宿主308GiB，触发的是 output bytes。
尽管错误文本写“before next request”，原guardian每2秒也检查一次（`cara_budget_host_guardian_r1.py:169`），所以在008写t24途中终止，并非等下一请求才停止。门槛未降低。

`du -x -B1 --max-depth=1`：gkd 可读合计至少2531.119GiB；最大为本workspace926.874、cosmos578.297、worldcache_omr401.819、planning_preserving_wm137.837、videogen123.577GiB。gkd部分其它项目的 Docker目录权限不足，未提权补读，合计为下界；未将这些其它项目列为清理对象。
本workspace：`.sync`887.249GiB（其中 storage-reservations880.000GiB），cache27.007、envs11.843、system-libs0.438GiB；`.sync`非卷部分约7.249GiB。最大的CPU stage为 full-RGB-cost0.7005、wc-time-score0.5160、dev128-fullCPU两个各0.3038GiB；仅凭名称不能判定可删。
`du -x outputs`仅0.028862GiB，因刻意跨不过 loop 挂载，**不是实际产物总量**，不能再加一次镜像880GiB；本卡约246.95GiB数据已计入镜像。

挂载路径属于另一用户 minchen 的盘域；OS挂载根目录为root:root，gkd为lihaoyang:lihaoyang（0777），本workspace为gaokuangda:gaokuangda（0700）。XFS选项为`noquota`，没有可证实的专属配额/整盘使用授权；我们的已占用范围是上述926.874GiB workspace，不是整个gkd。目录属主不能证明物理设备产权或约定份额。

| 仅限我方、已终止且SETTLED的候选 | 大小与限制 |
|---|---|
| `.sync/storage-reservations/budget-calibration-r1/output.ext4` | 64GiB已分配、卷内仅8192 bytes；对应0.002315298GPUh失败卡，优先候选。未来先保留失败metadata并确认无引用再卸载/释放；本轮未做 |
| CAL35 stage `CPU-pipeline-1793709564068210976`、`CPU-pipeline-1793709947544850288` | 2,871,296 + 5,787,648 = 8,658,944 bytes（8.258MiB）可重建CPU夹具；保留CPU-proof、原源码/launch、scores与账单 |
| 已结算 CAL35 `GPU-caches/xdg`，budget-calibration-r2同目录 | 各20,480 bytes；其余缓存为空，收益很小 |
| 已结算 budget-calibration-r2 64GiB卷、CAL35 16GiB卷 | 卷内分别38.710GiB、1.127GiB；只有归档后压缩/迁移空闲容量的可能，不能把整卷当垃圾删。CAL35原指标仍供非劣检验使用 |

本卡256GiB原镜像、五条完整记录、008失败证据均不列为清理候选；现有模型cache/envs、S/Q产物和其它用户数据不动。

## 报价偏差与执行顺序

原manifest：D-pair6.859528063秒；后缀 `(37-t)*pair + 68.257886994秒`；状态I/O另给1200秒（0.333333GPUh）；整卡9.287657161GPUh。a每条直接套用CAL35 clean Native314.536221秒，未测大状态快照。
以下实际秒来自collection；capture列是同一步 `state_before_t.pt.mtime - latent_before_t.pt.mtime` 的14项和，是捕获/哈希/D2H/序列化/写入的**近似窗口**，不是独立profiling。core含条件准备、循环、状态捕获和decode；write是延后视频写入。

| path / kind | 原估计s | 实际请求s | core s | capture窗口s | 视频write s |
|---|---:|---:|---:|---:|---:|
| 001 warm Native | 314.54 | 450.16 | 360.70 | 0 | 3.23 |
| 002 warm F19 | 212.39 | 223.39 | 188.53 | 0 | 5.80 |
| 003 record | 314.54 | 2178.09 | 2129.94 | 1736.60 | 8.47 |
| 004 record | 314.54 | 1542.48 | 1416.33 | 1099.04 | 81.96 |
| 005 record | 314.54 | 902.82 | 852.70 | 560.48 | 16.18 |
| 006 record | 314.54 | 1220.29 | 1152.26 | 854.22 | 21.96 |
| 007 record | 314.54 | 1096.51 | 1048.98 | 745.80 | 6.16 |
| 008 partial record | 314.54（完整路径） | ≈700（日志起点至容器退出，非完整计时） | 未保存 | ≈502.43（含截断t24，不能当完成保存） | 未到达 |

record去掉capture窗口后的core分别393.34/317.29/292.22/298.04/303.17秒，另有core外保护/安装/清理33.94–46.08秒及上述video write。无快照的步间隔中位数6.696–6.796秒，接近原6.8595而非算力慢十倍。
warm Native/F19的原T_DD分别277.426/154.304秒，tqdm循环约270/147秒，故decode约7/7秒（秒级日志近似）；record未单独记decode，不能补造精确分项。
7完整请求共7613.746秒，原对应2099.606秒=3.626倍；5record均值1388.039秒=原314.536的4.413倍，单条2.870–6.925倍。现有数据**不支持整卡或路径普遍10倍**的断言。guardian另含首次请求前约531.5秒模型/环境准备、008约700秒及约35秒外层/间隙/释放（日志近似）。
70次完整状态捕获窗口合计4996.145秒，均值71.3735、单次38.716–394.773秒；原I/O分摊仅1200/112=10.714秒/状态，均值低估6.66倍。已完成五record就用了1.388GPUh捕获窗口；八条外推2.2205GPUh，明显超过整卡0.3333预算。
原因定位到 `sampling.py:pair → CPUOwnedStateImage → save_state`：`cpu_owned_state_snapshot.py`先对原树做finite+全内容digest、按storage D2H，再对CPU树做digest；然后pickle/torch.save每份3.33GB。窗口中位数步计算正常、捕获窗口及81.96秒视频写入波动，支持状态处理与共享HDD/loop写回为瓶颈。没有当时的CPU/I/O-wait采样，无法把digest、序列化、D2H和磁盘等待进一步准确分账，也不能证明全部是磁盘或承诺SSD加速倍数。
容量同样漏算：8×43.802867=350.422939GiB，仅Native状态就超过256GiB镜像；112后缀若逐次从盘装载，还需约347.397GiB读取，原后缀报价没有单列完整状态读回/重建成本。LPIPS和质量评分均设计为释放后的CPU，本次GPU未跑LPIPS，不能用LPIPS解释偏差。

原143顺序是：001–002两个warm →003–010八record →011–013 Native桥和t8/t34 RESUME_D →014–125按t外层/8输入内层的112 SINGLE_C →126–127两FULL_SINGLE_C →128–143四新输入×四clean轮转。
总数8+112+16+2+5=143，**全部在PREREGISTRATION.md明确登记**；5控制是恢复等价技术依据，2warm是过程开销。当前后缀/控制/新clean均未到达，既无F17独立确认，也无实测s(t)。不能直接把143减成136并宣称仍完整履行原协议。

## 待批准的重跑方案：本轮均不执行

保持原4新输入、布局、seed、全部14步位、非劣δ0.027/70排列/p≤0.05、质量门和s·Δv函数；四新来源仍是manifest列出的vendor cosmos_eval_jsons_text_only原JSON。已有Native曝光如实登记，不再称从未执行，且不以此改布局/重选输入。
明显修复是按实测字节核容、把大状态放在获得盘主同意的高速空间，并将完整性检查放在一次CPU快照/读回边界，避免对同一GPU/CPU内容重复扫描；不得破坏storage alias、UniPC、RNG和原C语义。此处仅提方案，未实现，也未假定其加速收益。

下表为**规划估算，非新的可启动正式报价**：用record实测均值1388.039s；suffix计算仍用原实测D-pair+68.258s；未执行过任何suffix，因此读回/restore暂用40–124s/次的实测捕获窗口代理，中心71.3735s。明确这是代理，未来需要CPU真实大小读写/恢复计时才能正式核价；10%波动与600s加载+600s释放另计，不再叠加旧1200s状态写预算。

| 方案 | 新GPU工作与存储 | GPUh规划情景 |
|---|---|---|
| A 全量从头重跑 | 全143；至少384GiB有效容量设计，建议新512GiB高速私有卷，保留原256GiB失败资产；现共享盘仅308GiB空闲，无法直接再分配512GiB。按输入分组处理suffix可减少跨输入读盘切换，clean计时边界不变 | raw=10.222827h；`1.1*(raw+114*restore/3600)+1200/3600`：**12.97–15.90h，中心14.06h**。若record也按已见最慢2178s计，高情景17.83h，非硬上限 |
| B 只完成两个科学目标，复用原7条 | 复用001–007及五份完整Native状态；008整条重做，另补009/010，共3record；112suffix+16clean+新进程2warm=**133新请求**。去掉原5控制必须先修订预注册，不能冒称原完整143成功；建议保留控制的原协议版本见下。旧卷只读保留，补3record保留约131.41GiB，新输出192GiB卷量级足够；高速位置/盘主份额待确认 | raw=7.711770h；再加实测warm673.549s，`1.1*(raw+112*restore/3600+673.549/3600)+1200/3600`：**10.39–13.27h，中心11.46h**；record取最慢时高情景13.99h。未给快盘/去重hash任何未经测量的折扣 |

B若保留原5技术控制，新请求138条、避免科学协议删项：约**10.90–13.82GPUh，中心11.99GPUh**（同代理模型，另付新warm）。008的t8…22有ZIP目录但未作完整内容接受；不在本估算扣费，后续若验证并安全复用再重报，绝不读取截断t24。
两方案都 >4GPUh，均需用户批准新的run/完整硬限；本轮明确禁止GPU的指令继续有效，原9.5批准已随失败卡结算关闭。余额14.567451806GPUh；A中心仅余约0.503h且高情景超额，B中心约余3.103h，都不能同时保证另有Shared25规划10h。不能用低于2/2–4规则拆卡绕过批准。
未来验收需保留失败成本/原分母和复用来源，补齐对应技术控制，原GPU释放与新唯一结算后才可按批准的新协议CPU评分/固定analyze。**本轮没有运行postrun score/analyze。**

诊断原始材料仅留本地 `/tmp/cara_sens_disk_metadata.json`、`/tmp/cara_sens_disk_du_stream.txt`、`/tmp/cara_sens_mount.json`、`/tmp/cara_sens_targets.json`、`/tmp/cara_sens_cleanup.json`；服务器原 `O/collection.json`、`S/runner.log`、`S/host-guardian.log`、`S/billing.json` 保持原位。没有新审计文档，也未渲染或修改共享canonical文档/S/Q文件。
