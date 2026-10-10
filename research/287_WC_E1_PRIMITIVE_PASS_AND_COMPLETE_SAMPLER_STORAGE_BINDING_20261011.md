# E1附加状态部件已验收，接入原完整CPU恢复控制

2026-10-11。[286事前登记](286_WC_E1_CPU_STORAGE_PRIMITIVE_PREREGISTRATION_20261011.md)已实际执行，source b77ac304f0842a70a53386e6f2701d69ae0dc9e0，监督4039851／子4039852均结束，具体PID以[原字节回执](../reports/wc_e1_CPU_owned_snapshot_r1_terminal_20261011_capture.json)为准；CPU监督2.479312秒、fixture0.255734秒，exit0且子消失，GPU0／账本不变。四正控制与十一拒绝均通过：13张量对象／五storage、逻辑15892bytes／唯一4896bytes；别名、快照独立、原deepcopy完整恢复及后续24更新相等，不消耗RNG。[独立终态核对](../reports/wc_e1_CPU_owned_snapshot_r1_independent_terminal_20261011.json)。这不是实际Cosmos显存修复结果。

## 新的最小运行改动

新owner继承原CurrentBirth owner，只覆盖附加检查点存储和串行恢复准入。原controller、readout、P行选择、真D锚点、全sampler与原verifier／原件审计均保留；SourceRA owner不改，旧源不回写。每次恢复同时保留附加和physical状态fingerprint。

原physical snapshot建立前的“两份设备复制＋workspace／prefix余量”检查保持。snapshot已经存在后，下一动作分别为physical恢复或own恢复：设备free与当前已驻留物分开，前者要求下一份physical逻辑复制＋原完整reserve，后者要求一份own唯一storage＋原完整reserve。CPU own快照不额外持有GPU副本。保留组合6GiB logical cap，CPU完整backing storage另按6GiB限额。没有降低workspace、改变torch或调用empty_cache；阶段记录allocated／reserved／free／峰值，真实GPU仍待测。

## 受影响完整CPU验证登记

复用既有完整fixture，**不新增场景／密度／阈值网格**；由于本次改变所有dynamic路径的恢复部件，原两种P历史／flow开关、八方法及末写出失败／截断／来源误标等控制均保留。128成功＋128故障控制完整路径，9216实际UniPC更新／18432net、4736成功tensor重读、1024总恢复；其中896个非SourceRA附加恢复须实际使用新CPU storage并记录两阶段guard。旧数值fixture与原保护测试不删除。

输入仍为Toy权重／attention／prepare／视频writer；完整真实UniPC与冻结WC／RF源码用于接线和恢复等价。当前仅新源码与完整CPU范围登记，尚未执行或验收此新sampler版本。完整CPU成功后，再冻结真实GPU冷启动／短前序区分卡，不能由primitive通过直接重投旧64。

E0的AV28组合正信号、Human缺prepare、原64 FAILED_TECH和阶段A独立确认完整72范围保持。新GPU0，预算39.183807748／77.895246590，新48余额38.711438842。无新增人工评审。
