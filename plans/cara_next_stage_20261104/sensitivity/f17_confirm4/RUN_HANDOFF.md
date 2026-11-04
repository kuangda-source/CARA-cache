# F17 confirm4：GPU已完成并结算；独立确认FAIL

Run `cara-f17-confirm4-r1-20261104`；唯一原绑定launch `2fad981cd13e4ec8a0fad00253ea8358`。
源码/补充预注册已在首次GPU使用前提交并push：`6e33ee31544225802cbb07a7084de8d2cc8e14a1`。
scope `831797c82e8d1fa4ffe31716c5696da768b960571efe93dec8f094dfc0b5e6be`。
原sensitivity8继续保持seq92 SETTLED，不重派、不覆盖任何旧产物。

## 范围与报价

原四新输入×Native/F17/F19/WC轮转16条clean，另两个旧AV warm，共18条，仅MP4/终态latent。
同批速度≥1.9、F17≤133秒、LPIPS≤0.27、六质量均值门、δ0.027/70排列/单侧p≤0.05非劣检验全部保持；s(t)仍待完成。
预注册为本目录 `PREREGISTRATION_ADDENDUM.md`；完整输入来源、角色字节和矩阵见 `manifest.json`。

正式报价 **1.657808369500873GPUh**，硬限 **1.95GPUh**：CAL35四角色clean均值共1.016971396h＋sensitivity8原warm实测0.187096819h，10%波动0.120406821h，模型准备600s、退出600s。
本地/服务器CPU均为两flow×18完整tiny请求；服务器Torch2.7.1+cu128、exited0、CUDA=false，另验证无state目录和确认/非劣失败分支。CPU结果不代表真实F17确认成功。
50GiB准入、90°C、输出4GiB低水位和原600秒退出余量不变。没有新增任何heartbeat、cron、automation或持续监控。

## 磁盘实测与本卡落盘

`lsblk -f`、`df -hT`、`findmnt`、`mount`和ROTA/型号均已只读核实。当前只识别两块物理盘；没有可见20TB/NVMe或可用未挂载数据分区（sda2不是可用数据文件系统）。

| 设备 | 挂载/类型 | df容量/可用（测速前） | 系统/数据、ROTA | 我方写权限 / direct dd MB/s |
|---|---|---|---|---|
| sda5 / Samsung SSD 870 EVO 1TB | `/` ext4，含`/data20t`、`/home` | 916G / 61.328GiB | 系统SSD，0 | `/home/gaokuangda`可写；459.43（dd报告460） |
| sdb1 / ST16000NM001G-2KK103 | `/media/minchen/4def5c03-8324-4cba-ac0b-9fda7c79dc7b` XFS | 14T / 308.120GiB，98%已用 | 数据HDD，1 | 我方workspace/.sync可写；178.78（dd报告179） |
| 旧sensitivity8 loop51 | 数据HDD镜像内ext4 | 251G / 3.960GiB，99%已用 | 数据HDD的256GiB预分配镜像 | 不向近满旧卷写测试；测速用其同盘`.sync` |

`/data20t`名字具有误导性，但本项目 `R=/data20t/gaokuangda/worldcache_workspace` 是符号链接，真实落盘在上述HDD的 `gkd/cara_cal66_sm86_workspace`；旧状态数据并未放在系统SSD。
挂载根目录root:root，gkd为lihaoyang:lihaoyang，我方workspace为gaokuangda:gaokuangda；XFS为noquota，不能把共享盘当作我方专属整盘。

本卡 `S=$R/.sync/cara-budget-calibration-GPU-f17-confirm4-r1-20261104`；`O=$R/outputs/cara-f17-confirm4-r1-20261104`。
正常provision新建的独立16GiB镜像在 `$R/.sync/storage-reservations/f17-confirm4-r1/output.ext4`，新loop52；只格式化/挂载此新私有镜像，没有挂载或格式化任何闲置物理分区。
provision后输出可用16,713,109,504 bytes，HDD宿主可用313,644,158,976 bytes（约292.12GiB）；journal为系统SSD上的 `/home/gaokuangda/cara_control/f17-confirm4-r1/control.journal`，48MiB独立预分配。
原数据/旧镜像均不删除。本轮仅删除自己刚创建的测速文件 `/home/gaokuangda/cara_ddtest_f17_confirm4_20261104`、`$R/.sync/cara_ddtest_f17_confirm4_20261104`；新provision同时按原流程移除自己新建的`$O/.CPU-storage-admission-probe`与新ext4空目录`$O/lost+found`。CPU tiny夹具在其自身TemporaryDirectory中自动清理。

## 原句柄、进度和验收命令

