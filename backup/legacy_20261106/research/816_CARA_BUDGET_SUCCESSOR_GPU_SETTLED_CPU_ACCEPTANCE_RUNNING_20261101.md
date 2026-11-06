# 816 — 预算搜索原GPU完成结算，完整CPU验收运行中

原单次14GPUh卡已完成112/112路径，原GPU容器退出0、无OOM，四个原PID/start ticks均结束，设备锁释放且计算模式恢复Default。原guardian从2026-10-31 16:45:04.590671至23:56:56.112259记录完整25911.521343秒，实际 **7.197644817485577GPUh**。原中央账本唯一结算通过，原14GPUh硬限未超；此前失败卡0.002315298GPUh单列保留，没有重派GPU。

中央结算后快照：cap226、used190.98418827495934、reserved16.5、available18.515811725040663GPUh，旧16.5未知责任保留。本卡只有一次结算事件，未改变其他作业。余额只是该时点记录，不是新GPU授权或未来实时准入。

## 完整科学验收尚未结束

技术/费用接受不等于搜索赢家已经接受。原完整读者必须核验112个完整工件、全部51次双FIT查询、原Native/allD与计时开关等价、源/精度/身份及完整RGB后，才写一次冻结；当前没有读取或发布赢家分数、mask、LPIPS或端点速度结论。

第一次CPU提交在SSH banner阶段失败，随后只恢复原句柄；首次恢复亦超时，第二次明确原CPU stage与精确容器均不存在后，才执行首次实际CPU启动。没有重复启动原GPU或存在的CPU。

CPU容器`cara-budget-successor-accept-CPU-a6000-r1-20261101-cpu`于11月1日00:18:07启动，原container PID2654005；原reader PID2654036/start ticks675839119。00:20:01观察原reader仍活跃、无终态。资源固定2CPU、CPU26/27、8GiB/无额外swap、无网络、只读源码、无GPU；工作上限3600秒，超时收尾30秒。唯一命令调用原GPU stage里的固定源`accept_cara_budget_complete_r1.py --freeze`，没有修改实验源/配置。

新增运维入口只负责这个CPU读者的独占创建和恢复；存在stage时prepare也只恢复，UNKNOWN不重派。六项本地控制验证缺席capture不创建、已有stage不重复、无容器但有意图不重派、GPU暴露拒绝、worker改变拒绝和其他launch拒绝。该运维入口不实现新数值算法、不替代原112/51验收。

## 继续接受

同一个`14h-2`终验已改到11月1日00:30。只能使用`cara_budget_successor_accept_transport_r1.py capture`恢复原CPU，不能再次prepare或重新评分。成功终态返回accepted/frozen/collection原字节及SHA后再保存原件、汇总完整搜索，并删除终验；真实失败则保留失败、不冻结。半程14h保持已删除。

原A32冻结、B36/S/Q完整接受、WC/RA FIT UNMATCHED及四旧CAL范围保持。未自动进入下一张端点GPU卡。815评审文档的旧快照保留，并增加本次GPU完成/CPU待接受的时间说明。

- [完整运维汇总](../reports/cara_budget_successor_GPU_settled_CPU_running_r1_20261101.json)
- [原GPU终态](../reports/cara_budget_successor_final_capture_r1_20261101.json)
- [原中央结算](../reports/cara_budget_successor_final_settlement_r1_20261101.json)
- [释放独立接受](../reports/cara_budget_successor_final_release_accepted_r1_20261101.json)
- [原CPU启动](../reports/cara_budget_successor_final_CPU_launch_r2_20261101.json)
- [原CPU句柄](../reports/cara_budget_successor_final_CPU_capture_r3_20261101.json)
- [运维入口六项控制](../reports/cara_budget_successor_final_CPU_transport_checks_r1_20261101.json)
