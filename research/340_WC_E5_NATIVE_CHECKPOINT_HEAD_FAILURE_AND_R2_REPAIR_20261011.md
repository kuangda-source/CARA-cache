# E5完整采样CPU首轮失败与生产checkpoint head修复（2026-10-11）

**已定位一个必要的生产接线差异：2B的FinalLayer实际在原生选择性checkpoint wrapper内。** R1把外层wrapper当成FinalLayer校验，因此在2B Meta检查处停止，完整采样0条。原6406680／4089583与4089585退出1并消失、24.854265秒，411源码和预算hash保持；原receipt／log／registration压缩原件独立保存，不报CPU通过。

实际导入FinalLayer与AST取得的native FinalLayer函数字节码相同、flags均67；所以没有放松native指纹。完整2B Meta构造显示实际head根类为Torch CheckpointWrapper，叶子为同一原生FinalLayer，NO_REENTRANT／use_reentrant=False／preserve_rng_state=False，context_fn为固定predict2_2B_720_context_fn_aggressive。SAC配置为predict2_2b_720_aggressive／every_n_blocks=1。诊断未初始化CUDA、未加载2B真实权重或跑前向。

## R2明确改动与保护

独立`early_head_elision_sampling_r2.py`保留wrapper原有调用，候选和原head仍经同一个原生checkpoint包装调用。只将head guard区分为call_head根／native leaf，固定Torch wrapper与checkpoint来源hash、原生context函数字节码、NO_REENTRANT参数、根／叶identity与拓扑、eval／无buffer／无forward hooks、无compiled call／native leaf模式和子层配置。数值调用只允许inference no_grad，不绕过wrapper、去掉SAC或修改旧原型／R1源。

wrapper source SHA df706f293970d4177f2ba2133c9e5ffb4e98e424df56c7a42a450a0007629b08；Torch checkpoint source SHA b07acb21f5c727f3eace16249ca126a7c8a0ac8d97c83f2a13fff1b5a59a360f。实际native source及AdaLN／Wan／unpatchify合同保持。

原24完整路径／444实读比较／888张量／96完整自身恢复不缩。两版本CPU小权重head都用实际原生wrapper和固定context_fn，Python实际native leaf forward事件计数，不把wrapper选择或配置数当实际调用。增加七个生产wrapper动态拒绝：reentrant、preserve_rng、context_fn、根forward覆盖、根hook、根buffer、根training；拒绝后恢复原完整合同。原Meta子层eps变更拒绝继续。

R1未开始实际采样，失败原因已准确定位后R2才能跑原受影响完整范围；旧原型12路径CPU证据、老sampler、E2/E3冻结方法和在途E4c均保持。Toy attention／conditions／prepare／unpatchify／decode／writer边界保持，不能称真实2B视频或速度证据。

## 执行

独立`.sync/wc-e5-complete-sampling-cpu-r2-20261011`，411继承原件＋5新载荷＝416文件，提交后服务器CPU执行。结果尚待，不修改R1 receipt或原输出。CPU禁止CUDA／下载／账本写入；失败和未开始分母保留。

原E4c 4075406／4075494／4079033继续，完整4父／4事件／16suffix／24teacher不改不重投，终态自动CPU全读仍优先。完整单卡预计≤8GPUh自主／严格>8准确批准，E2／E3原above8问题保持不重问，累计新增48窗口和预算账本保持。无新GPU、训练、人评；目标active。

独立原失败见`reports/wc_e5_complete_sampling_cpu_r1_terminal_20261011_capture.json`，两个来源诊断见`reports/wc_e5_native_production_checkpoint_wrapper_diagnostic_20261011.json`及`reports/wc_e5_native_leaf_head_code_diagnostic_20261011.json`。