实际guardian计费开始（Asia/Shanghai）：**2026-11-04T12:48:17.069580+08:00**；容器StartedAt=`2026-11-04T04:48:18.785964202Z`（北京时间12:48:18.785964）。
原guardian PID=537673、supervisor PID=537758、runner PID=537801；容器Running=true，实际UUID=`GPU-cebf7119-cf03-23b9-e192-cd196332b704`。
唯一启动取证的compute-app为该runner、显存306MiB；runner.log显示模型加载。尚未出现collection采样行，不宣称warm/clean完成或科学确认。确认真实CUDA进程后停止远端操作，没有等待或安排检查。
正式准入MemAvailable=55121645568 bytes（51.336032867GiB）；选卡无compute PID、24MiB、0%利用率、46°C、Default，owner锁和全部源/资产/存储检查通过。
唯一预留事件 **seq93 F17_CONFIRM4_WHOLE1_95_RESERVE，1.95GPUh**；job为RESERVED_OR_RUNNING，未结算。

| ledger GPUh | cap | used | reserved | available |
|---|---:|---:|---:|---:|
| 预留前 | 250 | 218.93254819368744 | 16.5 | 14.567451806312562 |
| 预留后 | 250 | 218.93254819368744 | 18.45 | 12.617451806312562 |

预计完成 **2026-11-04T14:27:45.179710+08:00**；停止新工作阈值2026-11-04T14:35:17.069580+08:00，硬限2026-11-04T14:45:17.069580+08:00。预计完成仅按单GPU正式报价换算；模型准备、温度或I/O可能造成偏差，不是完成承诺。没有设置任何中途/终态自动检查。
原回执见 `reports/cara_f17_confirm4_r1_20261104/` 的CPU、storage、admission、reservation、dispatch、started JSON。
状态未知只恢复这个原launch，不再prepare/reserve/dispatch；响应丢失只恢复同一原交易。
日志为 `S/runner.log`、`S/host-guardian.log`、`S/guardian.json`、`S/supervisor.json`、`S/billing.json`；采集进度在 `O/collection.json`。
从本地仓库执行一次性只读查看；每次使用新的receipt文件名，不建立循环：

```sh
P=plans/cara_next_stage_20261104/sensitivity
M=$P/f17_confirm4/manifest.json
.venv/bin/python "$P/ops.py" status --manifest "$M" --receipt /tmp/cara_f17_status_manual.json
```

仅在原GPU终态后捕获并唯一结算，失败费用照常计入，不能将UNKNOWN当终态：

```sh
.venv/bin/python "$P/ops.py" capture --manifest "$M" --receipt /tmp/cara_f17_terminal.json
.venv/bin/python - <<'PY'
import json
from pathlib import Path
v=json.loads(Path('/tmp/cara_f17_terminal.json').read_text())
assert v['status']=='ORIGINAL_CALIBRATION_LIFECYCLE_CAPTURE'
Path('/tmp/cara_f17_settle_input.json').write_text(json.dumps(dict(capture=v,launch_sha256=v['files']['launch']['sha256'])))
PY
.venv/bin/python "$P/ops.py" settle --manifest "$M" --input /tmp/cara_f17_settle_input.json --receipt /tmp/cara_f17_settlement.json
```

仅完整18/18成功、释放/Default恢复/唯一结算后才启动CPU评分，已有scorer只恢复：

```sh
.venv/bin/python - <<'PY'
import json
from pathlib import Path
c=json.loads(Path('/tmp/cara_f17_terminal.json').read_text())
s=json.loads(Path('/tmp/cara_f17_settlement.json').read_text())
Path('/tmp/cara_f17_score_input.json').write_text(json.dumps(dict(capture=c,settlement=s)))
PY
.venv/bin/python "$P/postrun.py" score --manifest "$M" --input /tmp/cara_f17_score_input.json --receipt /tmp/cara_f17_score_launch.json
# scores.json为COMPLETE_PENDING_ANALYSIS后：
.venv/bin/python "$P/postrun.py" analyze --manifest "$M" --receipt /tmp/cara_f17_analysis.json
```

评分/分析结果为 `S/released-score-control/scores.json`、`complete_analysis.json`；旧CAL35原四条LPIPS只读复用。analysis仅给F17确认，返回sensitivity_status=PENDING_ORIGINAL_CARD，不试图重建尚未采集的s(t)。本轮不执行这些验收命令、不等待GPU完成。

## 剩余敏感度：只列修复计划，不执行

当前数据HDD空闲不足400GiB，系统SSD也仅61GiB，未发现满足用户条件的新数据盘。因此按指令停在存储/hash修复计划，未改CPUOwnedStateImage、未改变旧256GiB卷，未做新盘3.33GB状态save/reload测量；没有可据此发布的新正式启动报价。
拟采用至少384GiB容量设计、建议512GiB新私有卷，保留现有失败/完整资产；CPUOwnedStateImage在D2H后的CPU树只hash一次，保留load_state完整性及alias/UniPC/RNG控制，取消GPU树的重复全内容hash。实际改动及核价需满足存储条件后再做。

