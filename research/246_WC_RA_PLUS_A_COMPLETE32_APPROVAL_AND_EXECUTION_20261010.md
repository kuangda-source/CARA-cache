# 完整32路径 RA＋A：直接批准与执行接续

用户在2026-10-10对原完整卡问题直接回复“批准完整 32 路径卡”。授权记录为 `manifests/wc_ra_plus_a_r1_direct_authorization_20261010.json`；选定配置为 `configs/wc_ra_plus_a_selected_r1_20261010.json`。原冻结研究设计、283源载荷及原生产CPU证据不变。

本卡验证RA共同CFG控制在Cosmos/WorldCache上的表现，以及增量校准或β=1修正能否在共同控制下改善完整视频的保真—成本表现。每个已有CAL场景保留WC、JOINT_NATIVE、RA、W1_GLOBAL_1、BETA1_GLOBAL_1、W1_ONE_PHASE、BETA1_ONE_PHASE七方法，再加一个原生参考，共四场景32完整路径。请求35步、UniPC/Karras实际36更新／72CFG调用，合计1152更新／2304调用；93帧、768×432、16fps。

原完整预计5.147707517089633 GPUh高于单次4 GPUh自主门槛，此次直接授权满足该具体卡例外。计入现新增48 GPUh窗口，累计上限77.89524658965853；最近已结算34.37288029603066，不把旧快照当准入余额。预算保护继续计入加载、失败、写出及释放费用。预计耗时不是完成回执，也不是严格耗时保证。

当前授权和选定已完成，GPU提交0。下一步按原选定生产CPU入口执行；确认原PID退出、payload/runtime/request/authority/config一致后，运行既定唯一GPU launcher的fresh资源与账本准入。只跟踪该实际句柄，运行中不改源或重复提交。绑定的后续CPU审计在GPU释放后检查真实原件，随后全部可配对视频按93帧FP32 Alex LPIPS评分；拒绝或缺失保留在原分母，不替换。

阶段来源floor的完整128路径CPU原句柄独立继续；它不改变本283运行源，也不作为本卡额外门槛。同状态C/A/P/D成本设计五文件当前为未登记、未执行WIP，不据它们宣称已通过CPU或已授权新GPU。
