# E4c 生产CPU验收与整卡执行（2026-10-11）

原6a5910c／4074965与4074966退出0消失，47.512339秒；399部署原件、225旧输入helper原件、全部实际CAL/RA/Native/模型/solver绑定、7合同变异拒绝、1无guardrail入口拒绝、4GPU启动资产缺失/变更拒绝及8准入拒绝独立核对通过。未改native meta/helper的2B参数与1173模块eval验收同源复用，没有重跑模型构建或原完整sampling CPU。此前Toy采样全8父/32suffix/48点、独立88文件/776tensor/324比较保持。

当前具体整卡：`WC-E4C-MATCHED-P-D-AGE124-OFFON4-SUFFIX16-R1-20261011-A`，4完整父路径＋16个5步短分支＋24同状态dense teacher，248pair／496CFG，一个新模型生命周期。完整forecast2.577578296GPUh，受用户≤8整卡自主授权，计新48窗口；不新增采样、训练、人评，不替代或拆E2/E3完整待批卡。

`dispatch_wc_e4c_source_age_r1.py`先验证原CPU回执与句柄消失、原source/source-binding，再看fresh GPU UUID/VRAM/compute/8h规则/全预算/锁；选择独立目录只复制已验收399字节。supervisor重新在共享锁内执行正式准入，单模型全范围运行；任何错误保留分母并停止，旧秒级deadline不恢复、不中断他人进程、不放松原物理保护。以原supervisor/PID/日志/账本为是否真正启动的证据，dispatch本身不是GPU结果。

完成后读实际44文件／388张量、4父视频及24点guided误差；保持缺失/部分/失败分母。该卡检验P-after-C真实误差与代理筛选是否对齐，不将local MSE直接当视频质量。原R1/R2 CPU失败保留。
