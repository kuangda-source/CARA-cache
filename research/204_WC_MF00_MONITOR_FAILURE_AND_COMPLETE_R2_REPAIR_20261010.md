# MF-00监测故障与完整R2修复（2026-10-10）

本轮得到RA完整求解器CPU接线正结果，见[203](203_WC_RA_JOINT_EXECUTION_AND_CALIBRATION_ENTRY_20261010.md)。MF-00实际GPU R1则出现监督工程故障：只读`nvidia-smi`查询超过10秒抛出TimeoutExpired，监督器finally清理原runner，且漏写exit_code。后CPU按原监督字段读取触发KeyError。见[原故障日志](../reports/wc_mf00_interface_r1_monitor_exception_20261010.json)及[完整终态原件](../reports/wc_mf00_interface_r1_terminal_20261010_capture_and_independent_audit.json)。原三PID均消失、锁释放，四路径分母保持，完成0视频/0路径；无接口不等价或方法效果判断。

原任务完整wall752.441178秒，实费**0.209011438 GPUh**（包含620.284490秒模型加载），结算累计**30.104258028114113/77.89524658965853**，提交66、无在途，窗口尚余**47.790988562 GPUh**。本地权威账本已同步服务器原始字节，无重置、转移或漏计。原退出码缺失如实保留，不按猜测补写。

修正独立R2监督文件，原R1冻结stage及源码不修改：fresh准入仍严格要求目标GPU/锁/授权/预算；运行期间监测的TimeoutExpired、CalledProcessError和OSError记录为遥测不可用，保持原runner继续；真实进程失败或授权界限仍处理。任何退出路径都从原child.wait记录实际退出码；释放检查区分本卡runner和其他用户进程，后CPU仅在原GPU句柄实际消失后执行、CUDA关闭。三类遥测异常的[CPU分类检查](../reports/wc_mf00_interface_r2_telemetry_cpu_20261010.json)通过，尚非真实监督进程或GPU结果。

[完整R2登记](../manifests/wc_mf00_interface_r2_preregistration_20261010.json)保持Common/Human seed3×ORIGINAL/PAIRED全OFF一次，4全36路径/4全93视频/144 guided/4latent。科学采样源和既有batch CPU证明保持；新源资产/选定配置CPU须验收后再唯一GPU提交，不接受原失败子集，不自动重投旧身份。预测采用本次实际620.284490秒加载，整卡**1.880129229 GPUh**，当前单次≤4自主规则和窗口预算足够，不再请求重复批准。旧16路6.704055834卡仍未批准未执行。

下一完成R2监督源CPU和fresh资源准入、完整真实接口，再推进本地RA校准及A/B/C方法。此故障属于监督实现，方向与质量/速度假设尚未被检验；RA接线CPU正结果与原失败费用分别保留。
