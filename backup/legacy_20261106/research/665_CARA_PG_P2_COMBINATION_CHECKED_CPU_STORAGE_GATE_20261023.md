# 665 — PG-P2 整卡组合检查完成本地验证；生产CPU停在磁盘准入

## 结论

P2专用监督/评分/终态组合代码及本地检查已补齐。**75项本地控制、15项独立接受器控制通过；新的远端生产组合CPU未启动，不能写作完整生产CPU已接受。** 当前P1的stage、配置、GPU、预算和检查时刻未修改；本次P2 GPU提交0，账本写入0。按用户最新要求，最终预算等P1结果与物理策略去重后确定，本轮不重新报价。

## 已验证内容

- 518路径设计上限的显式合成整卡分母、346组全93帧LPIPS原件格式、36 shadow D、1600项独立质量位置；失败/未到达/NA身份保留，缺项、错误原件、非有限分数、时间污染和角色改写拒绝。
- 少步Native按实际更新数验收，history耗时不进入部署时钟。历史独立接受要求绑定真实双分支和P1 OFF核验回调，不能用状态标志替代原件。
- P2终态生命周期接受器检查原句柄、冻结来源、授权/费用、独占监测尾部、原容器/锁释放、权威账本及post绑定；新增10项费用/终态控制。
- 六类P2专用真实CPU子进程生命周期、完整93帧真实LPIPS及48路径真实采样入口已接入组合driver，**等待本次新闭包实际运行**。早先R4真实48路径/72请求接受保持有效；不能拿P1的旧六类运行冒充本次P2执行。

本地原件：
- `reports/cara_PG_P2_combination_local_checks_20261023.json`：75通过，实际约79.6秒。
- `reports/cara_PG_P2_combination_acceptor_fault_controls_20261023.json`：1合成正例+14故障拒绝；明确不是生产接受。

## 远端准入与恢复核查

原部署source `07b1b998`，拟定stage `cara-pg-p2-CPU-combination-r1-20261023`。统一SSH包装返回UNKNOWN/exit1，保留原件 `reports/cara_PG_P2_combination_CPU_launch_r1_20261023.json`。随后只读核查发现：连接可用，磁盘准入assertion发生在stage创建之前，stage不存在、CPU容器不存在、原launch不存在。没有未知运行需要重派。

- 原句柄核查：`reports/cara_PG_P2_combination_CPU_original_handle_check_20261023.json`；磁盘39,172,206,592 bytes（约36.48GiB），低于40GiB；内存53,785,882,624 bytes，满足24GiB。
- 只读备选盘核查：`reports/cara_PG_P2_CPU_alternate_filesystem_readonly_20261023.json`；共享盘随后约36.14GiB，home/tmp仅227,086,336 bytes。
- 已结束CPU目录核查：`reports/cara_PG_P2_completed_CPU_storage_inventory_r2_20261023.json`；原失败/成功目录均保留，总量不足1GiB，无法恢复准入余量。第一次库存脚本语法失败原件也保留；它没有执行任何变更。

不降低门槛、不改忙卡、不清理其他用户、P1或历史原件。共享盘余量变化的来源未调查，不能归因于P1。P1本轮未重新轮询，继续沿原半程和终态任务验收。

## 接续

见 `plans/cara_policy_generator_20261020/P2_COMBINATION_CPU_HANDOFF_R1_20261023.md`。资源恢复后新stage运行完整组合CPU并独立接受；P1接受与角色去重后才绑定真实P2整卡runner/模型资源/原件/最终预算。现有终态检查只追加接续说明，时间及P1句柄保持。旧518路/78.5GPUh报价作为历史上界保留，不是当前批准。
