# sensitivity8 流水线续卡：GPU已启动

Run `cara-native-sensitivity8-pipeline-r2-20261104`。
用户批准在 F17 非劣 FAIL（p=0.300）情况下照样启动，保留五控制，约10.37GPUh、硬限11.5GPUh；F17原判不变。

## 范围、报价和存储

122新请求=3 Native记录+112 single-C后缀+2 warm+5控制，2112 paired calls。复用已结算r1的SENS_003–007五条完整记录及F17卡16条clean的既有CPU结果，不重派、重评分或重复计费。
每个新输入立即完成14后缀，再删除本卡新写的14份state_before；保留metrics、每步latent、14 guided、终态latent和MP4，每新输入约0.378GiB（407MB上界）。旧256GiB卷全程只读，70份原状态不删除；其尺寸/ZIP中央目录已核查，一个样本已验嵌入digest，其他文件消费时各验一次。

原报价路径重新生成正式中心 **10.371018500875135GPUh**，工程范围 **8.459252184177252–11.37026798416013**，硬限 **11.5GPUh**；单GPU墙钟中心约10小时22分16秒。含42次保存、114次恢复、10%波动、600s加载和600s释放。CPU单次hash保存70.414s，冷读+恢复报价59.794s；GPU传输及新loop开销仍是工程估计，范围不是保证。
正式中心>11.0或可用额度<11.5不启动。Step0只读确认中央无job/reserve/settle回执、服务器无stage/输出/容器；当时ledger cap250 / used220.1337140687724 / reserved16.5 / available13.366285931227594。

`R=/data20t/gaokuangda/worldcache_workspace`，实际为minchen数据HDD上我方workspace的符号链接。
`S=$R/.sync/cara-budget-calibration-GPU-native-sensitivity8-pipeline-r2-20261104`；`O=$R/outputs/cara-native-sensitivity8-pipeline-r2-20261104`。
新64GiB镜像：`$R/.sync/storage-reservations/native-sensitivity8-pipeline-r2/output.ext4`；状态目录`$O/native_states`必须位于此新卷。独立48MiB journal：`/home/gaokuangda/cara_control/native-sensitivity8-pipeline-r2/control.journal`。
新增payload保守峰值50.242059GiB，另留ext4开销及固定4GiB低水位；旧256GiB+新64GiB分配总量320GiB。指定budget-calibration-r1旧64GiB镜像与metadata已在上一轮删除，其他旧卷保持。
50GiB fresh内存准入、90°C自动停、4GiB低水位及600s退出余量不变。只保留既有guardian/supervisor保护；无heartbeat、cron、automation或持续监控。

## 启动接线与验收入口

独立run binding与11.5GPUh中央事件；payload包含本补充预注册；F17复用以其原launch `2fad981cd13e4ec8a0fad00253ea8358` 对齐release。启动前源码提交并push，Linux入口/全部tiny路径、新卷及fresh准入完成后才唯一预留、唯一启动。
实际GPU源码固定为 `fafb0f23edfb149897b8c822f9f9d6ebb6a3f2ee`，scope `4f551bdddd8ffcd25d98d3d4fd73dcc531652676456c2b1bfcb640309dd309e4`。正常回执放`reports/cara_sensitivity8_pipeline_r2_20261104/`。

从Mac仓库根目录执行一次只读status，每次使用新receipt文件名：

```sh
P=plans/cara_next_stage_20261104/sensitivity
M=$P/pipeline_r2/manifest.json
.venv/bin/python "$P/ops.py" status --manifest "$M" --route relay --receipt /tmp/cara_pipeline_r2_status_manual.json
```

日志在`S/runner.log`、`host-guardian.log`、`guardian.json`、`supervisor.json`、`billing.json`；进度为`O/collection.json`。UNKNOWN只恢复本原launch，不prepare/reserve/dispatch第二次。
原GPU终态后capture，包含失败实际费用在内唯一结算；响应丢失只恢复同一交易：

```sh
.venv/bin/python "$P/ops.py" capture --manifest "$M" --route relay --receipt /tmp/cara_pipeline_r2_terminal.json
.venv/bin/python - <<'PY'
import json
from pathlib import Path
v=json.loads(Path('/tmp/cara_pipeline_r2_terminal.json').read_text())
assert v['status']=='ORIGINAL_CALIBRATION_LIFECYCLE_CAPTURE'
Path('/tmp/cara_pipeline_r2_settle_input.json').write_text(json.dumps(dict(capture=v,launch_sha256=v['files']['launch']['sha256'])))
PY
.venv/bin/python "$P/ops.py" settle --manifest "$M" --route relay --input /tmp/cara_pipeline_r2_settle_input.json --receipt /tmp/cara_pipeline_r2_settlement.json
```

