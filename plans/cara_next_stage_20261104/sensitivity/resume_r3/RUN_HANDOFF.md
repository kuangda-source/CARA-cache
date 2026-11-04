# sensitivity8 resume r3

用户2026-11-05 00:30北京时间批准：「批准从 PIPE_009 续跑，约 9.84 GPUh」。仅此一个新run `cara-native-sensitivity8-resume-r3-20261105`，硬限11.0GPUh；已结算r2不重启。累计仅记实际GPUh，新单卡>8GPUh需本人批准，本卡已有批准。

本补充登记只接续原PREREGISTRATION.md及pipeline_r2补充协议：新队列116=2 fresh warm＋原PIPE_009…122的114请求，原编号保持；r2的PIPE_003…008六条COMPLETE（3控制＋3敏感度）在manifest按原slot/result与latent/video SHA固定。启动时各验一次产物hash并预置控制索引；最终CPU评分包含六条，无新增重复样本或计费。原r1五Native及F17 clean16继续只读复用，F17非劣原FAIL/p=0.300保持，s·Δv函数、seed、输入、五控制、全112后缀分母不变。

包含15bb3d39每请求gc.collect修复。新生产输出host_memory.jsonl每请求GC后记录RSS、cgroup current和peak。此服务器实测cgroup v1，current/peak分别取memory.usage_in_bytes/memory.max_usage_in_bytes；peak为容器累计高水位，current含文件页缓存，均以bytes计，不伪称逐请求瞬时峰值。

正式报价中心9.842431872190623GPUh，工程范围8.019354858550322–10.801045382298438；墙钟中心9小时50分33秒，单卡硬限11.0GPUh/小时。42次保存＋109次恢复；2fresh warm保守成本不扣。GC代价和真实40g峰值尚未GPU验证，范围不是保证。40g容器限额、50GiB fresh宿主内存、90°C自动停、4GiB低水位及600s释放余量全部保持。

独立新64GiB输出卷（旧r2 64GiB及r1 256GiB原件保持只读）；最多一份新record状态，14suffix后仅删除该run自己的state_before文件，保留小产物。新峰值约50.24GiB＋4GiB低水位及ext4开销。无heartbeat/cron/automation或持续监控；启动后仅一次短首批确认。

R=/data20t/gaokuangda/worldcache_workspace
S=$R/.sync/cara-budget-calibration-GPU-native-sensitivity8-resume-r3-20261105
O=$R/outputs/cara-native-sensitivity8-resume-r3-20261105
日志：S/runner.log、host-guardian.log、guardian.json、supervisor.json、billing.json；O/collection.json、host_memory.jsonl。
路由：~/.local/bin/intranet-ssh two-card（FRP优先，连接建立前可退Tailscale，不重放远程命令）；ops的--route relay使用该入口，中央仅走既有账本通道。

从Mac仓库根目录人工只读检查（每次换新receipt文件名）：

```sh
P=plans/cara_next_stage_20261104/sensitivity
M=$P/resume_r3/manifest.json
.venv/bin/python "$P/ops.py" status --manifest "$M" --route relay --receipt /tmp/cara_resume_r3_status_manual.json
```

终态后捕获并唯一结算，失败费用照常计入；响应丢失恢复同一交易：

```sh
.venv/bin/python "$P/ops.py" capture --manifest "$M" --route relay --receipt /tmp/cara_resume_r3_terminal.json
.venv/bin/python - <<'PY'
import json
from pathlib import Path
v=json.loads(Path('/tmp/cara_resume_r3_terminal.json').read_text())
Path('/tmp/cara_resume_r3_settle_input.json').write_text(json.dumps(dict(capture=v,launch_sha256=v['files']['launch']['sha256'])))
PY
.venv/bin/python "$P/ops.py" settle --manifest "$M" --route relay --input /tmp/cara_resume_r3_settle_input.json --receipt /tmp/cara_resume_r3_settlement.json
```

116/116完整、释放/恢复Default/原进程结束及唯一结算后才CPU评分、分析；已有scorer只恢复：

```sh
.venv/bin/python - <<'PY'
import json
from pathlib import Path
c=json.loads(Path('/tmp/cara_resume_r3_terminal.json').read_text())
s=json.loads(Path('/tmp/cara_resume_r3_settlement.json').read_text())
Path('/tmp/cara_resume_r3_score_input.json').write_text(json.dumps(dict(capture=c,settlement=s)))
PY
.venv/bin/python "$P/postrun.py" score --manifest "$M" --route relay --input /tmp/cara_resume_r3_score_input.json --receipt /tmp/cara_resume_r3_score_launch.json
# 原CPU scorer退出0且scores.json为COMPLETE_PENDING_ANALYSIS后：
.venv/bin/python "$P/postrun.py" analyze --manifest "$M" --route relay --receipt /tmp/cara_resume_r3_analysis.json
```

