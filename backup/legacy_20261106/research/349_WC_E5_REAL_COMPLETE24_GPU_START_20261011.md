# E5 真实24路径卡已准入，原完整CPU正结果保留

2026-10-11。承接[348完整CPU验收](348_WC_E5_COMPLETE_CPU_ACCEPTANCE_AND_REAL24_ENTRY_20261011.md)与[347事前全范围](347_WC_E5_COMPLETE24_ACTUAL_ENTRY_AND_COST_PREREGISTRATION_20261011.md)。完整Toy／native head链路已证明可以实际省18／34次head并保持444项输出比较和96次恢复；当前新增的真实GPU卡将验证同一实现用于真实权重时的完整数值、决策和含取证成本，不把CPU次数直接换算为GPU净收益。

## 实际生产CPU与整卡准入

[原生产CPU回执独立捕获](../reports/wc_e5_head_complete24_production_cpu_r1_terminal_20261011_capture.json)：source `eff2b71bbd888f4576a2c1c159c394d72ba62fe9`，原4102617／4102619退出0并消失，48.484501秒；456源码／225输入helper保持。实际四块派生、四无guardrail入口、13合同改变、四启动资产拒绝、八准入拒绝及四真实监督器隔离CPU生命周期全部通过，Meta精确复用，无CUDA／GPU或账本写入。

[完整GPU启动回执](../reports/wc_e5_head_complete24_gpu_r1_launch_20261011.json)唯一选择独立目录 `.sync/wc-e5-head-complete24-selected-r1-20261011`。全部24路径／四加载／864更新／1728CFG／0teacher／96恢复范围保持，预测5.126846282GPUh，依用户本次≤8GPUh授权自动执行。准入前指定A6000为24MiB、无compute app，架构8.6；共享锁可用、输出磁盘free379212382208字节，超过完整输出12GiB保留。源与CPU proof绑定通过后由正式supervisor持锁准入，第79个作业已登记。

## 最新现场与边界

[原句柄与456字节核对](../reports/wc_e5_head_complete24_gpu_r1_live_20261011.json)：Unix1791691707.915，supervisor4103103／唯一model4103190／终态CPU等待器4103104均存活，命令行匹配冻结stage与source。A6000为24450MiB，唯一compute app为原model4103190。AV_R1加载92.591613秒，共享eval／原生后端／历史WC配置通过，首LEGACY_OFF已进入完整guarded管线；现场记录0更新、0完整路径，**尚无新GPU数值／视频／耗时结论**。其余三块全部未开始位置保留。

只跟踪原句柄，不重投、不改在途payload。24条范围全部完成或技术停止后，唯一4103104等待器自动读取原件：完整24 vector／888张量、12新旧对444直接比较、12同版本顺序重复另444比较，以及所有有效视频的93完整RGB帧／PTS／timebase；视频拒绝、部分与未开始位置保留。读取与GPU费用结算独立，终态仍须独立capture后才能宣布结果。

当前前实结41.908688946／77.895246590GPUh，新48启动前余35.986557644。现场`used=cap`是唯一在途保守预留，不是预算花完；结束按加载／失败／搬运／flush的实际whole wall结算一次，整卡授权8GPUh保持。E2／E3原准确above8确认待、不重复问或拆范围；P新工作参考保持数学组件阶段。本轮没有新增训练、人工评审或OMR。Goal active，原GPU与自动CPU继续。
