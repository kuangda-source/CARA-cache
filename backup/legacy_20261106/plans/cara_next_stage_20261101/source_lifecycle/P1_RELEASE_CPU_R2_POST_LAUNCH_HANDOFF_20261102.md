# 原P1释放读者R2已失败退出

原R2于06:58:37退出1，在合成账本schema处拒绝，未执行新真实评分。原失败/终态保留，两个检查已删除；不得再prepare或执行本原件。R3仅修复夹具并继续尚未接受部分，以下为历史原句柄。

原source `d40835fcaa45630887566689f31e90c8d7eab36f`，唯一stage `cara-source-lifecycle-P1-release-CPU-a6000-r2-20261102`，registration `3d9fddf24eceea6dcb11e0cf4efa6af6faa6b4deefcf80181a66465b65d3e0c6`。原[启动](../../../reports/cara_v1_P1_release_Linux_CPU_launch_r2b_20261102.json)与[首次观察](../../../reports/cara_v1_P1_release_Linux_CPU_capture_r3_20261102.json)；真实开始2026-11-02 06:57:31.452432+08。两卡CPU2配额、8GiB/no swap、CPU26、无网络/隐藏GPU；工作1200秒、退出60秒。项目和原stage不改源，不重启/重派。

只用：

```sh
python3 scripts/cara_source_lifecycle_p1_release_cpu_r2.py capture --source-revision d40835fcaa45630887566689f31e90c8d7eab36f --output reports/cara_v1_P1_release_Linux_CPU_capture_rN_20261102.json
```

每次新唯一回执。UNKNOWN只恢复原stage、容器及PID/原开始时间，不执行prepare。原R1失败已在[850](../../../research/850_CARA_P1_PRODUCTION_BINDING_AND_RELEASED146_SCORE52_PREPARATION_20261102.md)保留；它的21控制用原日志和未变source复用，R2不重跑。第一次R2旧源码块传输未派发已结束，不会成为另一个CPU运行。

原终态成功后，使用 `scripts/accept_cara_source_lifecycle_p1_release_cpu_r2.py`，指定本原launch、终态capture、新唯一accepted和原proof文件。它独立检查注册1412字节闭包、原CPU退出0/资源/时限、21复用且未重放、4新分析控制、146文件/64标签/12恒等/52质量、最多32对新的真实93帧Alex/PIQ、原评分子进程终态、一次意图及预设失败分母。内部host和内部指标在本CPU夹具是明确模拟；真实broker组件继续复用848。任何失败只保存原终态，不在原stage再执行。

[原检查安排](../../../reports/cara_v1_P1_release_CPU_acceptance_schedule_r2_20261102.json)：p1-cpu于07:08半程，p1-cpu-2于07:18终验。仍活跃可调整同一终验；完成后删除二者。原R1两检查早已删除，同名当前ID属于本新R2，不可混同。保持无变化安静。

完整后记录CPU组件接受和边界、更新canonical并精确提交推送。P1 GPU外层准入/dispatch/控制、后置评分实际一次派发/容器恢复、正式图表/生产冻结组合及完整报价仍待；8项本地新容器/worker控制不等于Linux接受。P1没有GPU或本卡中央账本权限，四卡保持禁访。原A32/B36/S/Q/搜索冻结、保护16/备用16、旧16.5责任及原cap226保持。
