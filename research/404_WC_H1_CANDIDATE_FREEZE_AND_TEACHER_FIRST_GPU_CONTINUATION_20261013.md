# H1候选冻结与teacher首velocity真实执行

2026-10-13。接续[403完整结果及研究设计](403_WC_ABSOLUTE_H1_COMPLETE_RESULTS_HIGH_FIDELITY_AND_NEXT_20261013.md)，本文件记录执行与准备，不新增科学结果。

## 1. 已启动的完整GPU实验

400的完整 `WC-SAME-STATE-TEACHER-FIRST-VELOCITY-FULL270-SUFFIX8-R1-20261013-A` 已单次提交并通过真实准入。原H1的全部GPU和CPU已结束；新supervisor563522、post watcher563523以及runner均真实存活，kernel由原supervisor持有，第90作业在途。原source `4b18478e1f414b16a0e63ad746a37afd8c776479` 的665文件全部保持；完整CPU回执与实际命令同版本。初始化不能算teacher标签、视频或方法结论。

完整范围仍为四固定父、八完整后缀、四新同状态D teacher pairs，270pairs/540CFG、12视频；预测1.811752758GPUh，单次≤8自主额度内。离线D先恢复，两首缓存仍按C维护，仅teacher臂首返回c/u velocity替换一次，然后相同π0。所有原件审计及12视频全93帧评分由原post执行，完成后独立重构四状态的正负终点和未来动作。

只跟踪原stage/handles，不因观察超时重启、不改在途代码、不并发下一GPU。见[单次启动回执](../reports/wc_teacher_first_velocity_r1_GPU_launch_20261013.json)与[只读现场](../reports/wc_teacher_first_velocity_live_or_terminal_capture_20261013.json)。

## 2. 独立确认候选已冻结，原模板与输入未改

以完整403开发结果为依据，明确选择 **TABLE_PHASE_H1 / SOURCE_PHASE** 作为高保真候选，和Native、RA、A_NO_P、P_OFF一起进入确认。冻结lambda525.1463509809399、原gamma、来源/支持/保护规则及当前执行器；不使用每场景赢家、确认终点或teacher结果调参。

[独立冻结回执](../manifests/wc_source_conditional_confirmation_candidate_freeze_r1_20261013.json)绑定开发GPU source595382e、记录commit be24dd6、完整独立分析、源码与参数hash；方法fingerprint `34ef948ed2a309e8b1cae4b72b780c14e21d63383fa1eadcdfc8803c3d5beef8`。输入选择不重排，四新提示词×seed17/43、五方法40正式＋10CAL预热保持。原protocol和manifest的历史 `candidate_frozen=false` 未改；本次选择通过新回执独立记录。

401完整240种子CPU和402完整50生产模板CPU均已通过。**模板仍明确CPU-only、禁止GPU，不把旧模板回执当作最终封口。** 下一步从原模板生成独立最终配置、绑定本次freeze，验证实际命令、完整50输出范围与40×93自动评分入口后，再串行提交。模板完整费用6.561346751GPUh，最终卡仍核对整体费用、输入/算法和新source；不是将旧E2卡或暂缓P卡转用。

## 3. 当前预算和优先级

提交前实际68.668097882/cap104.971363333，余额36.303265451；现在账本used=cap是本卡在途保守预留，不是已经花完36.30GPUh。结束按包含加载、teacher、恢复、全部后缀、视频与清理的完整wall结算。

先跟踪400，同时准备冻结候选的最终确认入口。继续保护固定mask/匹配实际成本归因、稳定测速、P真实费用profile与单覆盖轴；不要求本诊断正结果才确认强锚点。旧E2完整76的准确批准、用户暂缓P13h保持，严格单次>8才另问。无OMR、训练或人工评审。
