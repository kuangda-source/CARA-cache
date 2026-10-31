# E1 七角色范围与完整报价

用户已选择 **B版46路径**（仅范围确认）。它增加F19-C同批重放，直接回答局部风险交换的质量改进是否伴随实际时延变化。推荐仅准备并申请这一张卡。

| 项 | A版39（未选） | B版46（已选） |
|---|---:|---:|
| 四种新增角色×四旧CAL | 16 | 16 |
| 同批Native35/F19-A1控制 | 8 | 8 |
| F19-C同批重放 | 0 | 4 |
| 两CHECK计时重复 | 8 | 10 |
| warm | 6 | 7 |
| allD真实性控制 | 1 | 1 |
| 完整物理路径 | 39 | 46 |
| 新CPU评分对/复用原评分 | 16/12 | 16/12 |
| 预计整段GPUh | 5.298530 | 6.040147 |
| 建议硬限GPUh | 6.25 | **7.0** |

采用原A6000最慢Native完整请求321.402771秒作为每条请求工程代理，所有路径（含warm/控制/重复）均计入；它是有来源的保守估算，不是新策略实测上界。逐项公式如下，不沿用旧32卡5.25硬限：

| 成本（秒） | 39 | 46 |
|---|---:|---:|
| generation_at_slowest_old_Native | 12534.708 | 14784.527 |
| artifact_copy_save_hash | 2340.000 | 2760.000 |
| producer_readback | 1800.000 | 1800.000 |
| admission_and_model_load | 1800.000 | 1800.000 |
| stop_and_release | 600.000 | 600.000 |

在上述全成本之上增加15%并向上取0.25GPUh档。46卡实际余量3455.473秒，原600秒停止/释放余量已经计入预算，不能等7小时截止后才开始释放。90°C停止线不变，失败照原guardian整段实耗唯一结算，不重派。

生产容器：两卡宿主单张原A6000，2CPU、40GiB、无额外swap、无网络，真实EXCLUSIVE_PROCESS及sole CUDA context；不干扰其他用户。计划独立64GiB输出quota、8GiB低水位、准备前至少80GiB宿主空间；本次没有建立新GPU容器或预约。

后CPU：16新对，12行只引用，2CPU/8GiB、2小时上限（4vCPUh），GPUh为0，原GPU释放结算后才评分。逐视频流式处理，完整单视频float32 RGB约0.345GiB，避免保存46份未压缩RGB。原artifact/latent持久化、最大实际磁盘占用须在生产打包核实，不把这些估算写作已验资源。

计时：同一请求内平均正式与注册重复，再四prompt等权；同批Native均时除方法均时。warm/allD不入干净速度均值；Uniform旧时间仅作为历史参照，不能称同批。FIT与CHECK分别展示，旧CHECK不作独立TEST。

GPU前仍需：完整生产接线/源码/受影响CPU、资产和存储准入；单次7GPUh执行授权；仅本卡原中央账本预约与实耗结算授权。四卡维护期间不自行访问或迁移账本。启动后才按实际开始时间安排唯一半程和终验，UNKNOWN仅恢复原句柄。

## 全部物理路径（两版独立列明，不临时增删）

### 39路径

