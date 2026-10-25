# CAL66迁移至两卡A6000：完整66、同一预算责任

用户明确授权先准备两卡迁移、准备好直接推进，并按实际启动安排半程和最终验收。原四卡R2尚无GPU提交，等待自动化已暂停，不能双边启动。新run为`cara-shared-cal66-a6000-r1`，当前新CPU stage为`cara-shared66-full-a6000-r3-20261025`。

## 已完成准备

- 四卡已接受的模型、runtime、Python/Torch/CUDA、评分资源及三组历史桥接原件，通过局域网复制到两卡隔离目录。传输两端exit0，临时受限传输密钥已移除；未改旧两卡workspace。
- 相同Docker镜像已导入。新主机控制Python已实际运行通过，UID1004；Docker权限仅通过本次进程组授予，未改系统用户组。
- 新32GiB ext4独立预留输出卷与系统盘48MiB日志已建立，StorageGuard通过；不使用共享盘root保留块。
- 新报价完整重算为7.767292 GPUh，上限8；原66/alpha/强基线不变，累计226及最终部署min(257.7712338712067秒,.8freshNative)不变。

## CPU打包问题与处理

首个迁移CPU在真实冻结类入口及9项批处理控制后，动态加载的采样测试文件缺失，exit1，无GPU。检查还发现父stage注册了旧CPU回执，新阶段若继承它会与新输出冲突；旧原件完整保留。第二stage仅修正回执隔离，仍因相同动态依赖缺失退出，保留原件。第三stage增加静态加字面量动态同目录依赖闭包，不修改已执行stage，真实生产组合CPU正在验证。新回执必须绑定新source与registration，旧CPU不能代替。

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
