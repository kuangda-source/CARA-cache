# 794 — 单次14GPUh批准、中央入口恢复与启动前修复

用户明确批准“批准单次14GPUh，核验通过后启动”，随后批准四卡仅原账本/原句柄读取，以及“允许本卡的原账本预约与结算”。这些许可绑定同一完整112路径/51双FIT查询卡，launch_id 2b8058a77c7248f181acffddd399c257，实际GPU仍只允许两卡单A6000。无需再次询问相同批准；没有四卡GPU执行或账本迁移许可。

本次原四卡控制入口读取成功。唯一账本cap226，used183.78422815946897、reserved16.5、available25.715771840531033；旧两笔4.5+12责任保持，本卡无预约，也无其他非责任hold的活动登记作业。四卡原本卡stage/容器/意图均不存在。这个新观测证明控制入口可用，不代表四卡硬件实验恢复，也不代替真正启动前的fresh核验。

两卡源阶段按已接受cc5源准备完成，1181文件及runtime完整；原stage事先不存在，准备后仍无GPU意图或容器。原登记SHA a2e3b9345f6440934e7f18bfbfe19fff2f73a1e378b633678b8d7d8703c9d841。实际授权、CPU证明、工程报价与存储合同已绑定，但没有中央预约或GPU派发。

CPU资产准入原进程PID2341051/start ticks672318697在读取execution-CPU-proof.json时发生MemoryError；2GiB RLIMIT_AS限制了Python/NumPy已有虚拟地址空间，不能等同物理RSS上限。原进程已退出、workerSHA不变，失败状态/日志和阶段保留；资产哈希与GPU资源准入尚未完成。下一次准备须修正线程初始化与适当内存约束，使用新原句柄，不能把此失败说成GPU失败或重派实验。

启动前审阅另发现原capture_lifecycle只resolve项目根、不resolve登记stage，真实两卡项目根是符号链接，因而即使完整终态也会在路径一致性门被拒。新增真实项目别名夹具先复现失败，再改为保留与launch一致的登记项目路径；仍拒绝stage自身为符号链接。9项捕获加16项财务控制本地全部通过。实际Linux增量还待；原完整CPU证明仍只对应cc5，不可套用于修改后的源码。原数值/科学范围不变，无须重做完整数值矩阵。

继续先完成受影响Linux接受和修复后的独立源/准入准备，保留旧prelaunch阶段及失败；原R1当前不得派发。完整14GPUh授权保持，真正启动前重新核验并唯一预约，按实际起点安排6.5小时半程、13.25小时终验和14小时硬截止。GPU尚未启动，未建立无实际起点的自动检查。A32冻结及B36/S/Q源和结果不变。

[本轮回执](../reports/cara_budget_single14_approved_prelaunch_repair_r1_20261031.json) · [准入原失败](../reports/cara_budget_approved_two_admission_capture_r1_20261031.json) · [唯一授权](../plans/cara_next_stage_20261028/mainline/r2/BUDGET_SINGLE14GPUH_USER_AUTHORIZATION_20261031.json) · [原中央事务许可](../plans/cara_next_stage_20261028/mainline/r2/BUDGET_SINGLE14_CENTRAL_TRANSACTION_AUTHORIZATION_20261031.json)
