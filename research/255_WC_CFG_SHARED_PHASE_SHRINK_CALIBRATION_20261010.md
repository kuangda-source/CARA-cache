# CFG 共享修正的一参数校准接续

2026-10-10。按用户统一方法设计 MF-A，准备对既有阶段 A 增加一个两分支共用的收缩系数 κ，而不是逐分支或逐层增加参数。原32路径卡仍比较冻结的四种 A，当前运行、原卡分母与271成本卡均保持。

该修订针对一个具体问题：现有 α=1／0.5 是粗格点与有限阶段观察得到的强度，共用 κ 可用同状态真实 CFG 输出的损失直接选择更合适的幅度。它保留原 W1 与无拟合 β=1 两种提议，只增加一个有界标量，不训练生成器或 Head。代价和终点仍由后续完整方法视频决定。

执行前已登记完整八 CAL 起点、两提议和固定相对正则0.1；使用直接合成后的 FP64 矩，拟合 E+2κB+1.1κ²Q。这里的提议已包含原阶段 α，不除回该系数，也不从混合输出假定恢复另一条 FP32 输出。只报告 CAL 同状态目标，不把它叫作物理或 LPIPS 提升。

登记d8cf564并同步Git后已完成纯Python CPU，实计0.033129秒exit0。两个完整八起点拟合均由直接CFG向量重算损失并核对正则导数，三个边界控制及七异常拒绝通过，源与输入保持；CPU合成系数0.787491677仅用于实现校验，不安装为真实参数。[完整CPU结果](../reports/wc_shared_phase_shrink_cpu_r1_results_20261010.json)保留标准输出和全部范围。

真实读取器在完整成本回执与绑定缺失时已实际返回WAIT／exit2，无拟合文件、安装、GPU或账本写入；这是数据等待，不是方法失败。真实拟合仍待。原格点、固定阶段和全部旧负结果保留。

现场1791615122.212929：原32卡27方法视频／27张量，五个原句柄仍存活，四Native尚未开始；GPU只有原runner3929519，下一成本等待器新GPU0，账本SHA保持。[原任务现场](../reports/wc_ra_plus_a_r1_shared_shrink_CPU_live_20261010.json)独立记录当前进度。原完整卡、sourcebeb02c9／283载荷及下一成本271载荷均未改变，目标active/progress。

飞书 revision56→57 已同步共享修正CPU与27方法进度，197块全文核对只改变原指定进度段，其他内容保持；[读回与原件回执](../reports/wc_shared_phase_shrink_feishu_20261010_verification.json)完整保留。没有发消息或改变分享权限。

证据：[执行前方法](../plans/WORLD_CACHE_CFG_SHARED_PHASE_SHRINK_R1_20261010.md)、[登记](../manifests/wc_shared_phase_shrink_r1_preregistration_20261010.json)、[校准核心](../src/wcomr/cfg_shared_phase_shrink.py)、[直接向量 CPU 控制](../tests/check_cfg_shared_phase_shrink_cpu.py)、[真实读取器](../scripts/fit_wc_shared_phase_shrink_real_r1.py)。仅这个小参数修订，无新增GPU提交、预算写入或对在跑源的改动。