评分在S/released-score-control/scores.json，分析在complete_analysis.json。8旧完成中2warm只存档，六正式产物加入完整评分；不把复用称为新独立结果。

启动前状态：中央未有本run，服务器无本stage/输出/容器；ledger累计220.7842113659855、其他预留16.5、历史格式可用12.715788634014501GPUh。源提交、Linux CPU入口、新卷、fresh准入完成后才一次预留11.0并启动。实际启动及首批确认见下。


## 唯一启动与首批确认（2026-11-05）

run_id `cara-native-sensitivity8-resume-r3-20261105`；launch_id `e829f230b9c44b2cbd63128d1e511a0e`；GPU `GPU-cebf7119-cf03-23b9-e192-cd196332b704`。
GPU源码 `113dc7c80fafee00e15ae18375875732e8e97e4b`（含15bb3d39 GC修复；准备提交d9f00e37，容器cgroup根路径修正113dc7c8），scope `5b72ba273fb2315a47e136b7db406659080a7a4084f2c86d3c75de95a3b7cbcf`。源码均在GPU前commit+push。首次CPU入口因拼接了宿主cgroup路径退出1，已保留；同一新stage在GPU前修正路径，保留同一launch_id及已建新卷，以独立cpu-r2容器完整重验232条tiny、CUDA=false后退出0。本地3项生命周期/日志测试通过。

计费开始北京时间 **2026-11-05T00:57:45.435984+08:00**；Docker StartedAt=`2026-11-04T16:57:46.991568752Z`（UTC，约北京时间00:57:47）。中心墙钟 **9小时50分33秒**；预计完成 **2026-11-05T10:48:18.190724+08:00**，为报价估计，工程范围8.019355–10.801045小时；不承诺准时。硬限11.0GPUh，停止新工作阈值2026-11-05T11:47:45.435984+08:00，硬截止2026-11-05T11:57:45.435984+08:00。

中央唯一预留 **seq97 SENSITIVITY8_RESUME_R3_WHOLE11_RESERVE，11.0GPUh**；本run为RESERVED_OR_RUNNING，尚未结算。累计实际仅记账，不新增累计政策硬限，历史cap字段保留兼容。

| ledger GPUh | 历史cap字段 | used | reserved | 历史格式available |
|---|---:|---:|---:|---:|
| 预留前 | 250 | 220.7842113659855 | 16.5 | 12.715788634014501 |
| 预留后 | 250 | 220.7842113659855 | 27.5 | 1.7157886340145012 |

Fresh准入：MemAvailable=55336513536 bytes（51.536144GiB），目标卡无compute PID、24MiB、0%、Default、45°C；源码/资产、双锁和磁盘通过。未降低50GiB/90°C/4GiB门槛。容器Memory=MemorySwap=42949672960 bytes，保持40g。

实际调用路由为FRP `two_card_relay`，由`~/.local/bin/intranet-ssh two-card`选择；本轮未退Tailscale。只有一次启动后的有界前台日志等待，首条完成后读取一次状态；该reader已结束，没有持续查询、heartbeat、cron或automation。
确认时：容器Running=true/OOMKilled=false；guardian原进程PID=748964存活（其存活期文件标签仍为ADMITTING），supervisor为BUDGET_CALIBRATION_SUPERVISOR_RUNNING；GPU唯一runner PID=749100，显存21746MiB。新请求 **1/116 COMPLETE**，RESUME_WARM_002 RUNNING；六条原结果已通过导入hash校验，未重派。

首条RESUME_WARM_001完成后内存，记录时间2026-11-05T01:05:23.653654+08:00，GC后RSS=10986987520 bytes（10.232430GiB），cgroup current=11034722304 bytes（10.276886GiB），累计peak=23775289344 bytes（22.142464GiB）。这是首条warm基线；后缀峰值和长程40g余量仍以本run逐请求日志为准，未据此宣布完整OOM修复验收。

native_states位于新 **/dev/loop53 ext4**：镜像`.sync/storage-reservations/native-sensitivity8-resume-r3/output.ext4`，68,719,476,736 bytes，inode4428894995；新卷output_device=1845。旧r2输出及原r1 Native状态仅只读挂载，未修改、移动或删除。

正常回执在`reports/cara_sensitivity8_resume_r3_20261105/`：linux_cpu_entry_failure.json、linux_cpu.json、storage.json、admission.json、central_reservation.json、start_confirmation.json。后续只用上文status/capture→唯一settle→CPU score→analyze命令及原句柄验收；此次确认后已停止远端检查，仅提交Mac交接与回执，运行stage源码/manifest不再改动。
