# 684 — 104 R2技术半程：81路径完成，终态检查提前

实际收件2026-10-24 19:27:58（Asia/Shanghai），文件名1925是调度标签。唯一launch `eee11fe8-c801-4e11-9e53-15b5a6040863`保持：81/104完成、1运行、0失败；原guardian/supervisor/runner/container均存活，原锁仍持有，错误行为空。

GPU3为Exclusive_Process，唯一原runner1280552/start960555843/UID1000，无MPS。9278条连续监测（9276条已授予上下文）无违规、无坏行、无尾行损坏；最大间隔3.013秒。该完整运行前缀不代替终态独占接受。

StorageGuard通过。独立32GiB输出卷可用32766214144字节（30.52GiB），20T普通用户可用1416706490368字节（1.29TiB）；挂载设备、镜像inode、实体预分配与容器绑定保持。独立/data1上的48MiB日志supervisor/guardian/telemetry可读，遥测匹配原launch和runner，样本年龄2.10秒；运行中尚未产生终态billing/accounting，属预期。

瞬时88°C、SW Thermal Slowdown Active、SM855MHz；HW Thermal Slowdown Not Active。17:37未触发软件温控只是当时快照，本次再次记录温控。保留为终态计时可信度评估的技术证据，不改变功率/频率/方法/预算，不据此提前判断科学结果。

只读request.json文件mtime计算节奏，未读取部分科学时钟、视频或分数。81个完成文件的80个间隔中位242.12秒，最近5条均值269.81秒，最长305.64秒。剩23条按现有节奏外推约21:00–21:30完成采集；释放GPU及最多1.5小时CPU评分后，暂估22:30–23:15具备完整验收条件。诊断路径、温控和评分实际开销可能使估计延后，不以ETA代替完成。

监测单调已用约5.776GPUh，距11.9上限约6.124GPUh，非结算账单。池used140.60066151587193/reserved28.4/available56.99933848412807/cap226；旧两卡16.5未知责任保持。完整104范围、原alpha、部署257.7712338712067秒不变。

本次半程自动化cara104-r2已删除；现有终态cara104-r2-2改为10月24日23:15，保持同launch，无新派发或重复检查。若届时仅CPU评分中，继续原句柄并改绑原检查；完整接受后才按681/673/674及冻结接续方案分析。

原件：[半程](../reports/cara_history104_R2_halfway_20261024_1925.json)、[存储/日志/独占/节奏](../reports/cara_history104_R2_storage_journal_cadence_20261024_1925.json)、[瞬时热状态](../reports/cara_history104_R2_thermal_readonly_20261024_1925.json)。
