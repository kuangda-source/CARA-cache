# CAL66迁移至两卡A6000：完整66、同一预算责任

用户明确授权先准备两卡迁移、准备好直接推进，并按实际启动安排半程和最终验收。原四卡R2尚无GPU提交，等待自动化已暂停，不能双边启动。新run为`cara-shared-cal66-a6000-r1`，当前新CPU stage为`cara-shared66-full-a6000-r3-20261025`。

## 已完成准备

- 四卡已接受的模型、runtime、Python/Torch/CUDA、评分资源及三组历史桥接原件，通过局域网复制到两卡隔离目录。传输两端exit0，临时受限传输密钥已移除；未改旧两卡workspace。
- 相同Docker镜像已导入。新主机控制Python已实际运行通过，UID1004；Docker权限仅通过本次进程组授予，未改系统用户组。
- 新32GiB ext4独立预留输出卷与系统盘48MiB日志已建立，StorageGuard通过；不使用共享盘root保留块。
- 新报价完整重算为7.767292 GPUh，上限8；原66/alpha/强基线不变，累计226及最终部署min(257.7712338712067秒,.8freshNative)不变。

## CPU打包问题与处理

首个迁移CPU在真实冻结类入口及9项批处理控制后，动态加载的采样测试文件缺失，exit1，无GPU。检查还发现父stage注册了旧CPU回执，新阶段若继承它会与新输出冲突；旧原件完整保留。第二stage仅修正回执隔离，仍因相同动态依赖缺失退出，保留原件。第三stage增加静态加字面量动态同目录依赖闭包，不修改已执行stage，真实生产组合CPU已完整接受（428.19秒）。新回执必须绑定新source与registration，旧CPU不能代替。

## 财务和实验边界

四卡中央账本保留累计使用与旧16.5GPUh未知责任。单次启动时才建立8GPUh外部主机预算包；两卡子账本仅能花同一包，最终按原账单回填中央，不重复计费，不使用旧两卡历史余额。未确认提交的旧责任继续占财务额度，但不等于现在持有设备。

本卡是同一A6000批次上的方法闭环：Shared、间隔基线、全A/限龄A、少步Native共同评价。Ada历史桥接即使不同也如实保留，不能混成同硬件重复。完整采集和评分接受不等于最终部署或新DEV泛化成立。

## 接续

新CPU全部接受后，绑定新stage、fresh空闲GPU/磁盘/资源/中央账本，独占单次启动。已有intent只恢复，不重派。按实际起点约3h53半程、7h46采集预测；释放GPU后评分，最多6小时。实际启动、身份和检查安排在同页追加来源。

主要原件：
- [局域网复制](../reports/cara_CAL66_A6000_LAN_transfer_complete_20261025.json)
- [镜像和密钥清理](../reports/cara_CAL66_A6000_image_loaded_key_removed_20261025.json)
- [独立存储](../reports/cara_CAL66_A6000_private_storage_20261025.json)
- [宿主入口](../reports/cara_CAL66_A6000_actual_host_control_CPU_20261025.json)
- [新CPU启动](../reports/cara_CAL66_A6000_CPU_launch_r3_20261025.json)
- [完整报价](../manifests/cara_CAL66_A6000_whole_quote_r1_20261025.json)

## 实际启动与自动检查

- 实际2026-10-25 **23:06:21.473025 +08:00** 单次启动；launch `5d262751-5d8d-4c61-9081-96d816b9d581`。
- source `0af9c31cbfcef6dd57f9cca8c3219726b2b1477c`，registration `cd46c796ef34d67a7cbf17b4839de3d7642243e16209afc207cd072b6b0bae76`；CPU包装第三stage对应同一新GPU run的首次提交。
- 两卡GPU1 / A6000，UUID `GPU-cebf7119-cf03-23b9-e192-cd196332b704`；guardian3755009/start623568499，supervisor3755064/start623568652，runner3755108/start623568828/UID1004。
- 真实Exclusive_Process idle/active与唯一runner grant通过；最新技术快照111采样、最大间隔2.383秒、无前缀违规，已进入首个采集请求。私有卷约31.18GiB可用，系统盘日志最近采样约2.20秒前。前缀健康不替代最终连续监测接受。
- 中央账本已确认本包确有GPU提交：used156.620413、reserved24.5（旧16.5+本次8）、available44.879587/cap226。两卡子账本对应同一8h，不另加到总额。GPU完成并有原账单后用`settle-central`准确回填中央包。
- 半程 **10月26日03:00**（自动化`cara-cal66-a6000`，最早02:59:22）；旧`cara-cal66-r2`已改绑A6000最终验收 **10月26日11:45**。两者都只绑定此launch，无Ada等待启动。
- 预测采集 **06:52** 完成；释放后评分沿保守4.715486h预测约**11:35**完成，6h评分上限不变。实际可提前收件，若11:45尚在评分，复用终态检查调整时间，不能重派GPU。
- 新主机真实93帧三模型CPU探针总157.54秒，其中评分约144.47秒；这不是52视频整批实测，未据此缩减原6h CPU边界。

首次临时技术观察把实时“10秒内”检查误用于历史监测样本，产生STALE_OBSERVATION标签；原件保留，r2与正式只读技术入口改为在样本自身时间回放，并另查当前实时快照。没有修改运行监测或放宽45秒连续性要求。

实际原件：
- [完整新CPU接受](../reports/cara_CAL66_A6000_CPU_accepted_r3_20261025.json)
- [唯一GPU启动](../reports/cara_CAL66_A6000_GPU_actual_launch_20261025.json)
- [准入收件](../reports/cara_CAL66_A6000_GPU_admission_20261025.json)
- [实时独占/存储/跨盘日志](../reports/cara_CAL66_A6000_technical_admission_20261025.json)
- [中央包实际准入确认](../reports/cara_CAL66_A6000_central_admission_confirmed_20261025.json)

后续命令：`scripts/wc_two_card_cara_cal66_gpu_r1.py capture/accept-gpu/settle-central`；技术检查`check_cara_cal66_a6000_technical_r1.py`。UNKNOWN只对`reports/cara_CAL66_A6000_GPU_stage_20261025.json`执行recover，不再次launch。完整终态前不分析部分结果。

## 10月26日02:29–02:30技术进度与检查提前

实查46/66完成、1运行0失败，原四句柄存活、UUID锁持有、错误行为空。5513独占监测样本无违规，最大间隔3.287秒；独立卷30.80GiB可用，跨盘日志采样年龄0.67秒。未读取部分视频/质量，也未用部分请求时钟调参。

仅以已完成request.json的mtime间隔估计：最近20条均值261.10秒，采集预计03:50–04:20；按原4.715486h评分预测08:35–09:05可完整收件。评分仍有6h上限，较慢时可能约10:20才结束。03:00技术半程保留；既有cara-cal66-r2终态检查已从11:45提前09:30，届时若未结束只按实际状态调整同一检查。原源码、α、分母、8GPUh预算和运行stage不变。

证据：[实时技术检查](../reports/cara_CAL66_A6000_technical_progress_20261026_022914.json)、[原句柄收件](../reports/cara_CAL66_A6000_progress_capture_20261026_0230.json)、[仅文件时间节奏](../reports/cara_CAL66_A6000_progress_pace_20261026_0231.json)。实际观察以observed_unix为准，文件名0231仅标签。
