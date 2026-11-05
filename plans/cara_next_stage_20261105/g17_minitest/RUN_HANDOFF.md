# G17 mini-test with-nonfast 执行交接

终验完成（2026-11-05）：原GPU30/30完成，于北京时间16:30:36.722关闭，容器退出0、OOMKilled=false；原guardian/supervisor/runner均结束，GPU释放、Default恢复、双锁释放。seq100唯一结算actual **1.787543629149182GPUh**，累计 **230.13805245018418GPUh**，本卡2.5预留解除，旧16.5未知责任保持。原billing哈希字节不改，stage/central-settlement.json与release.json记录已结算。

CPU scorer于北京时间17:30:15.858退出0，28/28完整93帧、CUDA=false；原analyze完成。科学结论 **INCONCLUSIVE**：G17−F17 mean ΔAlex−0.021834，95%描述性CI[−0.052514,+0.008846]，2改善/2退化；三快臂mean T_DD≤132.98s。tail相对G17 mean+0.004018，2改善/2退化；N3复现+0.070686，主要为light C及丢掉D27/D30，late A不解释损失。M5f预测G22<G19<G17<F17，实测mean为G17<G22<F17<G19，未改拟合或阈值，未做n=4非劣检验。

完整逐输入、分解、G19/G22、固定M5f预测对照与原件见[COMPLETE_RESULTS.md](../../../reports/cara_g17_minitest_nonfast_r1_20261105/COMPLETE_RESULTS.md)。本run已关闭；下列为原启动记录及已执行验收命令，只恢复原交易/原评分，不重启、不再预留或重复计费。本次零GPU新增，未改guardian门限，无监控/automation。


2026-11-05用户经研究助手明确批准with-nonfast：`cara-g17-minitest-with-nonfast-r1-20261105`，28正式＋2warm，报价中心2.225452351GPUh，硬限2.5GPUh。只授权manifest_with_nonfast.json；base仍为quote only，不预留、不执行。初始只读确认中央job不存在，服务器stage/输出/容器不存在。

|方案|正式＋warm|中心GPUh/墙钟小时|工程范围GPUh/小时|建议硬限GPUh|
|---|---:|---:|---|---:|
|base（未授权）|20＋2|1.675519573|1.431485711–1.797536504|2.00|
|base＋19D/22D|28＋2|2.225452351|1.881430711–2.397463171|2.50|

base墙钟中心约1小时40分32秒；加非快臂约2小时13分32秒。增量8请求中心 **0.549932778GPUh**，范围0.449945000–0.599926667（同一进程加入，不再重复warm/模型加载/释放；另开卡需重报价）。范围是工程预测，不是统计CI或跑完保证；本次只批准扩展档2.5GPUh硬限。

|arm|正式请求数|完整request报价秒/次|
|---|---:|---:|
|G17|4|196.796789|
|G17_TAIL|4|196.796789|
|F19_A1_LIGHT_C|2|205.371531|
|F17_ORIGINAL_C|2|201.544361|
|F19_A2_LATE4_LIGHT_C|2|209.347354|
|F17_D27_LIGHT_C|2|202.575093|
|F17_A2_LIGHT_C|4|195.802833|

另2warm：O1的F17-A2-lightC＋F17-original-C各一次，预算分别195.802833/201.544361s，不计正式结果；无Native timing请求。可选G19/G22各四输入，单次完整请求预算216.305043/233.639957s，新增8请求。base总22、扩展总30。

报价锚来自CAL35已接受clean完整T_request均值：Native314.536221s、F19-A1 212.388954s、F19-A1-lightC205.371531s、F17-A2-lightC195.802833s。只拟合时间，未拿LPIPS调报价：T_request=70.734852+6.772260·nD+0.993956·nA+0.637948·nC(original C)。light C项为0，shared项含其共同边界及guard/decode/write开销，模型加载另外列。confirm4实测F17完整请求均值192.225969s；保留较高的CAL35锚，不额外打折。中心=1.1×请求合计+600s加载+600s释放；低/高=0.9/1.2×请求合计+同一1200s。无state IO费用；每请求GC在原runner中保留，其未单列代价由波动覆盖。