| 槽位 | 类别 | 输入 | 角色 | 干净计时 |
|---|---|---|---|---|
| E1_39_001 | WARM | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | NATIVE35 | 否 |
| E1_39_002 | WARM | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | F19_A1 | 否 |
| E1_39_003 | WARM | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | SU19_BR_DIAG_C | 否 |
| E1_39_004 | WARM | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | SU19_CFG_C | 否 |
| E1_39_005 | WARM | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | BUDGET_SEARCH19_C | 否 |
| E1_39_006 | WARM | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | F19_RISKSWAP_C | 否 |
| E1_39_007 | ALLD_EQUIVALENCE | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | ALLD | 否 |
| E1_39_008 | REPLAY_CONTROL | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | NATIVE35 | 是 |
| E1_39_009 | REPLAY_CONTROL | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | F19_A1 | 是 |
| E1_39_010 | FORMAL | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | SU19_BR_DIAG_C | 是 |
| E1_39_011 | FORMAL | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | SU19_CFG_C | 是 |
| E1_39_012 | FORMAL | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | BUDGET_SEARCH19_C | 是 |
| E1_39_013 | FORMAL | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | F19_RISKSWAP_C | 是 |
| E1_39_014 | REPLAY_CONTROL | human_199 | F19_A1 | 是 |
| E1_39_015 | FORMAL | human_199 | SU19_BR_DIAG_C | 是 |
| E1_39_016 | FORMAL | human_199 | SU19_CFG_C | 是 |
| E1_39_017 | FORMAL | human_199 | BUDGET_SEARCH19_C | 是 |
| E1_39_018 | FORMAL | human_199 | F19_RISKSWAP_C | 是 |
| E1_39_019 | REPLAY_CONTROL | human_199 | NATIVE35 | 是 |
| E1_39_020 | FORMAL | misc_13398218_3840_2160_60fps | SU19_BR_DIAG_C | 是 |
| E1_39_021 | FORMAL | misc_13398218_3840_2160_60fps | SU19_CFG_C | 是 |
| E1_39_022 | FORMAL | misc_13398218_3840_2160_60fps | BUDGET_SEARCH19_C | 是 |
| E1_39_023 | FORMAL | misc_13398218_3840_2160_60fps | F19_RISKSWAP_C | 是 |
| E1_39_024 | REPLAY_CONTROL | misc_13398218_3840_2160_60fps | NATIVE35 | 是 |
| E1_39_025 | REPLAY_CONTROL | misc_13398218_3840_2160_60fps | F19_A1 | 是 |
| E1_39_026 | FORMAL | av_51b45829-502e-4143-9c32-c026bd6ab191 | SU19_CFG_C | 是 |
| E1_39_027 | FORMAL | av_51b45829-502e-4143-9c32-c026bd6ab191 | BUDGET_SEARCH19_C | 是 |
| E1_39_028 | FORMAL | av_51b45829-502e-4143-9c32-c026bd6ab191 | F19_RISKSWAP_C | 是 |
| E1_39_029 | REPLAY_CONTROL | av_51b45829-502e-4143-9c32-c026bd6ab191 | NATIVE35 | 是 |
| E1_39_030 | REPLAY_CONTROL | av_51b45829-502e-4143-9c32-c026bd6ab191 | F19_A1 | 是 |
| E1_39_031 | FORMAL | av_51b45829-502e-4143-9c32-c026bd6ab191 | SU19_BR_DIAG_C | 是 |
| E1_39_032 | REPEAT | misc_13398218_3840_2160_60fps | SU19_BR_DIAG_C | 是 |
| E1_39_033 | REPEAT | misc_13398218_3840_2160_60fps | SU19_CFG_C | 是 |
| E1_39_034 | REPEAT | misc_13398218_3840_2160_60fps | BUDGET_SEARCH19_C | 是 |
| E1_39_035 | REPEAT | misc_13398218_3840_2160_60fps | F19_RISKSWAP_C | 是 |
| E1_39_036 | REPEAT | av_51b45829-502e-4143-9c32-c026bd6ab191 | F19_RISKSWAP_C | 是 |
| E1_39_037 | REPEAT | av_51b45829-502e-4143-9c32-c026bd6ab191 | BUDGET_SEARCH19_C | 是 |
| E1_39_038 | REPEAT | av_51b45829-502e-4143-9c32-c026bd6ab191 | SU19_CFG_C | 是 |
| E1_39_039 | REPEAT | av_51b45829-502e-4143-9c32-c026bd6ab191 | SU19_BR_DIAG_C | 是 |

### 46路径

