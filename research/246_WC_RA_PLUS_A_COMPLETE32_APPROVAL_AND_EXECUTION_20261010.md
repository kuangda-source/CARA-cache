# 完整32路径 RA＋A：直接批准与执行接续

用户在2026-10-10对原完整卡问题直接回复“批准完整 32 路径卡”。授权记录为 `manifests/wc_ra_plus_a_r1_direct_authorization_20261010.json`；选定配置为 `configs/wc_ra_plus_a_selected_r1_20261010.json`。原冻结研究设计、283源载荷及原生产CPU证据不变。

本卡验证RA共同CFG控制在Cosmos/WorldCache上的表现，以及增量校准或β=1修正能否在共同控制下改善完整视频的保真—成本表现。每个已有CAL场景保留WC、JOINT_NATIVE、RA、W1_GLOBAL_1、BETA1_GLOBAL_1、W1_ONE_PHASE、BETA1_ONE_PHASE七方法，再加一个原生参考，共四场景32完整路径。请求35步、UniPC/Karras实际36更新／72CFG调用，合计1152更新／2304调用；93帧、768×432、16fps。

原完整预计5.147707517089633 GPUh高于单次4 GPUh自主门槛，此次直接授权满足该具体卡例外。计入现新增48 GPUh窗口，累计上限77.89524658965853；最近已结算34.37288029603066，不把旧快照当准入余额。预算保护继续计入加载、失败、写出及释放费用。预计耗时不是完成回执，也不是严格耗时保证。

当前授权和选定已完成，GPU提交0。下一步按原选定生产CPU入口执行；确认原PID退出、payload/runtime/request/authority/config一致后，运行既定唯一GPU launcher的fresh资源与账本准入。只跟踪该实际句柄，运行中不改源或重复提交。绑定的后续CPU审计在GPU释放后检查真实原件，随后全部可配对视频按93帧FP32 Alex LPIPS评分；拒绝或缺失保留在原分母，不替换。

阶段来源floor的完整128路径CPU原句柄独立继续；它不改变本283运行源，也不作为本卡额外门槛。同状态C/A/P/D成本设计五文件当前为未登记、未执行WIP，不据它们宣称已通过CPU或已授权新GPU。

## 已执行：selected CPU 与唯一GPU提交

source `beb02c95e7edf570e137bcc4131d5ee3d73fa71b` 已推送。独立选定目录的生产CPU实计 54.039325 秒，exit0，原PIDs3929003／3929004退出；配置绑定、四请求完整scope、283载荷及runtime一致，27变异拒绝通过。见 `reports/wc_ra_plus_a_selected_cpu_r1_terminal_20261010_capture.json` 与原件压缩副本。

原完整卡fresh准入后唯一提交：supervisor 3929440、实际runner3929519、绑定post CPU 3929441。`reports/wc_ra_plus_a_r1_GPU_launch_20261010.json` 与 `reports/wc_ra_plus_a_r1_start_observation_20261010.json` 记录首个现场；锁实际被持有，初始化日志存在，GPU科学终态尚未产生。后CPU等原supervisor与runner退出及GPU释放后审计全部张量与接受视频。

账本提交前已结算34.37288029603066；第73项进入在途，预算系统保守预留剩余43.52236629362787。账面临时used达到上限是预留，**不是已耗尽或本卡实耗43.52h**；终态按真实wall结算。

全帧CPU评分已事前登记 `manifests/wc_ra_plus_a_score_cpu_r1_preregistration_20261010.json`，十源载荷、28最大配对×93帧=2604最大距离、28场景方法摘要、十预定对照及32成本槽。配置中的已有开发曝光保持；不把逐帧当独立样本，不把LPIPS当物理或语义质量，不把带记录的wall当clean速度，但如实比较它的质量与成本信号。接续只等待原GPU／raw CPU实际退出，失败不评分子集为成功。

完整评分接续已部署：source651ebfbcbaaf8f9ee6c7b31e5ad37e44bc41bd05／CPU supervisor3930095，CUDA排除，GPU提交0、账本不写；等待原GPU3929440与raw CPU3929441退出，成功后仅一次评估原卡全部可配对93帧。见 `reports/wc_ra_plus_a_score_cpu_r1_launch_20261010.json`。阶段128 CPU独立验收结果见247；不改已在跑的283载荷或post CPU。

最新现场确认原GPU句柄正常进入首场景WC采样：观察1791608605.3902872时已经执行12/36更新，目标GPU10094MiB／98%且唯一compute PID为3929519，原配置哈希保持；零完成视频／张量是此早期现场状态，不能当最终产出数量。见 `reports/wc_ra_plus_a_r1_progress_observation_20261010.json`。飞书组会报告52→53只替换一个进度段，197块其他内容均保持，记录 `reports/wc_ra_plus_a_gpu_launch_feishu_20261010_verification.json`。
