# 736｜WC73 热保护停止与精确结算

北京时间10月28日02:55安排的半程检查恢复原唯一句柄，确认任务已于10月27日21:38:56结束GPU计费，21:39:18整卡控制器停止。原监督错误为 `Thermal stop >=90C`；此前热记录89°C。这是运行环境热保护中断，不能解释为数值等价不成立。

A完成11/26：6条warm、5/12条诊断，第6条诊断中断。门禁尚未形成结论；runner/collection留下的RUNNING是退出前快照，不能覆盖supervisor、controller和实际进程终态。未选参冻结、未创建B stage，未运行后评分。73路径整卡未完成、未科学接受；原门槛与既有结果不变。

原controller/guardian/supervisor/runner均退出，原容器退出码1且非OOM；原GPU释放、空闲时恢复Default的回执齐全，目前无匹配锁。检查时GPU已有其他用户任务，未触碰。监督摘要虽然写有CPU_POST_PENDING，真实controller已STOPPED_NO_REPLAY，不能据摘要继续评分或派发。

A实际3530.349914491秒，即0.9806527540253268 GPUh；账单SHA与中央唯一SETTLED记录一致，原12GPUh预约已解除，B费用0。中央cap226、used175.8058597668662、reserved16.5、available33.694140233133794；旧16.5责任不动。

准备CPU已记录任务累计392.277929秒；已知分配vCPUh上界0.161070279，未覆盖未计量部分。权重哈希读取44.500673秒单列；新后评分/质量模型运行0。原费用回执完整复用，未将未计量本地编辑、传输、CLI、存储准备假填为零。汇总见终态验证JSON。

本次未重跑、未修改运行代码/配置或追加GPU。原08:10–10:10完成预测作废，半程wc73与10:10全程wc73-2均已删除。任何修复后GPU执行需另行授权；本轮止于失败证据和释放财务验收。

证据：[半程恢复](../reports/cara_wc73_halfway_20261028_0255.json)、[原终态与哈希](../reports/cara_wc73_terminal_failure_originals_20261028.json)、[独立验证与费用汇总](../reports/cara_wc73_terminal_failure_verified_20261028.json)。
