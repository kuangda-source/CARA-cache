# 校准卡生命周期回执的 CPU 控制

2026-10-30。预算搜索新增只读终态回执核验组件，延续B36“成功失败均保留原guardian实耗、科学接受另行判断”的规则。原B36代码、实际费用和冻结未修改，新组件没有派发或账本写入入口。

[14项本地控制](../reports/cara_budget_lifecycle_receipt_local_CPU_r1_20261030.json)通过，使用显式合成的启动/容器/设备记录，以及真实临时文件中的原BudgetPool结算代码。没有访问实际GPU、Docker或中央账本；这一结果不等同于双端生产CPU接受或真实GPU终态。

## 接入与核验

[生命周期组件](../src/wcomr/cara_budget_lifecycle_r1.py)接收派发时保留的唯一launch SHA，逐份验证原始JSON字节、registration/authority/envelope绑定、scope/source/runtime和原终态核验器SHA。授权字段仅用于验证该已绑定启动的原依据，不生成新批准，也不代替派发前审批。

四个原角色必须具有各自身份；观察视图与原boot/PID namespace相符，PID/start ticks和实际退出原因一致。worker启动记录必须与guardian绑定一致。未派容器、Docker CLI已结束但未创建容器、容器init在runner意图前失败，分别保留明确失败分支；不能用缺失记录掩盖已出现的runner意图。

容器终态要求原ID、名称、image、registration标签及唯一GPU UUID相符，原资源锁已释放。费用必须是完整guardian单调时钟差，监督器分项、估计值、零费用替代和不完整时钟均被拒绝。失败、OOM或超限实耗仍可财务结算；超限必须留在账本中，不能报告执行成功。

中央before/after回执维持cap、origin、其它任务和旧16.5责任；只允许原任务的一次实耗事件。再次接收已结算原件要求账本完全不变，冲突费用由原BudgetPool拒绝。原GPU释放与模式恢复分开核验；后来的其它GPU使用不改写原释放证据，也不被当作新准入。

## 已测情形与剩余工作

14项控制覆盖原件与重复接收、默认拒绝CPU夹具冒充生产、launch/source/authority/runtime/envelope不符、存活/UNKNOWN/错误视图/伪造退出、模拟PID复用、错误容器及锁、失败容器实耗、缺少释放或未恢复模式、后续外部使用、三个pre-runner失败分支、不完整费用、超限、旧责任或结算事件篡改，以及worker启动/其它launch释放混用。

该组件只审核捕获到的生命周期回执，始终返回`complete_search_accepted=false`、`scientific_read_allowed=false`、`authorizes_replay=false`。新的真实采集入口、完整监控日志、完整搜索及控制验收、双端受影响CPU、专用存储和整卡报价仍待组合。771的实际Linux身份组件保持接受；本次没有重复启动那个CPU容器。

用户随后明确选择[14GPUh公平预算设计](../reports/cara_budget_14GPUh_design_direction_20261030.json)。该回复确定设计上限，SA/HC轮数和查询数仍待报价组合；未授予实际启动批准。S原运行及其两个原检查保持；本轮新增GPU、预约、中央费用和科学评分均为0。