条件规划估算（不是已测读回的正式报价）：复用003–007的五条Native记录；重做008并补009/010，112后缀和2新warm，共117请求；假定本F17卡16条clean完整接受后复用，绝不重复执行它们。
record仍取已测均值1388.039s，后缀计算沿用6.859528s/D-pair＋68.257887s/请求，restore以40–124s捕获窗口作代理；10%波动、600s加载、600s退出计入，约 **9.2723–12.1485GPUh（中心10.3460）**。
若保留原登记的5技术控制，则122新请求，约 **9.7773–12.7048GPUh（中心10.8701）**。删控制不能宣称原143完整履行；该调整需显式写入新续卡协议。实际读回未测、无新盘或hash优化加速折扣，范围不是硬上限。
全部>4GPUh，需要用户明确批准新数字与硬限；不能沿用原已关闭9.5GPUh批准，也不保证Shared25另有10GPUh。没有为续卡预留或启动。


## 2026-11-04 人工验收

Step0中央ledger确认本原launch尚未结算，pipeline_r2无job或stage；未重复结算/启动。原GPU容器2026-11-04 14:00:18.600384北京时间正常退出0、非OOM；guardian计费结束14:00:21.266785。
18/18完整，释放/Default恢复/原进程结束均通过；guardian唯一账单4324.197150305845秒=1.201165875084957GPUh，中央seq94唯一结算，返还预留余量0.748834124915043GPUh。
结算后cap250 / used220.1337140687724 / reserved16.5 / available13.366285931227594GPUh。原S/Q责任和所有其他job保持。
原唯一CPU scorer于2026-11-04 15:00:39.807156开始、15:47:35.389716北京时间结束，wall 2815.582560秒；exit0、非OOM、CUDA_initialized=false。12/12完整93帧LPIPS及48/48原质量位置完成，scores状态COMPLETE_PENDING_ANALYSIS；随后原stage的固定analyze正常退出0。

| 新输入 | Native/F17 T_DD | F17 LPIPS-Alex |
|---|---:|---:|
| av_cc90f226-5312-4e0f-959a-39cd4eb4d90d | 1.919858838× | 0.315270626 |
| human_034 | 1.920085430× | 0.154256711 |
| misc_9699390-uhd_3840_2160_30fps | 1.919521731× | 0.346878853 |
| physics_017 | 1.918576411× | 0.128339623 |

同批均值比1.9195105447531575×；Native/F17均值T_DD252.80195500275/131.701258789秒，通过≥1.9及≤133秒门。
新F17平均LPIPS0.23618645337159916≤0.27，旧CAL35平均0.2383678987301806；固定δ0.027、70标签排列的单侧非劣p=0.300>0.05，非劣性证据不足。
**独立确认FAIL（统计非劣门未通过，不能解释成已证明新输入更差）**。因此用户附带“F17验收通过后上卡”的pipeline_r2条件未满足：0新增预留、0stage/provision/launch，run仍无launch_id和实际/预计完成时刻。
结果路径仍为原stage的released-score-control；本地原始collection、terminal_capture、central_settlement、release、score_launch及指定旧卷清理receipt在 `reports/cara_f17_confirm4_r1_20261104/`。旧CAL35四条LPIPS仅复用，无重新评分。

budget-calibration-r1的唯一旧job已核实SETTLED；F17容器退出后losetup -j精确image无输出、findmnt无loop42、fuser无open、唯一活动CPU评分容器无loop42引用。删除了该reservation的output.ext4、provision.json和空目录，分配合计68,719,484,928 bytes（约64GiB）；XFS延迟回收后df为/dev/sdb1 14T/13T/357G/98%，精确可用382,360,334,336 bytes。未触及r2、CAL35、旧256GiB或F17的16GiB卷。本轮没有创建测速scratch文件、监控、cron或automation。


六个点均值质量门全部通过（差值均为F17减对应reference）：

| reference | 维度 | 均值差 | 最低门 | 通过 |
|---|---|---:|---:|---|
| NATIVE35 | MUSIQ_LONGER512 | -0.505542735 | -1.0 | 是 |
| NATIVE35 | subject_consistency | 0.012133556 | -0.01 | 是 |
| NATIVE35 | motion_smoothness | 0.000602518 | -0.01 | 是 |
| F19_A1 | MUSIQ_LONGER512 | 0.796042494 | -1.0 | 是 |
| F19_A1 | subject_consistency | 0.001197851 | -0.01 | 是 |
| F19_A1 | motion_smoothness | 0.000306426 | -0.01 | 是 |

正式 `complete_analysis.json` 的 `confirmation_passed=false`、`NI_passed=false`、`sensitivity_status=PENDING_ORIGINAL_CARD`。速度、平均T_DD、平均LPIPS及六质量门均通过，唯独固定统计非劣门未通过。源码/阈值未改，未重评分旧CAL35。
原始完整结果为 `reports/cara_f17_confirm4_r1_20261104/scores.json`、`CPU_score_terminal.json`、`complete_analysis.json`；服务器保留原S/released-score-control/scores.json及complete_analysis.json。上文capture/settle/score/analyze命令已各执行一次，已有句柄/交易只恢复，不重派或重评分。
15:48终态只读复核：中央ledger cap250 / used220.1337140687724 / reserved16.5 / available13.366285931227594；pipeline job为空、stage不存在。数据盘df仍14T/13T/357G/98%，精确可用382,359,617,536 bytes。没有新reserve或GPU启动；37项其他工作流未提交项保持未入本提交。
