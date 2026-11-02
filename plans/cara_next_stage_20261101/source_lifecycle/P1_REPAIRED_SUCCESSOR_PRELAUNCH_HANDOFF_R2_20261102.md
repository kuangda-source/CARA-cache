# P1 修复后新单次 R2：准备完成，等待独立批准

先读[完整审批卡](V1_P1_REPAIRED_SUCCESSOR_SINGLE19_REVIEW_R2.md)、[新授权草案](V1_P1_SUCCESSOR_SINGLE19_AUTHORIZATION_R2.json)、[源接受](../../../reports/cara_v1_P1_successor_source_accepted_r2_20261102.json)和[整卡CPU](../../../reports/cara_v1_P1_successor_whole_CPU_accepted_r2_20261102.json)。当前未授权GPU/新卡中央事务，不能执行bind/中央准备/预约或dispatch。原R1已失败释放、4.933201964GPUh唯一结算且三个检查删除；禁止重放原R1或重评其部分结果。

## 新卡固定身份

run cara-source-lifecycle-V1-P1-full146-r2-20261102；launch 498503f9cfd249f1aab929da18f04e10；source 8cc9b30a2b08b25c23fa7c38ef63a7b64d456f99；registration 8367f1f9877a495a2dd203c711f6d498155a64135a00da21a22f8a16aef49884；stage /data20t/gaokuangda/worldcache_workspace/.sync/cara-source-lifecycle-V1-P1-GPU-a6000-full146-r2-20261102；仅two_card原A6000 GPU-cebf7119-cf03-23b9-e192-cd196332b704。科学scope 97c6941ebded8e829d1ba28e5f71e868aa781e20b2075fd9062c5abe47ebaad1，完整146语义/最多142物理/5176pair/64标签、19D22D，报价18.050670925709685GPUh、建议硬19。源1473和存储64GiB/48MiB已接受，原CPU/存储进程均结束；禁止再prepare它们或重新评分。新GPU未开始。

## 用户批准后才执行

1. 将用户对**本张新单次19和本卡原账本事务**的明确原话/问题ID写入新授权，execution_authorized/central_transaction_authorized=true、authorization_basis=DIRECT_USER_SINGLE_CARD，记录实际授权时间；其余身份/完整范围/19/50/40/8/12/90C/600秒不改。本草案不授权24GPUh增额，余额不足停等。
2. 仅用`python3 scripts/cara_p1_successor_control_r2.py`，输出新的唯一reports回执。使用原私有Tailscale入口；不改Clash/路由、不自动切LAN。先status核原R2，任何原意图/活跃/UNKNOWN只恢复；无原运行时bind一次，再admit完整生产资产。源prepare/capture和全部CPU/存储已接受，不再调用。
3. 四卡只准本新卡原账本事务。新central-prepare一次，仅在批准后创建持久化缓存 `/data20t/gaokuangda/worldcache_workspace/.sync/source-lifecycle-P1-central-operator-498503f9cfd249f1aab929da18f04e10`（原115文件闭包），不迁账本、不做实验。已有缓存只central-status/recover。原RPC saved碰撞已修复；不因网络未知重复收费或预约。
4. 资源通过后，在60秒窗内reserve --input 原完整admission（过期用refresh，不重扫已验资产内容但重核stat/设备/宿主/存储/独占）。中央快照过期central-status取同一envelope，再dispatch --input 原中央回执一次；任何已有意图只status恢复。不得降低50GiB门、停止别人的任务或换卡。
5. 验证原guardian实际epoch、PID/start ticks、supervisor/runner、容器和唯一CUDA，保存实际启动。按实际开始+预计完整时长的1/4、1/2和预计结束+约5分钟安排3个单次安静线程heartbeat；硬截止固定开始+19小时、600秒余量。若资源等待，保留同一个安静准入检查，批准不重问；只在有意义进展/完成/失败/需用户行动时通知。检查仅运维计数/温度/资源/独占/账本，不读部分分数；可按计数/墙钟前移同一终验。

## 终态与完整验收

先status取完整原lifecycle/launch SHA，核全部原进程/服务/锁释放和Default，settle --input原terminal capture唯一结算guardian全段实际GPUh，成功失败同样处理；UNKNOWN先恢复原事务。失败不后评分/冻结，不自动新卡，保存完整记录后删除所有剩余检查。

完整GPU成功退出、释放且结算后，在原stage固定source调用 `wcomr.cara_source_lifecycle_p1_artifacts_r1.released_artifacts(capture,expected_launch_sha256,settlement)`，完整接受146语义/64标签及RGB/等价门，再用原internal-score-environment绑定 `bind_post_scorer` 和原 `score_dispatch.dispatch(stage,packet,config,registration_sha256)` 一次至多32新CPU对，复用本卡封存内部FIT组成52位置；CPU已有intent只recover。原 `report.complete(stage)` 完整汇总双时钟/93帧/实际校准费用、一次原FIT冻结，`result_bundle export` 原字节及SHA取回本机render。不得重选旧赢家或重评原冻结/旧R1部分指标。更新canonical/完整研究记录、精确提交推送，完成后删除监控。保留四旧CAL/曝光CHECK、WC/RA FIT UNMATCHED与最终/备用16保护输入。