完整122/122、释放/Default恢复/原进程结束及唯一结算后，启动一次CPU评分；已有scorer只恢复：

```sh
.venv/bin/python - <<'PY'
import json
from pathlib import Path
c=json.loads(Path('/tmp/cara_pipeline_r2_terminal.json').read_text())
s=json.loads(Path('/tmp/cara_pipeline_r2_settlement.json').read_text())
Path('/tmp/cara_pipeline_r2_score_input.json').write_text(json.dumps(dict(capture=c,settlement=s)))
PY
.venv/bin/python "$P/postrun.py" score --manifest "$M" --route relay --input /tmp/cara_pipeline_r2_score_input.json --receipt /tmp/cara_pipeline_r2_score_launch.json
# 原CPU scorer退出0且scores.json为COMPLETE_PENDING_ANALYSIS后：
.venv/bin/python "$P/postrun.py" analyze --manifest "$M" --route relay --receipt /tmp/cara_pipeline_r2_analysis.json
```

评分为112个新后缀LPIPS-Alex/latent MSE和原等价控制；analysis只合并F17既有12 LPIPS及48质量位置，F17仍为FAIL/p=0.300，独立报告s·Δv原理重建。结果在`S/released-score-control/scores.json`、`complete_analysis.json`。不在本轮等待完成、评分或结算。


## 原launch与一次启动确认

原stage安装调用响应丢失，经既有FRP主入口恢复了同一binding。启动前容器路径测试发现旧回执实路径不可见；为CPU入口、GPU采集及CPU评分补上旧256GiB输出实路径的只读挂载，源码在GPU前修订并发布为fafb0f23，launch_id沿用，64GiB卷沿用。初版与修订版Linux证明均保存；修订版16:44:50正常退出0，Torch2.7.1+cu128，两flow各122完整tiny请求、旧实路径可读，CUDA=false。F17原FAIL/p=0.300未改。

唯一launch_id `56926fe31f234746940a9d2d6677335d`；GPU UUID `GPU-cebf7119-cf03-23b9-e192-cd196332b704`。
guardian计费开始（北京时间）：**2026-11-04T16:47:59.057262+08:00**；容器StartedAt=`2026-11-04T08:48:00.765748585Z`。
预计完成（北京时间）：**2026-11-05T03:10:14.723865+08:00**；预计单GPU墙钟约10小时22分16秒。此为正式报价换算的估计，工程范围8.459252–11.370268小时。硬限11.5GPUh；停止新工作阈值2026-11-05T04:07:59.057262+08:00，硬截止2026-11-05T04:17:59.057262+08:00。

中央唯一预留 **seq95 SENSITIVITY8_PIPELINE_R2_WHOLE11_5_RESERVE，11.5GPUh**，job为RESERVED_OR_RUNNING，尚未结算。

| ledger GPUh | cap | used | reserved | available |
|---|---:|---:|---:|---:|
| 预留前 | 250 | 220.1337140687724 | 16.5 | 13.366285931227594 |
| 预留后 | 250 | 220.1337140687724 | 28.0 | 1.8662859312275941 |

Fresh准入MemAvailable=55781072896 bytes（51.950172GiB），目标卡无compute PID、24MiB、0%、45°C、Default，owner锁、源码/实际资产及存储检查通过。
一次启动确认：guardian PID=622200原进程存活，supervisor为BUDGET_CALIBRATION_SUPERVISOR_RUNNING，容器Running=true；唯一CUDA runner PID=622342、306MiB，GPU为Exclusive_Process、49°C。
状态目录 `/media/minchen/4def5c03-8324-4cba-ac0b-9fda7c79dc7b/gkd/cara_cal66_sm86_workspace/outputs/cara-native-sensitivity8-pipeline-r2-20261104/native_states` 在新64GiB镜像（68,719,476,736 bytes，inode66973293）的/dev/loop42 ext4上；主机与GPU容器内st_dev均为1834。此loop42是新卷复用的设备号，非已删除旧r1镜像。旧256GiB输出实路径Mount.RW=false。
已完成唯一启动与挂载确认，随后停止远端检查；未等待请求/整卡完成，未创建heartbeat、cron、automation或额外持续监控。源码及服务器manifest自GPU启动起不再改动。后续仅按上文原句柄status和终态capture→唯一settle→CPU score→analyze人工验收。
