# E5 CPU首轮状态比较停止与R2修复登记（2026-10-11）

原CPU source a9a4d04、4084569／4084571已退出1并消失，25.798320秒。独立核对403来源字节与原回执／log，预算SHA前后相同；原两条OFF完整输出实读74张量，37／37逐元素相同。全12路径及全部状态／故障检查未通过，不把这次记成原型验收。

停止于跨版本状态比较。投影缓存`ProjectionCache.parameter_versions`包含真实参数对象ID，来自两个不同Net安装；直接对这个raw cache整体hash要求相同会把实例身份当成算法差异。R2仅在**跨安装比较**中将每个原ID映射为当前安装的native参数名称；要求原ID确属当前Net，参数version、投影值、更新时间、D／P来源、形状／dtype、trueD等保持严格。raw投影hash也记录，不改任何缓存或guard、不删除版本检查。自身完整physical／owned恢复依然使用全部原ID／原数据严格hash。此解释要由R2实跑确认，不能只凭推测宣布故障消失。

原R1原型、fixture、结果、失败原件与stage不覆盖。R2通过有逆源码检查的三个fixture插入：名字对应、比较排除单独保存的raw installation-ID hash、每路径状态先持久化。受影响完整两Flow／三A／两版本12路径，222直接输出比较、24完整恢复、7动态head拒绝、4真实paired故障等原范围不缩；prototype算法仍为同一R1字节，不改当前E4c／E2／E3。406来源复制至独立CPU R2目录，提交后执行。无新GPU、训练或人工评审。
