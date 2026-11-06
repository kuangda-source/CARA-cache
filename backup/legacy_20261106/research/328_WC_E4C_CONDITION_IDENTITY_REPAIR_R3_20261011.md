# E4c 条件身份恢复错误与R3（2026-10-11）

R2原d295bb6／4073838与4073841退出1消失，CPU36.4653秒，载荷与账本保持、GPU0。OFF首个完整父路径写出，ON首个事件自然policy短分支入口被`Changed model/condition/noise/layout requires a fresh request owner`拒绝；之后healthy-boundary拒绝恢复，原链式故障日志保留。完整8父／32suffix／48点尚未通过。

已定位：新增DiagnosticSnapshot的condition deepcopy＋restore_object_state替换了相同值的条件tensor对象，破坏原PartialDeployment使用的id／version签名。不是原条件变化、原方法负结果或GPU泄漏。R3保留原condition对象，保存内容hash和原id／version签名，在每次物理及owned恢复前后严格检查它们不变；禁止悄悄修复条件变异或改部署_identity。

原two-copy物理gate、6GiB逻辑＋8GiBworkspace保护与CPU-owned串行恢复、P positive floor、真D锚点和四事件不变。R1/R2失败、提交与原目录保持；新378完整CPU载荷重新绑定，CPU全范围不缩。对应科学卡仍248pair／496CFG，未选择GPU；不会把OFF首父成功当全范围成功。