| 槽位 | 类别 | 输入 | 角色 | 干净计时 |
|---|---|---|---|---|
| E1_46_001 | WARM | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | NATIVE35 | 否 |
| E1_46_002 | WARM | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | F19_A1 | 否 |
| E1_46_003 | WARM | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | SU19_BR_DIAG_C | 否 |
| E1_46_004 | WARM | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | SU19_CFG_C | 否 |
| E1_46_005 | WARM | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | BUDGET_SEARCH19_C | 否 |
| E1_46_006 | WARM | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | F19_RISKSWAP_C | 否 |
| E1_46_007 | WARM | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | F19_C | 否 |
| E1_46_008 | ALLD_EQUIVALENCE | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | ALLD | 否 |
| E1_46_009 | REPLAY_CONTROL | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | NATIVE35 | 是 |
| E1_46_010 | REPLAY_CONTROL | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | F19_A1 | 是 |
| E1_46_011 | FORMAL | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | SU19_BR_DIAG_C | 是 |
| E1_46_012 | FORMAL | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | SU19_CFG_C | 是 |
| E1_46_013 | FORMAL | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | BUDGET_SEARCH19_C | 是 |
| E1_46_014 | FORMAL | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | F19_RISKSWAP_C | 是 |
| E1_46_015 | REPLAY_CONTROL | av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632 | F19_C | 是 |
| E1_46_016 | REPLAY_CONTROL | human_199 | F19_A1 | 是 |
| E1_46_017 | FORMAL | human_199 | SU19_BR_DIAG_C | 是 |
| E1_46_018 | FORMAL | human_199 | SU19_CFG_C | 是 |
| E1_46_019 | FORMAL | human_199 | BUDGET_SEARCH19_C | 是 |
| E1_46_020 | FORMAL | human_199 | F19_RISKSWAP_C | 是 |
| E1_46_021 | REPLAY_CONTROL | human_199 | F19_C | 是 |
| E1_46_022 | REPLAY_CONTROL | human_199 | NATIVE35 | 是 |
| E1_46_023 | FORMAL | misc_13398218_3840_2160_60fps | SU19_BR_DIAG_C | 是 |
| E1_46_024 | FORMAL | misc_13398218_3840_2160_60fps | SU19_CFG_C | 是 |
| E1_46_025 | FORMAL | misc_13398218_3840_2160_60fps | BUDGET_SEARCH19_C | 是 |
| E1_46_026 | FORMAL | misc_13398218_3840_2160_60fps | F19_RISKSWAP_C | 是 |
| E1_46_027 | REPLAY_CONTROL | misc_13398218_3840_2160_60fps | F19_C | 是 |
| E1_46_028 | REPLAY_CONTROL | misc_13398218_3840_2160_60fps | NATIVE35 | 是 |
| E1_46_029 | REPLAY_CONTROL | misc_13398218_3840_2160_60fps | F19_A1 | 是 |
| E1_46_030 | FORMAL | av_51b45829-502e-4143-9c32-c026bd6ab191 | SU19_CFG_C | 是 |
| E1_46_031 | FORMAL | av_51b45829-502e-4143-9c32-c026bd6ab191 | BUDGET_SEARCH19_C | 是 |
| E1_46_032 | FORMAL | av_51b45829-502e-4143-9c32-c026bd6ab191 | F19_RISKSWAP_C | 是 |
| E1_46_033 | REPLAY_CONTROL | av_51b45829-502e-4143-9c32-c026bd6ab191 | F19_C | 是 |
| E1_46_034 | REPLAY_CONTROL | av_51b45829-502e-4143-9c32-c026bd6ab191 | NATIVE35 | 是 |
| E1_46_035 | REPLAY_CONTROL | av_51b45829-502e-4143-9c32-c026bd6ab191 | F19_A1 | 是 |
| E1_46_036 | FORMAL | av_51b45829-502e-4143-9c32-c026bd6ab191 | SU19_BR_DIAG_C | 是 |
| E1_46_037 | REPEAT | misc_13398218_3840_2160_60fps | SU19_BR_DIAG_C | 是 |
| E1_46_038 | REPEAT | misc_13398218_3840_2160_60fps | SU19_CFG_C | 是 |
| E1_46_039 | REPEAT | misc_13398218_3840_2160_60fps | BUDGET_SEARCH19_C | 是 |
| E1_46_040 | REPEAT | misc_13398218_3840_2160_60fps | F19_RISKSWAP_C | 是 |
| E1_46_041 | REPEAT | misc_13398218_3840_2160_60fps | F19_C | 是 |
| E1_46_042 | REPEAT | av_51b45829-502e-4143-9c32-c026bd6ab191 | F19_C | 是 |
| E1_46_043 | REPEAT | av_51b45829-502e-4143-9c32-c026bd6ab191 | F19_RISKSWAP_C | 是 |
| E1_46_044 | REPEAT | av_51b45829-502e-4143-9c32-c026bd6ab191 | BUDGET_SEARCH19_C | 是 |
| E1_46_045 | REPEAT | av_51b45829-502e-4143-9c32-c026bd6ab191 | SU19_CFG_C | 是 |
| E1_46_046 | REPEAT | av_51b45829-502e-4143-9c32-c026bd6ab191 | SU19_BR_DIAG_C | 是 |
