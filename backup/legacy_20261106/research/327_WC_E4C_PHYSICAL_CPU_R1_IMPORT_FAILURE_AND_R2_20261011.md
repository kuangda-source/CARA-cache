# E4c CPU R1导入故障与R2（2026-10-11）

原9ada1ea／4073467与4073468均退出1且消失，CPU27.9657秒，载荷378原件保持、账本SHA20d8c7保持，CUDA未初始化、GPU0。测试错用了不存在的`ra_joint_control`和未导出CreationPhasePrior的模块。尚未执行父路径、短分支或teacher物理比较，不是缓存方法失败。

失败回执与完整日志独立捕获到`reports/wc_e4c_matched_source_age_cpu_r1_terminal_20261011_capture.json`及native.gz，旧stage不改。R2仅改测试导入为现有cfg_ra_joint_control／source_aware_cpd_control／source_aware_phase_control；方法代码、248pair科学卡和8父／32suffix／48点／776张量CPU范围不改。使用新CPUstage及新payload绑定，完整实际CPU待，不报部分通过。

继续受用户完整单卡≤8GPUh自主、严格>8完整确认约束；E2/E3原完整卡不拆不取消。本次为影响入口修复，无GPU、训练、人评。