四条同批F17正式对照增量中心约0.239315GPUh。两次历史卡的四个核心请求/采样/计时源码与当前逐文件SHA相等，seed0、Cosmos网格、配置与GPU UUID相同；但历史数据分属批次。小额加价换同批T_DD与配对LPIPS，故加入4条。历史F19-A1只在N1/N3作LPIPS诊断参照，Native视频SHA与本卡一致，不借旧时间声称同批加速。

mask全部36，计数见预注册/manifest。G17-tail按1-based交换13/27，无歧义。G17/G17-tail为17D/11A/8C；F17-D27为18D/10A/8C；G19/G22分别19D/17A/0C、22D/14A/0C。生成G17的132.63s及可选151.35/169.23s是模型T_DD预测，不是本卡实测，也不是完整请求报价。长A运行仍需真实测量；不以预测18%LPIPS收益当作结果。

本地CPU检查已用原SpeedOwner/cache/RF/UniPC的tiny模型，在flow false/true各跑九角色共18条完整36步，实际action匹配、无fallback、有限值、CUDA=false；另有paired-summary合成控制。`cpu_check.json`是小模型证据，非Linux真实入口准入。未做新的百万布局穷举或重新拟合，导入报告保留原字节及其/workspace历史脚本路径。

本地复现（无GPU、无远程调用）：
```sh
P=plans/cara_next_stage_20261105/g17_minitest
.venv/bin/python "$P/prepare.py"
.venv/bin/python "$P/cpu_check.py"
```

manifest提供可直接供既有`plans/cara_next_stage_20261104/sensitivity/runner.py`加载的role/matrix；复用`wcomr.cara_f19_speed190_requests_r1.Requests`，不是新的采样框架。`postprocess.py`只在正常release/capture/唯一settlement后、原CPU评分环境（2核/8GiB、既有Alex权重与PIQ依赖、GPU隐藏）执行完整93帧LPIPS，analyze单独计算固定paired CI；启动本轮不调用评分。原Native视频路径与SHA在native_references，未来GPU/CPU环境须按原只读方式挂载这些输出路径。

