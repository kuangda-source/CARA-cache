# 809 — 端点评分一次派发与有界监督CPU验证

新端点评分的一次性CPU容器派发、原意图恢复和有界监督组件通过两卡21项CPU控制，随后13项独立终态接受检查通过。真实Linux子进程覆盖七种生命周期，包含超时停止、前置/评分失败、未知连接恢复和错误容器拒绝；内部Docker与评分数值为显式夹具。启动回执超时后仅恢复原stage，原容器正常退出。本轮没有新增指标计算、GPU派发、原实验输出读取或中央账本访问。

## 原终态

源码`ed380339dfd537e0a6c34edc489930433223258c`，stage为`/data20t/gaokuangda/worldcache_workspace/.sync/cara-S-endpoint-dispatch-CPU-a6000-r1-20261031`，容器为stage名加`-cpu`，注册SHA为`2d1f105bb73dbf271cd1a9f555b0ad2c978e623bc6ba930f86c1bb18064657f0`。实际21:05:40启动、21:06:12退出/0，Pid=0、无OOM；worker实测30.883964777秒。外层CPU26、1核、4GiB、无额外swap、network none、只读根文件系统、无GPU设备，工作上限300秒、退出余量30秒，均由原capture与源码接受器核验。

Mac启动传输因SSH回执超时返回-9；只读capture随后找回同一个stage的唯一launch、原源码和完整退出终态。保留未知启动回执，不重新prepare、不补造一次成功传输。13项独立接受检查核对源码、外层资源、七种场景完整分母、原句柄退出、未重复派发、外部进程保留、超时确实触发，以及资源快照不能充当未来准入。

## 一次派发与恢复

派发前校验完整工件包和评分配置、原GPU释放launch、注册payload/runtime；只允许明确不存在的原评分容器进入首次派发。已有输出、孤立句柄、源码不符或资源不足均拒绝。配置以规范字节保存，执行意图先独占创建并fsync，再启动原监督进程；已有意图的调用只走恢复，不再做资源准入或spawn。

监督进程先保存原PID/start ticks/boot/namespace和意图SHA，再启动CLI bootstrap；后者同样先独占保存自身身份，才exec冻结的Docker命令。因此即使CLI在评分进程开始前失败，原身份仍可恢复；重复bootstrap在执行Docker前拒绝。生产命令固定2核/8GiB、CPU26/27、network none、GPU隐藏、只读project/stage和唯一可写评分目录，保留原CID文件，不自动删除或重启容器。

监督从自身开始计时，生产工作上限4小时，包含CLI/容器启动等待；原评分CLI自身的4小时alarm保持。超时或中断时先核对原CID、name、image、manifest、入口及资源，再停止匹配的原CPU容器，随后清理绑定的原CLI子进程。停止过程有独立的短超时；容器身份不符或观察未知保留失败/未决记录，不操作其它容器，也不会重新派发。成功接受还要求监督进程本身退出且原终态无错误，再调用808的原容器/原CLI/原worker完整接受门。

七种实际Linux场景为成功、worker失败、worker前失败、缩短到2秒的CPU超时、Docker观察未知后恢复、容器身份替换拒绝、CLI bootstrap前失败。每种都只启动一个监督进程；重复调用不spawn。成功和未知后恢复两种均接通完整24逻辑位置/12新合成行的接受，原CLI和worker句柄确实退出。另一个哨兵进程在各场景中保持存活，测试收尾只停止自身绑定子进程。bootstrap前失败缺少CID/CLI witness时仍保持UNKNOWN，不把失败推断为可重派。

## 资源与证据范围

21项由13项本地边界控制、七种实际进程场景和一次实际只读CPU环境检查组成。最后一项实测可用内存42,823,987,200字节、可用磁盘1,001,469,206,528字节、affinity为CPU26，并核对原Alex checkpoint SHA及PIQ目录。它只证明当时的单核CPU检查环境，不证明未来生产双核准入；正式派发仍重新检查CPU26/27、至少12GiB可用内存、2GiB磁盘和原离线权重/环境。

外层容器是真实Docker运行，内部Docker inspect/stop及评分行数值是受控夹具；进程、exec、signal、PID/start ticks和超时使用真实Linux机制。没有调用新指标网络或重评807的合成对，更没有重评原A32/B36视频。生产评分容器尚未实际派发，整卡CPU仍未接受。

## 下一步

将已接受的释放、工件/RGB、一次评分派发和原容器恢复接到新端点GPU runner/一次派发，完成32/25两种范围的整链CPU，以及24位置汇总/图表。实际预算mask仍等待原112路径/51查询完整接受与一次冻结；之后完成所选策略受影响验证、最终源与完整报价，再取得新卡授权和原中央交易权限。

原14GPUh卡、23:16半程、次日06:01终验、06:45:04硬截止保持，本轮未观测它的GPU状态或读取部分科学分数。A32/B36/原S冻结、科学表行、cap226及旧16.5责任不变。

[原CPU接受](../reports/cara_s_endpoint_dispatch_CPU_accepted_r1_20261031.json) · [原完整终态](../reports/cara_s_endpoint_dispatch_CPU_capture_r1_20261031.json) · [保留的未知启动回执](../reports/cara_s_endpoint_dispatch_CPU_launch_r1_20261031.json) · [独立接受检查](../reports/cara_s_endpoint_dispatch_acceptance_checks_r1_20261031.json) · [一次派发组件](../src/wcomr/cara_s_endpoint_score_dispatch_r1.py)