按既有sensitivity ops/runner流程接本卡stage/launch binding、Linux生产CPU入口、私有卷及fresh准入；源码在GPU前commit+push，然后唯一预留2.5GPUh及启动。输出计划为manifest.output_root中的collection.json、requests/<id>/*.mp4和<id>.pt；无Native states。本轮新建16GiB私有卷；40g容器、50GiB宿主内存、90°C、4GiB低水位及既有温度/硬限保护不变；无监控/heartbeat/cron/automation。


只读status（从Mac仓库根目录，每次使用新的receipt文件名）：

```sh
P=plans/cara_next_stage_20261104/sensitivity
M=plans/cara_next_stage_20261105/g17_minitest/manifest_with_nonfast.json
.venv/bin/python "$P/ops.py" status --manifest "$M" --route relay --receipt /tmp/cara_g17_nonfast_status_manual.json
```

终态后capture→唯一实际settle；响应丢失只恢复同一交易，失败费用照常结算：

```sh
.venv/bin/python "$P/ops.py" capture --manifest "$M" --route relay --receipt /tmp/cara_g17_nonfast_terminal.json
.venv/bin/python - <<'PY_SETTLE'
import json
from pathlib import Path
c=json.loads(Path('/tmp/cara_g17_nonfast_terminal.json').read_text())
Path('/tmp/cara_g17_nonfast_settle_input.json').write_text(json.dumps(dict(capture=c,launch_sha256=c['files']['launch']['sha256'])))
PY_SETTLE
.venv/bin/python "$P/ops.py" settle --manifest "$M" --route relay --input /tmp/cara_g17_nonfast_settle_input.json --receipt /tmp/cara_g17_nonfast_settlement.json
```

30/30完成、原GPU/进程结束、Default恢复、唯一结算后才CPU score；已有scorer只恢复：

```sh
.venv/bin/python - <<'PY_SCORE'
import json
from pathlib import Path
c=json.loads(Path('/tmp/cara_g17_nonfast_terminal.json').read_text())
s=json.loads(Path('/tmp/cara_g17_nonfast_settlement.json').read_text())
Path('/tmp/cara_g17_nonfast_score_input.json').write_text(json.dumps(dict(capture=c,settlement=s)))
PY_SCORE
.venv/bin/python "$P/postrun.py" score --manifest "$M" --route relay --input /tmp/cara_g17_nonfast_score_input.json --receipt /tmp/cara_g17_nonfast_score_launch.json
# 原CPU scorer退出0且scores.json=COMPLETE_PENDING_ANALYSIS后：
.venv/bin/python "$P/postrun.py" analyze --manifest "$M" --route relay --receipt /tmp/cara_g17_nonfast_analysis.json
```

服务器R=/data20t/gaokuangda/worldcache_workspace；S=$R/.sync/cara-budget-calibration-GPU-g17-minitest-with-nonfast-r1-20261105；O=$R/outputs/cara-g17-minitest-with-nonfast-r1-20261105。进度O/collection.json；日志S/runner.log、host-guardian.log、guardian.json、supervisor.json、billing.json；收尾S/released-score-control/{scores,complete_analysis}.json。路由`~/.local/bin/intranet-ssh two-card`（ops --route relay；FRP优先），不切换正在运行卡的路由。


唯一启动与首条确认（2026-11-05）：

- run_id：`cara-g17-minitest-with-nonfast-r1-20261105`；launch_id：`66164b05160c4c9b8c411ff65bc0871e`；GPU：`GPU-cebf7119-cf03-23b9-e192-cd196332b704`。
- GPU冻结源码：`1f949cb0c76fdb651f885b233762b9fca5b3a794`（启动前已commit+push）；scope：`702fb9d1b5a94aae19dc7ef7637471d425c8550d4259482a6bffc6770be5013d`。科学矩阵、mask、参数、原Native SHA及报价与f88856ac相同；只有执行权限、专属预留事件和CPU/lifecycle接线变化。
- guardian计费/启动北京时间：**2026-11-05T14:43:21.565000+08:00**；Docker StartedAt：`2026-11-05T06:43:23.106975408Z`（UTC）。中心墙钟2小时13分32秒（约2h14m），预计完成北京时间 **2026-11-05T16:56:53.193464+08:00**；工程范围1.881430711–2.397463171小时，硬限2.5GPUh。新工作停止阈值为2026-11-05T17:03:21.565000+08:00，硬截止2026-11-05T17:13:21.565000+08:00，保留既有600s释放余量。
- 实际路由：FRP `two_card_relay`，经`~/.local/bin/intranet-ssh two-card` / ops `--route relay`，未退Tailscale。
- 中央唯一预留：**seq99 G17_MINITEST_NONFAST_WHOLE2_5_RESERVE，2.5GPUh**。预留前 used228.350508821035/reserved16.5/历史格式available5.1494911789650075；预留后 used228.350508821035/reserved19.0/历史格式available2.6494911789650075。cap250为兼容字段，不是新的累计政策上限；19.0=旧16.5未知责任＋本run2.5，实际累计仍为228.350508821035，最终按guardian实际唯一结算。
- Linux生产入口导入及60条完整tiny请求通过，原CPU退出0、CUDA=false；fresh准入MemAvailable=58596474880 bytes（54.57221984863281GiB）、目标卡空闲，资产/源码/双锁/存储通过。
- 新卷`/dev/loop54` ext4，image为`/media/minchen/4def5c03-8324-4cba-ac0b-9fda7c79dc7b/gkd/cara_cal66_sm86_workspace/.sync/storage-reservations/g17-minitest-with-nonfast-r1/output.ext4`，17,179,869,184 bytes（16GiB），输出设备1846；容器输出bind为该卷上的本run输出，未写旧卡卷。低水位4GiB；Memory=MemorySwap=42,949,672,960 bytes（40g）；50GiB宿主门、90°C自动停保持。
- 一次前台有界启动确认于北京时间2026-11-05T14:45:29.088435+08:00结束：Running=true、OOMKilled=false；guardian PID1140332、supervisor PID1140417、runner PID1140461的原PID/start ticks均存活；目标GPU唯一runner显存24,418MiB、Exclusive_Process、59°C；collection状态RUNNING、0/30完成，首条G17MINI_001 RUNNING。未等待首条结束或整卡完成。确认读取已退出，不留监控、heartbeat、cron或automation。

正常回执：`reports/cara_g17_minitest_nonfast_r1_20261105/`中的precheck.json、linux_cpu.json、storage.json、admission.json、central_reservation.json、start_confirmation.json。此确认后停止远端操作；后续人工只读status及终态capture→唯一settle→CPU score→analyze用上文命令，不重复启动、预留或评分。
